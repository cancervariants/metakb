"""A module for to transform CIViC."""
from typing import Optional, Dict, List, Set
from pathlib import Path
import logging
import re

from ga4gh.core import core_models
from ga4gh.vrs import models

from metakb import APP_ROOT
from metakb.normalizers import VICCNormalizers
from metakb.transform.base import Transform
from metakb.schemas.app import MethodId, SourcePrefix
from metakb.schemas.annotation import Direction, Document
from metakb.schemas.variation_statement import (
    AlleleOrigin,
    VariantTherapeuticResponseStudy,
    VariantTherapeuticResponseStudyPredicate,
    VariantOncogenicityStudyQualifier
)
from metakb.schemas.categorical_variation import ProteinSequenceConsequence

logger = logging.getLogger(__name__)


class CIViCTransform(Transform):
    """A class for transforming CIViC to the common data model."""

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[VICCNormalizers] = None) -> None:
        """Initialize CIViC Transform class.
        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param VICCNormalizers normalizers: normalizer collection instance
        """
        super().__init__(data_dir=data_dir,
                         harvester_path=harvester_path,
                         normalizers=normalizers)
        # Create cache of able to normalize and unable to normalize
        # variation/disease/therapeutic agents
        self.able_to_normalize = {
            'variations': {},
            'molecular_profiles': {},
            'diseases': {},
            'therapeutics': {},
            'genes': {}
        }
        # Unable to normalize these IDs
        self.unable_to_normalize = {
            'therapeutics': [],
            'diseases': []
        }

    @staticmethod
    def _mp_to_variant_mapping(molecular_profiles: List[Dict]) -> Dict:
        """Get mapping from Molecular Profile ID to Variant ID. We currently do not
        handle complex molecular profiles (> 1 variant associated).

        :param molecular_profiles: List of civic molecular profiles represented as
            dictionaries
        :return: Molecular Profile ID to Variant ID mapping {mp_id: v_id}
        """
        mapping: Dict = {}
        not_supported_mps = set()
        for mp in molecular_profiles:
            mp_id = mp["id"]
            mp_variant_ids = mp["variant_ids"]
            if len(mp_variant_ids) != 1:
                mapping[mp_id] = None
                not_supported_mps.add(mp_id)
            else:
                mapping[mp_id] = mp_variant_ids[0]

        logger.debug(f"{len(not_supported_mps)} Molecular Profiles not supported: "
                     f"{not_supported_mps}")
        return mapping

    async def transform(self):
        """Transform CIViC harvested json to common data model.

        TODO:
        Add support for assertions
        Add support for Prognostic + Diagnostic evidence types
        """
        data = self.extract_harvester()
        evidence_items = data['evidence']
        molecular_profiles = data["molecular_profiles"]
        variants = data['variants']
        genes = data['genes']
        mp_id_to_v_id_mapping = self._mp_to_variant_mapping(molecular_profiles)

        # Only want evidence with approved status
        evidence_items = [e for e in evidence_items if e["status"] == "accepted"]

        # Filter Variant IDs for Predictive
        evidence_items = [e for e in evidence_items
                          if e["evidence_type"].upper() == "PREDICTIVE"]

        vids = {mp_id_to_v_id_mapping[e["molecular_profile_id"]]
                for e in evidence_items if e["molecular_profile_id"]}

        await self._add_variations(variants, vids)
        self._add_genes(genes)

        # Only want to do MPs where variation-normalizer succeeded
        able_to_normalize_vids = self.able_to_normalize["variations"].keys()
        mps = [
            mp
            for mp in molecular_profiles
            if f"civic.vid:{mp['variant_ids'][0]}" in able_to_normalize_vids
        ]
        self._add_molecular_profiles(mps, mp_id_to_v_id_mapping)
        self._transform_evidence(evidence_items, mp_id_to_v_id_mapping)

    def _transform_evidence(
        self, records: List[Dict], mp_id_to_v_id_mapping: Dict
    ) -> None:
        """Transform statements, propositions, descriptors, and documents
        from CIViC evidence items and assertions.

        :param records: CIViC Evidence Items or Assertions
        :param mp_id_to_v_id_mapping: Molecular Profile ID to Variant ID mapping
            {mp_id: v_id}
        :param is_evidence: `True` if records are evidence items.
            `False` if records are assertions.
        """
        for r in records:
            # Get predicate
            predicate = self._get_predicate(r["evidence_type"], r["significance"])

            # Don't support TR that has  `None`, "N/A", or "Unknown" predicate
            if not predicate:
                continue

            # Get Disease
            if not r['disease']:
                continue

            disease_id = f"civic.did:{r['disease']['id']}"
            civic_disease = self._add_disease(disease_id, r)
            if not civic_disease:
                continue

            if civic_disease not in self.diseases:
                self.diseases.append(civic_disease)

            # Get therapy
            if len(r["therapies"]) != 1:
                continue
            else:
                therapy_id = f"civic.tid:{r['therapies'][0]['id']}"
                civic_therapeutic = self._add_therapeutic(therapy_id, r)
                if not civic_therapeutic:
                    continue

                if civic_therapeutic not in self.therapeutics:
                    self.therapeutics.append(civic_therapeutic)

            # Get method and add to instance variable
            method = self.methods_mapping[MethodId.CIVIC_EID_SOP.value]
            if method not in self.methods:
                self.methods.append(method)

            # isReportedIn
            document = self._get_eid_document(r['source'])
            if document not in self.documents:
                self.documents.append(document)

            direction = self._get_evidence_direction(r["evidence_direction"])
            evidence_level = f"civic.evidence_level:{r['evidence_level']}"
            strength = self.evidence_level_vicc_concept_mapping[evidence_level]

            # Get variation and gene
            mp = self.able_to_normalize["molecular_profiles"][f"civic.mpid:{r['molecular_profile_id']}"]
            variant_id = f"civic.vid:{mp_id_to_v_id_mapping[r['molecular_profile_id']]}"
            variation_gene_map = self.able_to_normalize['variations'].get(variant_id)
            if not variation_gene_map:
                continue

            gene_id = variation_gene_map["civic_gene_id"]
            qualifiers = self._get_qualifiers(r["variant_origin"], gene_id)

            statement = VariantTherapeuticResponseStudy(
                id=r['name'].lower().replace('eid', 'civic.eid:'),
                description=r["description"] if r["description"] else None,
                direction=direction,
                strength=strength,
                predicate=predicate,
                variant=mp,
                therapeutic=civic_therapeutic,
                tumorType=civic_disease,
                qualifiers=qualifiers,
                specified_by=method,
                isReportedIn=[document]
            ).model_dump(exclude_none=True)
            self.statements.append(statement)

    def _get_qualifiers(self, variant_origin, civic_gene_id) -> Optional[VariantOncogenicityStudyQualifier]:
        variant_origin = variant_origin.upper()
        if variant_origin == "SOMATIC":
            allele_origin = AlleleOrigin.SOMATIC
        elif variant_origin in ["RARE_GERMLINE", "COMMON_GERMLINE"]:
            allele_origin = AlleleOrigin.GERMLINE
        else:
            allele_origin = None

        gene_context = self.able_to_normalize["genes"].get(civic_gene_id)

        if allele_origin or gene_context:
            qualifiers = VariantOncogenicityStudyQualifier(
                alleleOrigin=allele_origin,
                geneContext=gene_context
            )
        else:
            qualifiers = None

        return qualifiers

    def _get_evidence_direction(self, direction) -> Optional[Direction]:
        """Return the evidence direction.

        :param str direction: The civic evidence_direction value
        :return: Direction
        """
        direction_upper = direction.upper()
        if direction_upper == "SUPPORTS":
            return Direction.SUPPORTS
        elif direction_upper == "DOES_NOT_SUPPORT":
            return Direction.DOES_NOT_SUPPORT
        else:
            return None

    def _get_assertion_evidence_level(self, assertion) -> Optional[str]:
        """Return evidence_level for CIViC assertion.

        :param dict assertion: CIViC Assertion
        :return: CIViC assertion evidence_level
        """
        evidence_level = None
        # TODO: CHECK
        if assertion['amp_level']:
            if assertion['amp_level'] == 'Not Applicable':
                evidence_level = None
            else:
                amp_level = assertion["amp_level"]
                regex = re.compile(r"TIER_(?P<tier>\w+)_LEVEL_(?P<level>\w+)")
                match = regex.match(amp_level)
                if match:
                    match = match.groupdict()
                    tier = match["tier"]
                    level = match["level"]

                    if tier == 'I':
                        tier = 1
                    elif tier == 'II':
                        tier = 2
                    elif tier == 'III':
                        tier = 3
                    elif tier == 'IV':
                        tier = 4

                    evidence_level = f"amp_asco_cap_2017_level:" \
                                     f"{tier}{level}"
                else:
                    raise Exception(f"{amp_level} not supported with regex")
        return evidence_level

    def _get_predicate(self, record_type,
                       clin_sig) -> Optional[VariantTherapeuticResponseStudyPredicate]:
        """Return predicate for an evidence item.

        :param str record_type: The evidence or assertion type
        :param str clin_sig: The evidence item's clinical significance
        :return: Predicate for proposition if valid
        """
        predicate = None

        if record_type == "PREDICTIVE":
            if clin_sig == 'SENSITIVITYRESPONSE':
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_SENSITIVITY_TO
            elif clin_sig == 'RESISTANCE':
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_RESISTANCE_TO
        return predicate

    def _add_molecular_profiles(self, molecular_profiles, mp_id_to_v_id_mapping):
        for mp in molecular_profiles:
            mp_score = mp["molecular_profile_score"]
            if mp_score:
                extensions = [
                    core_models.Extension(
                        name="CIViC Molecular Profile Score",
                        value=mp_score
                    )
                ]
            else:
                extensions = None

            mp_id = f"civic.mpid:{mp['id']}"
            vid = f"civic.vid:{mp_id_to_v_id_mapping[mp['id']]}"
            defining_context = self.able_to_normalize["variations"][vid]["vrs_variation"]
            psc = ProteinSequenceConsequence(
                id=mp_id,
                description=mp["description"],
                label=mp["name"],
                definingContext=defining_context,
                aliases=mp["aliases"] if mp["aliases"] else None,
                extensions=extensions
            ).model_dump(exclude_none=True)
            self.molecular_profiles.append(psc)
            self.able_to_normalize["molecular_profiles"][mp_id] = psc

    async def _add_variations(self, variants: List, vids: Set) -> None:
        """Add variations to instance variables `able_to_normalize['variations']` and
        `variations`, if the variation-normalizer can successfully normalize

        :param List variants: CIViC variants
        :param set vids: Candidate CIViC Variant IDs
        """
        for variant in variants:
            if variant["id"] not in vids:
                continue
            variant_id = f"civic.vid:{variant['id']}"
            if "c." in variant["name"]:
                variant_name = variant["name"]
                if "(" in variant_name:
                    variant_name = \
                        variant_name.replace("(", "").replace(")", "")
                variant_name = variant_name.split()[-1]
            else:
                variant_name = variant["name"]

            variant_query = f"{variant['entrez_name']} {variant_name}"

            # TODO: Remove as more get implemented in variation normalizer
            #  Filtering to speed up transformation
            vname_lower = variant["name"].lower()

            if vname_lower.endswith("fs") or "-" in vname_lower or "/" in vname_lower:
                logger.warning("Variation Normalizer does not support "
                                f"{variant_id}: {variant_query}")
                continue

            unable_to_normalize = {
                "mutation", "exon", "overexpression",
                "frameshift", "promoter", "deletion", "type", "insertion",
                "expression", "duplication", "copy", "underexpression",
                "number", "variation", "repeat", "rearrangement", "activation",
                "expression", "mislocalization", "translocation", "wild",
                "polymorphism", "frame", "shift", "loss", "function", "levels",
                "inactivation", "snp", "fusion", "dup", "truncation",
                "homozygosity", "gain", "phosphorylation"
            }

            if set(vname_lower.split()) & unable_to_normalize:
                logger.warning("Variation Normalizer does not support "
                               f"{variant_id}: {variant_query}")
                continue

            vrs_variation = await self.vicc_normalizers.normalize_variation(
                [variant_query]
            )

            # Couldn't find normalized concept
            if not vrs_variation:
                logger.warning("Variation Normalizer unable to normalize "
                               f"{variant_id} using query {variant_query}")
                continue

            params = vrs_variation.model_dump(exclude_none=True)
            params["id"] = variant_id
            params["label"] = variant["name"]
            civic_variation = models.Variation(**params)

            # Get extensions
            extensions = []
            hgvs_exprs = self._get_hgvs_exprs(variant)
            if hgvs_exprs:
                extensions.append(
                    core_models.Extension(
                        name="expressions",
                        value=hgvs_exprs
                    )
                )

            if variant["variant_types"]:
                extensions.append(
                    core_models.Extension(
                        name="structural_type",
                        value=variant["variant_types"][0]["so_id"]
                    )
                )

            # TODO: alises, xrefs, representative coordinate
            # xrefs = self._get_variant_xrefs(variant)
            # aliases = [
            #     v_alias for v_alias
            #     in variant["variant_aliases"]
            #     if not v_alias.startswith("RS")
            # ]

            if extensions:
                civic_variation.root.extensions = extensions

            civic_variation_dict = civic_variation.model_dump(exclude_none=True)

            self.able_to_normalize["variations"][variant_id] = {
                "vrs_variation": civic_variation_dict,
                "civic_gene_id": f"civic.gid:{variant['gene_id']}"
            }
            self.variations.append(civic_variation_dict)


    def _get_variant_extensions(self, variant) -> list:
        """Return a list of extensions for a variant.

        :param dict variant: A CIViC variant record
        :return: A list of extensions
        """
        return [
            core_models.Extension(
                name='civic_representative_coordinate',
                value={k: v for k, v in variant['coordinates'].items()
                       if v is not None}
            ).dict(exclude_none=True)
        ]

    # def _get_variant_xrefs(self, v) -> Optional[List[str]]:
    #     """Return a list of xrefs for a variant.

    #     :param dict v: A CIViC variant record
    #     :return: A dictionary of xrefs
    #     """
    #     xrefs = []
    #     for xref in ['clinvar_entries', 'allele_registry_id',
    #                  'variant_aliases']:
    #         if xref == 'clinvar_entries':
    #             for clinvar_entry in v['clinvar_entries']:
    #                 if clinvar_entry and clinvar_entry not in ['N/A',
    #                                                            "NONE FOUND"]:
    #                     xrefs.append(f"{schemas.XrefSystem.CLINVAR.value}:"
    #                                  f"{clinvar_entry}")
    #         elif xref == 'allele_registry_id' and v['allele_registry_id']:
    #             xrefs.append(f"{schemas.XrefSystem.CLINGEN.value}:"
    #                          f"{v['allele_registry_id']}")
    #         elif xref == 'variant_aliases':
    #             dbsnp_xrefs = [item for item in v['variant_aliases']
    #                            if item.startswith('RS')]
    #             for dbsnp_xref in dbsnp_xrefs:
    #                 xrefs.append(f"{schemas.XrefSystem.DB_SNP.value}:"
    #                              f"{dbsnp_xref.split('RS')[-1]}")
    #     return xrefs

    def _get_hgvs_exprs(self, variant) -> Optional[List[Dict[str, str]]]:
        """Return a list of hgvs expressions for a given variant.

        :param dict variant: A CIViC variant record
        :return: A list of hgvs expressions
        """
        hgvs_expressions = list()
        for hgvs_expr in variant['hgvs_expressions']:
            if ':g.' in hgvs_expr:
                syntax = 'hgvs.g'
            elif ':c.' in hgvs_expr:
                syntax = 'hgvs.c'
            else:
                syntax = 'hgvs.p'
            if hgvs_expr != 'N/A':
                hgvs_expressions.append(
                    {
                        "syntax": syntax,
                        "value": hgvs_expr
                    }
                )
        return hgvs_expressions

    def _add_genes(self, genes) -> None:
        """Add genes to instance variables `able_to_normalize['genes']` and `genes`, if
        the gene-normalizer can successfully normalize

        :param list genes: CIViC genes
        """
        for gene in genes:
            gene_id = f"civic.gid:{gene['id']}"
            ncbigene = f"ncbigene:{gene['entrez_id']}"
            queries = [ncbigene, gene['name']] + gene['aliases']

            _, normalized_gene_id = \
                self.vicc_normalizers.normalize_gene(queries)

            if normalized_gene_id:
                civic_gene = core_models.Gene(
                    id=gene_id,
                    label=gene["name"],
                    description=gene['description'] if gene['description'] else None,
                    mappings=[
                        core_models.Mapping(
                            coding=core_models.Coding(
                                code=str(gene["entrez_id"]),
                                system="https://www.ncbi.nlm.nih.gov/gene/"
                            ),
                            relation=core_models.Relation.EXACT_MATCH
                        )
                    ],
                    aliases=gene["aliases"] if gene["aliases"] else None
                ).model_dump(exclude_none=True)
                self.able_to_normalize["genes"][gene_id] = civic_gene
                self.genes.append(civic_gene)
            else:
                logger.warning(f"Gene Normalizer unable to normalize {gene_id}"
                               f"using queries: {queries}")

    def _add_disease(self, disease_id, record) -> Optional[core_models.Disease]:
        """Add disease ID to list of valid or invalid transformations.

        :param str disease_id: The CIViC ID for the disease
        :param dict record: CIViC AID or EID
        :return: A disease object
        """
        vrs_disease = self.able_to_normalize['diseases'].get(disease_id)
        if vrs_disease:
            return vrs_disease
        else:
            vrs_disease = None
            if disease_id not in self.unable_to_normalize['diseases']:
                vrs_disease = self._get_diseases(record['disease'])
                if vrs_disease:
                    self.able_to_normalize['diseases'][disease_id] = vrs_disease
                else:
                    self.unable_to_normalize['diseases'].append(disease_id)
            return vrs_disease

    def _get_diseases(self, disease) -> Optional[core_models.Disease]:
        """Get a VRS disease object.

        :param dict disease: A CIViC disease record
        :return: A Disease
        """
        if not disease:
            return None
        disease_id = f"civic.did:{disease['id']}"
        display_name = disease['display_name']
        doid = disease['doid']
        mappings = []

        if not doid:
            logger.debug(f"{disease_id} ({display_name}) has null DOID")
            queries = [display_name]
        else:
            doid = f"DOID:{doid}"
            queries = [doid, display_name]
            mappings.append(core_models.Mapping(
                coding=core_models.Coding(
                    code=doid,
                    system="https://www.disease-ontology.org/",
                ),
                relation=core_models.Relation.EXACT_MATCH
            ))

        _, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.warning(f"Disease Normalizer unable to normalize: "
                           f"{disease_id} using queries {queries}")
            return None

        return core_models.Disease(
            id=disease_id,
            label=display_name,
            mappings=mappings if mappings else None,
            extensions=[
                core_models.Extension(
                    name="disease_normalizer_id",
                    value=normalized_disease_id
                )
            ]
        ).model_dump(exclude_none=True)

    def _add_therapeutic(self, therapy_id, record)\
            -> Optional[core_models.TherapeuticAgent]:
        """Add therapy ID to list of valid or invalid transformations.

        :param str therapy_id: The CIViC ID for the drug
        :param dict record: CIViC AID or EID
        :return: A therapeutic agent object
        """
        vrs_therapeutic = self.able_to_normalize['therapeutics'].get(therapy_id)
        if vrs_therapeutic:
            return vrs_therapeutic
        else:
            vrs_therapeutic = None
            if therapy_id not in self.unable_to_normalize['therapeutics']:
                vrs_therapeutic = self._get_therapeutic(record["therapies"][0])
                if vrs_therapeutic:
                    self.able_to_normalize['therapeutics'][therapy_id] = vrs_therapeutic
                else:
                    self.unable_to_normalize['therapeutics'].append(therapy_id)
            return vrs_therapeutic

    def _get_therapeutic(self, drug) -> Optional[core_models.TherapeuticAgent]:
        """Get a VRS therapeutic agent.

        :param dict drug: A CIViC drug record
        :return: A Therapeutic Agent
        """
        therapy_id = f"civic.tid:{drug['id']}"
        label = drug["name"]
        ncit_id = drug["ncit_id"]
        mappings = []
        if ncit_id:
            ncit_id = f"ncit:{ncit_id}"
            queries = [ncit_id, label]
            mappings.append(core_models.Mapping(
                coding=core_models.Coding(
                    code=ncit_id,
                    system="https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                ),
                relation=core_models.Relation.EXACT_MATCH
            ))
        else:
            queries = [label]

        therapy_norm_resp, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy(queries)

        if not normalized_therapy_id:
            logger.warning(f"Therapy Normalizer unable to normalize: "
                           f"using queries {ncit_id} and {label}")
            return None

        regulatory_approval_extension = \
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)

        extensions = [
            core_models.Extension(
                name="therapy_normalizer_id",
                value=normalized_therapy_id
            )
        ]

        if regulatory_approval_extension:
            extensions.append(regulatory_approval_extension)

        return core_models.TherapeuticAgent(
            id=therapy_id,
            label=label,
            mappings=mappings if mappings else None,
            aliases=drug["aliases"] if drug["aliases"] else None
        ).model_dump(exclude_none=True)

    def _get_eid_document(self, source) -> Optional[Document]:
        """Get an EID's document.

        :param dict source: An evidence item's source
        :return: Document for EID
        """
        source_type = source['source_type'].upper()
        if source_type in SourcePrefix.__members__:
            document = Document(
                id=f"civic.source:{source['id']}",
                label=source["citation"],
                title=source["name"],
            ).model_dump(exclude_none=True)

            if source["source_type"] == SourcePrefix.PUBMED:
                document["pmid"] = int(source["citation_id"])
        else:
            logger.warning(f"{source_type} not in schemas.SourcePrefix")
            document = None

        return document
