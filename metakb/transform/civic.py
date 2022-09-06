"""A module for to transform CIViC."""
from enum import Enum
from typing import Optional, Dict, List, Set
from pathlib import Path
import logging

from ga4gh.vrsatile.pydantic.core_models import Extension, Disease, Therapeutic, \
    Coding, CombinationTherapeuticCollection, SubstituteTherapeuticCollection
from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, \
    Expression, GeneDescriptor, DiseaseDescriptor, TherapeuticDescriptor, \
    TherapeuticCollectionDescriptor

from metakb import APP_ROOT
from metakb.normalizers import VICCNormalizers
from metakb.schemas import Direction, Document, MethodId, \
    Predicate, PredictivePredicate, SourcePrefix, TargetPropositionType, \
    VariationNeoplasmTherapeuticResponseProposition, XrefSystem, VariationOrigin, \
    VariationNeoplasmTherapeuticResponseStatement
from metakb.transform.base import Transform


logger = logging.getLogger("metakb.transform.civic")
logger.setLevel(logging.DEBUG)


class EvidenceType(str, Enum):
    """Define CIViC evidence type constraints"""

    PREDICTIVE = "PREDICTIVE"
    PREDISPOSING = "PREDISPOSING"


class CIViCTransform(Transform):
    """A class for transforming CIViC to the common data model."""

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[VICCNormalizers] = None) -> None:
        """Initialize CIViC Transform class.
        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param Optional[VICCNormalizers] normalizers: normalizer collection instance
        """
        super().__init__(data_dir=data_dir,
                         harvester_path=harvester_path,
                         normalizers=normalizers)
        # Able to normalize these IDs
        self.valid_ids = {
            'variation_descriptors': dict(),
            'disease_descriptors': dict(),
            'therapeutic_descriptors': dict(),
            'therapeutic_collection_descriptors': dict()
        }
        # Unable to normalize these IDs
        self.invalid_ids = {
            'therapeutic_descriptors': set(),
            'therapeutic_collection_descriptors': set(),
            'disease_descriptors': set()
        }

    async def transform(self) -> None:
        """Transform CIViC harvested json to common data model."""
        data = self.extract_harvester()
        evidence_items = data['evidence']
        # assertions = data['assertions']
        variants = data['variants']
        genes = data['genes']

        # Filter Variant IDs for
        # Prognostic, Predictive, and Diagnostic evidence
        # TODO: Uncomment
        supported_evidence_types = [EvidenceType.PREDICTIVE]
        # supported_evidence_types = ['Prognostic', 'PREDICTIVE', 'Diagnostic']
        vids = {e['variant_id'] for e in evidence_items
                if e['evidence_type'].upper() in supported_evidence_types}
        # TODO: Uncomment
        # vids |= {a['variant']['id'] for a in assertions
        #          if a['evidence_type'].upper() in supported_evidence_types}

        await self._add_variation_descriptors(variants, vids)
        self._add_gene_descriptors(genes)
        self._transform_evidence_and_assertions(evidence_items)
        # TODO: Uncomment
        # self._transform_evidence_and_assertions(assertions, is_evidence=False)

    def _transform_evidence_and_assertions(self, records: List[Dict],
                                           is_evidence: bool = True) -> None:
        """Transform statements, propositions, descriptors, and documents
        from CIViC evidence items and assertions.

        :param List[Dict] records: CIViC Evidence Items or Assertions
        :param bool is_evidence: `True` if records are evidence items.
            `False` if records are assertions.
        """
        for r in records:
            name_lower = r['name'].lower()
            if name_lower.startswith('eid'):
                civic_id = name_lower.replace('eid', 'civic.eid:')
            else:
                civic_id = name_lower.replace('aid', 'civic.aid:')

            # Omit entries that are not in an accepted state
            if r['status'] != 'accepted':
                logger.warning(f"{civic_id} has status: {r['status']}")
                continue

            evidence_type_upper = r["evidence_type"].upper()

            if evidence_type_upper != EvidenceType.PREDICTIVE:
                continue
            #  TODO: Uncomment once we have prognostic / diagnostic
            # if evidence_type_upper not in ['Predictive', 'Prognostic',
            #                               'Diagnostic']:
            #     continue
            else:
                # Functional Evidence types do not have a disease
                if not r['disease']:
                    continue

            if evidence_type_upper == EvidenceType.PREDICTIVE:
                drugs = r["drugs"]
                len_drugs = len(drugs)
                if len_drugs == 1:
                    drug = drugs[0]
                    therapeutic_descriptor_id = f"civic.tid:{drug['id']}"
                    therapeutic_descriptor = self._add_therapeutic_descriptor(drug)
                elif len_drugs > 1:
                    therapeutic_ids = [f"civic.tid:{d['id']}" for d in drugs]
                    therapeutic_digest = self._get_digest_for_str_lists(therapeutic_ids)
                    drug_interaction_type = r["drug_interaction_type"]
                    therapeutic_descriptor_id = f"civic.tcd:{therapeutic_digest}"

                    therapeutic_descriptor = self._add_therapeutic_collection_descriptor(  # noqa: E501
                        therapeutic_descriptor_id, drugs, drug_interaction_type)
                else:
                    logger.debug(f"{r['name']} has 0 drugs")
                    continue

                if not therapeutic_descriptor:
                    continue

                if therapeutic_descriptor not in self.therapeutic_descriptors:
                    self.therapeutic_descriptors.append(therapeutic_descriptor)
            else:
                therapeutic_descriptor_id = None
                therapeutic_descriptor = None

            disease_descriptor_id = f"civic.did:{r['disease']['id']}"
            disease_descriptor = self._add_disease_descriptor(disease_descriptor_id, r)
            if not disease_descriptor:
                continue

            if disease_descriptor not in self.disease_descriptors:
                self.disease_descriptors.append(disease_descriptor)

            if is_evidence:
                variation_descriptor_id = f"civic.vid:{r['variant_id']}"
            else:
                variation_descriptor_id = f"civic.vid:{r['variant']['id']}"
            variation_descriptor = self.valid_ids['variation_descriptors'].get(
                variation_descriptor_id)
            if not variation_descriptor:
                continue

            proposition = self._get_proposition(
                r, variation_descriptor, disease_descriptor, therapeutic_descriptor)

            # Only support Therapeutic Response and Prognostic
            if not proposition:
                continue

            if proposition not in self.propositions:
                self.propositions.append(proposition)

            if is_evidence:
                # Evidence items's method and evidence level
                method = self.methods_mappping[MethodId.CIVIC_EID_SOP.value]
                if method not in self.methods:
                    self.methods.append(method)
                civic_evidence_level = f"civic.evidence_level:{r['evidence_level']}"

                evidence_level_params = self.evidence_level_vicc_concept_mapping[civic_evidence_level]  # noqa: E501
                evidence_level = Coding(**evidence_level_params).dict(exclude_none=True)

                # Supported by evidence for evidence item
                document = self._get_eid_document(r['source'])
                if document not in self.documents:
                    self.documents.append(document)
            else:
                # Assertion's method
                if r['amp_level'] and not r['acmg_codes']:
                    method = MethodId.CIVIC_AID_AMP_ASCO_CAP.value
                elif not r['amp_level'] and r['acmg_codes']:
                    method = MethodId.CIVIC_AID_ACMG.value
                else:
                    # Statements are required to have a method
                    logger.warning(f"Unable to get method for {civic_id}")
                    continue

                # assertion's evidence level
                evidence_level = self._get_assertion_evidence_level(r)

                # Supported by evidence for assertion
                supported_by = list()
                documents = self._get_aid_document(r)
                for d in documents:
                    if d not in self.documents:
                        self.documents.append(d)
                    supported_by.append(d['id'])
                for evidence_item in r['evidence_items']:
                    supported_by.append(f"civic.eid:{evidence_item['id']}")

            if evidence_type_upper == EvidenceType.PREDICTIVE:
                statement = VariationNeoplasmTherapeuticResponseStatement(
                    id=civic_id,
                    description=r["description"],
                    direction=self._get_evidence_direction(r["evidence_direction"]),
                    evidence_level=evidence_level,
                    variation_origin=self._get_variation_origin(r["variant_origin"]),
                    target_proposition=proposition["id"],
                    subject_descriptor=variation_descriptor_id,
                    neoplasm_type_descriptor=disease_descriptor_id,
                    object_descriptor=therapeutic_descriptor_id,
                    method=method,
                    is_reported_in=[document]
                ).dict(exclude_none=True)

            self.statements.append(statement)

    def _get_evidence_direction(self, direction: str) -> Optional[str]:
        """Return the evidence direction.

        :param str direction: The civic evidence_direction value
        :return: `supports` or `does_not_support` or None
        """
        direction_upper = direction.upper()
        if direction_upper == 'SUPPORTS':
            return Direction.SUPPORTS.value
        elif direction_upper == 'DOES_NOT_SUPPORT':
            return Direction.OPPOSES.value
        elif direction_upper == "NA":
            # TODO: Check if NA == Uncertain
            return Direction.UNCERTAIN.value
        else:
            return None

    def _get_assertion_evidence_level(self, assertion: Dict) -> Optional[str]:
        """Return evidence_level for CIViC assertion.

        :param Dict assertion: CIViC Assertion
        :return: CIViC assertion evidence_level
        """
        evidence_level = None
        # TODO: CHECK
        if assertion['amp_level']:
            if assertion['amp_level'] == 'Not Applicable':
                evidence_level = None
            else:
                tier, level = assertion['amp_level'].split(' - ')
                tier = tier.split()[1]
                if tier == 'I':
                    tier = 1
                elif tier == 'II':
                    tier = 2
                elif tier == 'III':
                    tier = 3
                elif tier == 'IV':
                    tier = 4
                evidence_level = f"amp_asco_cap_2017_level:{tier}{level.split()[1]}"
        return evidence_level

    def _get_proposition(
        self, record: Dict, variation_descriptor: Dict, disease_descriptor: Dict,
        therapeutic_descriptor: Dict
    ) -> Optional[Dict]:
        """Return a proposition for a record.

        :param Dict record: CIViC EID or AID
        :param Dict variation_descriptor: The record's variation descriptor
        :param Dict disease_descriptor: The record's disease descriptor
        :param Dict therapeutic_descriptor: The record's therapeutic descriptor
        :return: A proposition
        """
        try:
            proposition_type = self._get_proposition_type(record["evidence_type"])
        except KeyError:
            return None

        predicate = self._get_predicate(proposition_type,
                                        record["clinical_significance"])

        # Don't support TR that has  `None`, "N/A", or "Unknown" predicate
        if not predicate:
            return None

        params = {
            "type": proposition_type,
            "predicate": predicate,
            "subject": variation_descriptor["variation"]["id"],
            "neoplasm_type_qualifier": Disease(id=disease_descriptor["disease"]).dict(exclude_none=True)  # noqa: E501
        }

        if proposition_type == TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE:  # noqa: E501
            td_type = therapeutic_descriptor["type"]
            if td_type == "TherapeuticDescriptor":
                params["object"] = Therapeutic(id=therapeutic_descriptor["therapeutic"]).dict(exclude_none=True)  # noqa: E501
            elif td_type == "TherapeuticsCollectionDescriptor":
                params["object"] = therapeutic_descriptor["therapeutic_collection"]

        params["id"] = self._get_proposition_id(params)

        if params["id"] is None:
            return None

        # TODO: Prognostic + Diagnostic
        if proposition_type == TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE:  # noqa: E501
            proposition = VariationNeoplasmTherapeuticResponseProposition(**params).dict(exclude_none=True)  # noqa: E501
        else:
            proposition = None
        return proposition

    def _get_proposition_type(
        self, evidence_type: str, is_evidence: bool = True
    ) -> Optional[TargetPropositionType]:
        """Return proposition type for a given EID or AID.

        :param str evidence_type: CIViC evidence type
        :param bool is_evidence: `True` if EID. `False` if AID.
        :return: Proposition's type
        """
        evidence_type = evidence_type.upper()
        if evidence_type in TargetPropositionType.__members__.keys():
            if evidence_type == EvidenceType.PREDISPOSING:
                if is_evidence:
                    proposition_type = TargetPropositionType.PREDISPOSING
                else:
                    proposition_type = TargetPropositionType.PATHOGENIC
            else:
                if evidence_type == EvidenceType.PREDICTIVE:
                    proposition_type = TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE  # noqa: E501
                else:
                    # TODO: Check others
                    proposition_type = TargetPropositionType[evidence_type]
        else:
            raise KeyError(f"Proposition Type {evidence_type} not found in "
                           f"TargetPropositionType")
        return proposition_type

    def _get_variation_origin(self, variant_origin: str) -> Optional[str]:
        """Return variant origin.

        :param str variant_origin: CIViC variant origin
        :return: Variation origin
        """
        variant_origin = variant_origin.upper()
        if variant_origin == "SOMATIC":
            origin = VariationOrigin.SOMATIC.value
        elif variant_origin in ["RARE_GERMLINE", "COMMON_GERMLINE"]:
            origin = VariationOrigin.GERMLINE.value
        else:
            origin = None
        return origin

    def _get_predicate(self, proposition_type: str,
                       clin_sig: str) -> Optional[Predicate]:
        """Return predicate for an evidence item.

        :param str proposition_type: The proposition type
        :param str clin_sig: The evidence item's clinical significance
        :return: Predicate for proposition if valid
        """
        if clin_sig is None or clin_sig.upper() in ['N/A', 'UNKNOWN']:
            return None

        predicate = None

        if proposition_type == TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE:  # noqa: E501
            if clin_sig == 'SENSITIVITYRESPONSE':
                predicate = PredictivePredicate.SENSITIVITY
            elif clin_sig == 'RESISTANCE':
                predicate = PredictivePredicate.RESISTANCE
        # if proposition_type == TargetPropositionType.PREDICTIVE:
        #     if clin_sig == 'SENSITIVITY/RESPONSE':
        #         predicate = PredictivePredicate.SENSITIVITY
        #     elif clin_sig == 'RESISTANCE':
        #         predicate = PredictivePredicate.RESISTANCE
        # elif proposition_type == TargetPropositionType.DIAGNOSTIC:
        #     predicate = DiagnosticPredicate[clin_sig]
        # elif proposition_type == TargetPropositionType.PROGNOSTIC:
        #     if clin_sig == 'POSITIVE':
        #         predicate = PrognosticPredicate.BETTER_OUTCOME
        #     else:
        #         predicate = PrognosticPredicate[clin_sig]
        # elif proposition_type == TargetPropositionType.FUNCTIONAL:
        #     predicate = FunctionalPredicate[clin_sig]
        # elif proposition_type == TargetPropositionType.ONCOGENIC:
        #     # TODO: There are currently no Oncogenic types in CIViC harvester
        #     #  Look into why this is
        #     pass
        # elif proposition_type == TargetPropositionType.PATHOGENIC:
        #     if clin_sig in ['PATHOGENIC', 'LIKELY_PATHOGENIC']:
        #         predicate = PathogenicPredicate.PATHOGENIC
        else:
            logger.warning(f"CIViC proposition type: {proposition_type} "
                           f"not supported in Predicate schemas")
        return predicate

    async def _add_variation_descriptors(self, variants: List, vids: Set) -> None:
        """Add Variation Descriptors to dict of transformations.

        :param List variants: CIViC variants
        :param Set vids: Candidate CIViC Variant IDs
        """
        for variant in variants:
            if variant["id"] not in vids:
                continue
            variant_id = f"civic.vid:{variant['id']}"
            if "c." in variant["name"]:
                variant_name = variant["name"]
                if "(" in variant_name:
                    variant_name = variant_name.replace("(", "").replace(")", "")
                variant_name = variant_name.split()[-1]
            else:
                variant_name = variant["name"]

            variant_query = f"{variant['entrez_name']} {variant_name}"
            hgvs_exprs = self._get_hgvs_expr(variant)

            # TODO: Remove as more get implemented in variation normalizer
            #  Filtering to speed up transformation
            vname_lower = variant["name"].lower()

            if vname_lower.endswith("fs") or "-" in vname_lower or "/" in vname_lower:
                if not hgvs_exprs:
                    logger.warning("Variation Normalizer does not support "
                                   f"{variant_id}: {variant_query}")
                    continue

            unable_to_normalize = {
                "mutation", "amplification", "exon", "overexpression",
                "frameshift", "promoter", "deletion", "type", "insertion",
                "expression", "duplication", "copy", "underexpression",
                "number", "variation", "repeat", "rearrangement", "activation",
                "expression", "mislocalization", "translocation", "wild",
                "polymorphism", "frame", "shift", "loss", "function", "levels",
                "inactivation", "snp", "fusion", "dup", "truncation",
                "homozygosity", "gain", "phosphorylation",
            }

            if set(vname_lower.split()) & unable_to_normalize:
                logger.warning("Variation Normalizer does not support "
                               f"{variant_id}: {variant_query}")
                continue

            variation_norm_resp = await self.vicc_normalizers.normalize_variation(
                [variant_query])

            # Couldn't find normalized concept
            if not variation_norm_resp:
                logger.warning("Variation Normalizer unable to normalize "
                               f"civic.vid:{variant['id']} using query {variant_query}")
                continue

            if variant["variant_types"]:
                structural_type = variant["variant_types"][0]["so_id"]
            else:
                structural_type = None

            alternate_labels = [v_alias for v_alias in variant["variant_aliases"]
                                if not v_alias.startswith("RS")]
            xrefs = self._get_variant_xrefs(variant)

            variation_descriptor = VariationDescriptor(
                id=variant_id,
                label=variant["name"],
                description=variant["description"] if variant["description"] else None,
                variation=variation_norm_resp.variation_descriptor.variation,
                gene_context=f"civic.gid:{variant['gene_id']}",
                structural_type=structural_type,
                expressions=hgvs_exprs if hgvs_exprs else None,
                xrefs=xrefs if xrefs else None,
                alternate_labels=alternate_labels if alternate_labels else None,
                extensions=self._get_variant_extensions(variant)
            ).dict(exclude_none=True)
            self.valid_ids["variation_descriptors"][variant_id] = variation_descriptor
            self.variation_descriptors.append(variation_descriptor)

    def _get_variant_extensions(self, variant: Dict) -> list:
        """Return a list of extensions for a variant.

        :param Dict variant: A CIViC variant record
        :return: A list of extensions
        """
        extensions = [
            Extension(
                name='civic_representative_coordinate',
                value={k: v for k, v in variant['coordinates'].items() if v is not None}
            ).dict(exclude_none=True),
            Extension(
                name='civic_actionability_score',
                value=variant['civic_actionability_score']
            ).dict(exclude_none=True)
        ]

        variant_groups = variant['variant_groups']
        if variant_groups:
            v_groups = list()
            for v_group in variant_groups:
                params = {
                    'id': f"civic.variant_group:{v_group['id']}",
                    'label': v_group['name'],
                    'description': v_group['description'],
                    'type': 'variant_group'
                }
                if v_group['description'] == '':
                    del params['description']
                v_groups.append(params)
            extensions.append(Extension(name='variant_group',
                                        value=v_groups).dict(exclude_none=True))
        return extensions

    def _get_variant_xrefs(self, v: Dict) -> List[str]:
        """Return a list of xrefs for a variant.

        :param Dict v: A CIViC variant record
        :return: A list of xrefs
        """
        xrefs = []
        for xref in ['clinvar_entries', 'allele_registry_id', 'variant_aliases']:
            if xref == 'clinvar_entries':
                for clinvar_entry in v['clinvar_entries']:
                    if clinvar_entry and clinvar_entry not in {"N/A", "NONE FOUND"}:
                        xrefs.append(f"{XrefSystem.CLINVAR.value}:{clinvar_entry}")
            elif xref == 'allele_registry_id' and v['allele_registry_id']:
                xrefs.append(f"{XrefSystem.CLINGEN.value}:{v['allele_registry_id']}")
            elif xref == 'variant_aliases':
                dbsnp_xrefs = [item for item in v['variant_aliases']
                               if item.startswith('RS')]
                for dbsnp_xref in dbsnp_xrefs:
                    xrefs.append(f"{XrefSystem.DB_SNP.value}:"
                                 f"{dbsnp_xref.split('RS')[-1]}")
        return xrefs

    def _get_hgvs_expr(self, variant: List) -> List[Dict[str, str]]:
        """Return a list of hgvs expressions for a given variant.

        :param Dict variant: A CIViC variant record
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
                hgvs_expressions.append(Expression(syntax=syntax,
                                                   value=hgvs_expr).dict(exclude_none=True))  # noqa: E501
        return hgvs_expressions

    def _add_gene_descriptors(self, genes: List) -> None:
        """Add Gene Descriptors to dict of transformations.

        :param List genes: CIViC genes
        """
        for gene in genes:
            gene_id = f"civic.gid:{gene['id']}"
            ncbigene = f"ncbigene:{gene['entrez_id']}"
            queries = [ncbigene, gene['name']] + gene['aliases']

            _, normalized_gene_id = self.vicc_normalizers.normalize_gene(queries)

            if normalized_gene_id:
                gene_descriptor = GeneDescriptor(
                    id=gene_id,
                    label=gene['name'],
                    description=gene['description'] if gene['description'] else None,
                    gene=normalized_gene_id,
                    alternate_labels=gene['aliases'],
                    xrefs=[ncbigene]
                ).dict(exclude_none=True)
                self.gene_descriptors.append(gene_descriptor)
            else:
                logger.warning(f"Gene Normalizer unable to normalize {gene_id}"
                               f"using queries: {queries}")

    def _add_disease_descriptor(self, disease_id: str,
                                record: Dict) -> Optional[DiseaseDescriptor]:
        """Add disease ID to list of valid or invalid transformations.

        :param str disease_id: The CIViC ID for the disease
        :param Dict record: CIViC AID or EID
        :return: A disease descriptor
        """
        disease_descriptor = self.valid_ids['disease_descriptors'].get(disease_id)
        if disease_descriptor:
            return disease_descriptor
        else:
            disease_descriptor = None
            if disease_id not in self.invalid_ids['disease_descriptors']:
                disease_descriptor = self._get_disease_descriptors(record['disease'])
                if disease_descriptor:
                    self.valid_ids['disease_descriptors'][disease_id] = \
                        disease_descriptor
                else:
                    self.invalid_ids['disease_descriptors'].add(disease_id)
            return disease_descriptor

    def _get_disease_descriptors(self, disease: Dict) -> Optional[DiseaseDescriptor]:
        """Get a disease descriptor.

        :param Dict disease: A CIViC disease record
        :return: A Disease Descriptor
        """
        if not disease:
            return None

        disease_id = f"civic.did:{disease['id']}"
        display_name = disease['display_name']
        doid = disease['doid']

        if not doid:
            logger.warning(f"{disease_id} ({display_name}) has null DOID")
            queries = [display_name]
            xrefs = []
        else:
            doid = f"DOID:{disease['doid']}"
            queries = [doid, display_name]
            xrefs = [doid]

        _, normalized_disease_id = self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.warning(f"Disease Normalizer unable to normalize: "
                           f"{disease_id} using queries {queries}")
            return None

        disease_descriptor = DiseaseDescriptor(
            id=disease_id,
            label=display_name,
            disease=normalized_disease_id,
            xrefs=xrefs if xrefs else None
        ).dict(exclude_none=True)
        return disease_descriptor

    def _add_therapeutic_descriptor(self,
                                    drug: Dict) -> Optional[TherapeuticDescriptor]:
        """Add therapeutic ID to list of valid or invalid transformations.

        :param str therapeutic_id: The CIViC ID for the drug
        :param Dict drug: CIViC drug record
        :return: A therapeutic descriptor
        """
        therapeutic_id = f"civic.tid:{drug['id']}"
        therapeutic_descriptor = self.valid_ids['therapeutic_descriptors'].get(therapeutic_id)  # noqa: E501
        if therapeutic_descriptor:
            return therapeutic_descriptor
        else:
            therapeutic_descriptor = None
            if therapeutic_id not in self.invalid_ids['therapeutic_descriptors']:
                therapeutic_descriptor = self._get_therapeutic_descriptor(
                    therapeutic_id, drug)
                if therapeutic_descriptor:
                    self.valid_ids['therapeutic_descriptors'][therapeutic_id] = \
                        therapeutic_descriptor
                else:
                    self.invalid_ids['therapeutic_descriptors'].add(therapeutic_id)
            return therapeutic_descriptor

    def _get_therapeutic_descriptor(self, therapeutic_id: str,
                                    drug: Dict) -> Optional[TherapeuticDescriptor]:
        """Get a therapeutic descriptor.

        :param Dict drug: A CIViC drug record
        :return: A Therapeutic Descriptor
        """
        label = drug['name']
        queries = list()
        xrefs = list()
        if drug['ncit_id']:
            ncit_id = f"ncit:{drug['ncit_id']}"
            xrefs.append(ncit_id)
            queries.append(ncit_id)
        queries.append(label)

        therapy_norm_resp, normalized_therapeutic_id = \
            self.vicc_normalizers.normalize_therapy(queries)

        if not normalized_therapeutic_id:
            logger.warning(f"Therapy Normalizer unable to normalize: "
                           f"using queries {queries}")
            return None

        regulatory_approval_extension = \
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)

        alternate_labels = drug['aliases']

        therapeutic_descriptor = TherapeuticDescriptor(
            id=therapeutic_id,
            label=label,
            therapeutic=normalized_therapeutic_id,
            alternate_labels=alternate_labels if alternate_labels else None,
            xrefs=xrefs if xrefs else None,
            extensions=[regulatory_approval_extension] if regulatory_approval_extension else None  # noqa: E501
        ).dict(exclude_none=True)
        return therapeutic_descriptor

    def _add_therapeutic_collection_descriptor(
        self, therapeutic_descriptor_id: str, drugs: List[Dict],
        drug_interaction_type: str
    ) -> Optional[TherapeuticCollectionDescriptor]:
        tcd = self.valid_ids["therapeutic_collection_descriptors"].get(
            therapeutic_descriptor_id)
        if tcd:
            return tcd
        else:
            tcd = None
            if therapeutic_descriptor_id not in self.invalid_ids["therapeutic_collection_descriptors"]:  # noqa: E501
                tcd = self._get_therapeutic_collection_descriptor(
                    therapeutic_descriptor_id, drugs, drug_interaction_type)
                if tcd:
                    self.valid_ids["therapeutic_collection_descriptors"][therapeutic_descriptor_id] = tcd  # noqa: E501
                else:
                    self.invalid_ids["therapeutic_collection_descriptors"].add(
                        therapeutic_descriptor_id)
            return tcd

    def _get_therapeutic_collection_descriptor(
        self, therapeutic_descriptor_id: str, drugs: List[Dict],
        drug_interaction_type: str
    ) -> Optional[TherapeuticCollectionDescriptor]:
        member_descriptors = list()
        members = list()

        for drug in drugs:
            therapeutic_descriptor = self._add_therapeutic_descriptor(drug)
            if therapeutic_descriptor:
                member_descriptors.append(therapeutic_descriptor)
                therapeutic = Therapeutic(id=therapeutic_descriptor["therapeutic"]).dict(exclude_none=True)  # noqa: E501
                members.append(therapeutic)
            else:
                return None

        therapeutic_collection = None
        drug_interaction_type_upper = drug_interaction_type.upper()
        # TODO: Check if collection needs ID field
        if drug_interaction_type_upper in {"COMBINATION", "SEQUENTIAL"}:
            therapeutic_collection = CombinationTherapeuticCollection(members=members).dict(exclude_none=True)  # noqa: E501
        elif drug_interaction_type_upper == "SUBSTITUTES":
            therapeutic_collection = SubstituteTherapeuticCollection(members=members).dict(exclude_none=True)  # noqa: E501
        else:
            logger.debug(f"drug interaction type, {drug_interaction_type}, "
                         f"is not supported")

        if not therapeutic_collection:
            return None

        extensions = [Extension(name="civic_drug_interaction_type",
                                value=drug_interaction_type).dict(exclude_none=True)]

        tcd = TherapeuticCollectionDescriptor(
            id=therapeutic_descriptor_id,
            therapeutic_collection=therapeutic_collection,
            member_descriptors=member_descriptors,
            extensions=extensions
        ).dict(exclude_none=True)
        self.therapeutic_collection_descriptors.append(tcd)
        return tcd

    def _get_eid_document(self, source) -> Optional[Document]:
        """Get an EID's document.

        :param dict source: An evidence item's source
        :return: Document for EID
        """
        source_type = source["source_type"].upper()
        if source_type in SourcePrefix.__members__:
            xrefs = list()
            if source["asco_abstract_id"]:
                xrefs.append(f"asco.abstract:{source['asco_abstract_id']}")
            if source["pmc_id"]:
                xrefs.append(f"pmc:{source['pmc_id']}")
            if source["source_type"].upper() == "PUBMED" and source["source_url"]:
                pubmed_id = source["source_url"].split("/")[-1]
                xrefs.append(f"pmid:{pubmed_id}")

            document = Document(
                id=f"civic.source:{source['id']}",
                xrefs=xrefs if xrefs else None,
                label=source["citation"],
                title=source["name"],
            ).dict(exclude_none=True)
            return document
        else:
            logger.warning(f"{source_type} not in SourcePrefix")

    def _get_aid_document(self, assertion: Dict) -> List[Document]:
        """Get an AID's documents.

        :param dict assertion: A CIViC Assertion
        :return: A list of AID documents
        """
        # NCCN Guidlines
        documents = list()
        label = assertion["nccn_guideline"]
        version = assertion["nccn_guideline_version"]
        if label and version:
            doc_id = "https://www.nccn.org/professionals/physician_gls/default.aspx"
            doc_label = f"NCCN Guidelines: {label} version {version}"
            db_id = self._get_document_id(document_id=doc_id, label=doc_label)
            documents = list()
            documents.append(Document(
                id=db_id,
                document_id=doc_id,
                label=doc_label
            ).dict(exclude_none=True))

        # TODO: Check this after first pass
        # ACMG Codes
        if assertion['acmg_codes']:
            for acmg_code in assertion['acmg_codes']:
                document_id = f"acmg:{acmg_code['code']}"
                documents.append(Document(
                    id=document_id,
                    label=acmg_code['code'],
                    description=acmg_code['description'],
                    type="Document"
                ).dict(exclude_none=True))

        return documents
