"""A module for to transform CIViC."""
from typing import Optional, Dict, List, Set, Tuple
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


SNP_RE = re.compile(r"RS\d+")


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
    def _mp_to_variant_mapping(molecular_profiles: List[Dict]) -> Tuple[List, Dict]:
        """Get mapping from Molecular Profile ID to Variant ID. We currently do not
        handle complex molecular profiles (> 1 variant associated).

        :param molecular_profiles: List of civic molecular profiles represented as
            dictionaries
        :return: Molecular Profile ID to Variant ID mapping {mp_id: v_id}
        """
        mapping: Dict = {}
        supported_mps = []
        not_supported_mps = set()
        for mp in molecular_profiles:
            mp_id = mp["id"]
            mp_variant_ids = mp["variant_ids"]
            if len(mp_variant_ids) != 1:
                mapping[mp_id] = None
                not_supported_mps.add(mp_id)
            else:
                supported_mps.append(mp)
                mapping[mp_id] = mp_variant_ids[0]

        logger.debug(f"{len(not_supported_mps)} Molecular Profiles not supported: "
                     f"{not_supported_mps}")
        return supported_mps, mapping

    async def transform(self) -> None:
        """Transform CIViC harvested json to common data model."""
        data = self.extract_harvester()
        evidence_items = data['evidence']
        variants = data['variants']
        genes = data['genes']

        molecular_profiles, mp_id_to_v_id_mapping = self._mp_to_variant_mapping(
            data["molecular_profiles"]
        )

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
        """Transform statements, vrs objects, and documents from CIViC evidence items.

        :param records: CIViC Evidence Items
        :param mp_id_to_v_id_mapping: Molecular Profile ID to Variant ID mapping
            {mp_id: v_id}
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

            # Get therapy
            if len(r["therapies"]) != 1:
                continue
            else:
                therapy_id = f"civic.tid:{r['therapies'][0]['id']}"
                civic_therapeutic = self._add_therapeutic(therapy_id, r)
                if not civic_therapeutic:
                    continue

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
            mp_id = f"civic.mpid:{r['molecular_profile_id']}"
            mp = self.able_to_normalize["molecular_profiles"].get(mp_id)
            if not mp:
                logger.debug(f"mp_id not supported: {mp_id}")
                continue

            variant_id = f"civic.vid:{mp_id_to_v_id_mapping[r['molecular_profile_id']]}"
            variation_gene_map = self.able_to_normalize['variations'].get(variant_id)
            if not variation_gene_map:
                logger.debug("variant_id not supported: {variant_id}")
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
                specifiedBy=method,
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
            return Direction.REFUTES
        else:
            return Direction.NONE

    def _get_predicate(self, record_type,
                       clin_sig) -> Optional[VariantTherapeuticResponseStudyPredicate]:
        """Return predicate for an evidence item.

        :param str record_type: The evidence type
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
            mp_id = f"civic.mpid:{mp['id']}"
            vid = f"civic.vid:{mp_id_to_v_id_mapping[mp['id']]}"
            civic_variation_data = self.able_to_normalize["variations"][vid]
            aliases = (mp["aliases"] or []) + civic_variation_data["aliases"]

            mp_score = mp["molecular_profile_score"]
            if mp_score:
                extensions = [
                    core_models.Extension(
                        name="CIViC Molecular Profile Score",
                        value=mp_score
                    )
                ]
            else:
                extensions = []

            for ext_key, var_key in [
                ("CIViC representative coordinate", "coordinates"),
                ("Variant types", "variant_types")
            ]:
                if civic_variation_data[var_key]:
                    extensions.append(core_models.Extension(
                        name=ext_key,
                        value=civic_variation_data[var_key]
                    ))

            # TODO: Add support for CNVs
            if civic_variation_data["vrs_variation"]["type"] == "Allele":
                psc = ProteinSequenceConsequence(
                    id=mp_id,
                    description=mp["description"],
                    label=mp["name"],
                    definingContext=civic_variation_data["vrs_variation"],
                    aliases=list(set(aliases)) or None,
                    mappings=civic_variation_data["mappings"],
                    extensions=extensions or None,
                    members=civic_variation_data["members"]
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

            # Will remove as more get implemented in variation normalizer
            # Filtering to speed up transformation
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

            # Get members
            members = None
            genomic_hgvs = (
                [expr for expr in variant["hgvs_expressions"] if "g." in expr] or [None]
            )[0]
            if genomic_hgvs:
                vrs_genomic_variation = await self.vicc_normalizers.normalize_variation(
                    [genomic_hgvs]
                )

                if vrs_genomic_variation:
                    genomic_params = vrs_genomic_variation.model_dump(exclude_none=True)
                    genomic_params["id"] = vrs_genomic_variation.id
                    genomic_params["digest"] = vrs_genomic_variation.id.split(".")[-1]
                    genomic_params["label"] = genomic_hgvs
                    members = [models.Variation(**genomic_params)]

            params = vrs_variation.model_dump(exclude_none=True)
            params["id"] = vrs_variation.id
            params["digest"] = vrs_variation.id.split(".")[-1]
            params["label"] = variant["name"]
            civic_variation = models.Variation(**params)

            # Get extensions
            extensions = []
            hgvs_exprs = self._get_expressions(variant)
            if hgvs_exprs:
                civic_variation.root.expressions = hgvs_exprs

            variant_types_value = []
            for vt in variant["variant_types"]:
                variant_types_value.append(
                    core_models.Coding(
                        code=vt["so_id"],
                        system=f"{vt['url'].rsplit('/', 1)[0]}/",
                        label="_".join(vt["name"].lower().split())
                    )
                )

            mappings = [
                core_models.Mapping(
                    coding=core_models.Coding(
                        code=str(variant["id"]),
                        system="https://civicdb.org/variants/",
                    ),
                    relation=core_models.Relation.EXACT_MATCH
                )
            ]

            if variant["allele_registry_id"]:
                mappings.append(core_models.Mapping(
                    coding=core_models.Coding(
                        code=variant["allele_registry_id"],
                        system="https://reg.clinicalgenome.org/",
                    ),
                     relation=core_models.Relation.RELATED_MATCH
                ))

            for ce in variant["clinvar_entries"]:
                mappings.append(core_models.Mapping(
                    coding=core_models.Coding(
                        code=ce,
                        system="https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                    ),
                     relation=core_models.Relation.RELATED_MATCH
                ))

            aliases = []
            for a in variant["variant_aliases"]:
                if SNP_RE.match(a):
                    mappings.append(core_models.Mapping(
                        coding=core_models.Coding(
                            code=a.lower(),
                            system="https://www.ncbi.nlm.nih.gov/snp/",
                        ),
                        relation=core_models.Relation.RELATED_MATCH
                    ))
                else:
                    aliases.append(a)

            if variant["coordinates"]:
                coordinates = {
                    k: v for k,v in variant["coordinates"].items() if v is not None
                }
            else:
                coordinates = None

            if extensions:
                civic_variation.root.extensions = extensions

            civic_variation_dict = civic_variation.model_dump(exclude_none=True)

            self.able_to_normalize["variations"][variant_id] = {
                "vrs_variation": civic_variation_dict,
                "civic_gene_id": f"civic.gid:{variant['gene_id']}",
                "variant_types": variant_types_value or None,
                "mappings": mappings or None,
                "aliases": aliases,
                "coordinates": coordinates or None,
                "members": members
            }
            self.variations.append(civic_variation_dict)

    def _get_expressions(self, variant) -> Optional[List[Dict[str, str]]]:
        """Return a list of expressions for a given variant.

        :param dict variant: A CIViC variant record
        :return: A list of expressions
        """
        expressions = []
        for hgvs_expr in variant['hgvs_expressions']:
            if ':g.' in hgvs_expr:
                syntax = models.Syntax.HGVS_G
            elif ':c.' in hgvs_expr:
                syntax = models.Syntax.HGVS_C
            else:
                syntax = models.Syntax.HGVS_P

            if hgvs_expr != 'N/A':
                expressions.append(models.Expression(
                    syntax=syntax,
                    value=hgvs_expr
                ))
        return expressions

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
                                code=f"ncbigene:{gene['entrez_id']}",
                                system="https://www.ncbi.nlm.nih.gov/gene/"
                            ),
                            relation=core_models.Relation.EXACT_MATCH
                        )
                    ],
                    aliases=gene["aliases"] if gene["aliases"] else None,
                    extensions=[core_models.Extension(
                        name="gene_normalizer_id",
                        value=normalized_gene_id
                    )]
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
                    self.diseases.append(vrs_disease)
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
                    self.therapeutics.append(vrs_therapeutic)
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
            queries = [f"ncit:{ncit_id}", label]
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
                           f"using queries ncit:{ncit_id} and {label}")
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
            aliases=drug["aliases"] if drug["aliases"] else None,
            extensions=extensions
        ).model_dump(exclude_none=True)

    def _get_eid_document(self, source: Dict) -> Optional[Document]:
        """Get an EID's document.

        :param source: An evidence item's source
        :return: Document for EID
        """
        source_type = source['source_type'].upper()
        if source_type in SourcePrefix.__members__:
            document = Document(
                id=f"civic.source:{source['id']}",
                label=source["citation"],
                title=source["title"],
            ).model_dump(exclude_none=True)

            if source["source_type"] == SourcePrefix.PUBMED:
                document["pmid"] = int(source["citation_id"])
        else:
            logger.warning(f"{source_type} not in schemas.SourcePrefix")
            document = None

        return document
