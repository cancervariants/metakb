"""A module for to transform CIViC."""

import logging
import re
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)
from ga4gh.va_spec.aac_2017 import (
    Classification,
    Strength,
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    DiagnosticPredicate,
    Direction,
    Document,
    EvidenceLine,
    MembershipOperator,
    PrognosticPredicate,
    Statement,
    System,
    TherapeuticResponsePredicate,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele, Expression, Syntax, Variation
from pydantic import BaseModel, ValidationError

from metakb import APP_ROOT
from metakb.harvesters.civic import CivicHarvestedData
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.transformers.base import (
    CivicEvidenceLevel,
    MethodId,
    Transformer,
    _TransformedRecordsCache,
)

_logger = logging.getLogger(__name__)

# SNP pattern
SNP_RE = re.compile(r"RS\d+")

# Variant names that are known to not be supported in the variation-normalizer
UNABLE_TO_NORMALIZE_VAR_NAMES = {
    "mutation",
    "exon",
    "overexpression",
    "frameshift",
    "promoter",
    "deletion",
    "type",
    "insertion",
    "expression",
    "duplication",
    "copy",
    "underexpression",
    "number",
    "variation",
    "repeat",
    "rearrangement",
    "activation",
    "mislocalization",
    "translocation",
    "wild",
    "polymorphism",
    "frame",
    "shift",
    "loss",
    "function",
    "levels",
    "inactivation",
    "snp",
    "fusion",
    "dup",
    "truncation",
    "homozygosity",
    "gain",
    "phosphorylation",
}

# CIViC significance to GKS predicate
CLIN_SIG_TO_PREDICATE = {
    "SENSITIVITYRESPONSE": TherapeuticResponsePredicate.SENSITIVITY,
    "RESISTANCE": TherapeuticResponsePredicate.RESISTANCE,
    "POOR_OUTCOME": PrognosticPredicate.WORSE_OUTCOME,
    "BETTER_OUTCOME": PrognosticPredicate.BETTER_OUTCOME,
    "POSITIVE": DiagnosticPredicate.INCLUSIVE,
    "NEGATIVE": DiagnosticPredicate.EXCLUSIVE,
}


class _CivicInteractionType(str, Enum):
    """Define constraints for CIViC interaction types supported by MetaKB

    SEQUENTIAL is not currently supported
    """

    SUBSTITUTES = "SUBSTITUTES"
    COMBINATION = "COMBINATION"


class _TherapeuticMetadata(BaseModel):
    """Define model for CIVIC therapeutic metadata"""

    therapy_id: str
    membership_operator: MembershipOperator | None
    therapies: list[dict]


class _CivicEvidenceAssertionType(str, Enum):
    """Define constraints for CIViC evidence and assertion types supported by MetaKB

    DIAGNOSTIC, ONCOGENIC, PREDISPOSING are not currently supported
    """

    PREDICTIVE = "PREDICTIVE"
    PROGNOSTIC = "PROGNOSTIC"
    DIAGNOSTIC = "DIAGNOSTIC"


class _VariationCache(BaseModel):
    """Create model for caching CIViC Variation data that will be accessed when
    transforming MP data
    """

    vrs_variation: Variation | None = None
    civic_gene_id: str
    variant_types: list[Coding] | None = None
    mappings: list[ConceptMapping] | None = None
    aliases: list[str] | None = None
    coordinates: dict | None = None
    members: list[Variation] | None = None
    extensions: list[Extension] | None = None


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = "PUBMED"
    ASCO = "ASCO"
    ASH = "ASH"


class CivicEvidenceName(str, Enum):
    """Define constraints for CIViC evidence names"""

    VALIDATED_ASSOCIATION = "Validated association"
    CLINICAL_EVIDENCE = "Clinical evidence"
    CASE_STUDY = "Case study"
    PRECLINICAL_EVIDENCE = "Preclinical evidence"
    INFERENTIAL_ASSOCIATION = "Inferential association"


CIVIC_EVIDENCE_LEVEL_TO_NAME = MappingProxyType(
    {
        CivicEvidenceLevel.A: CivicEvidenceName.VALIDATED_ASSOCIATION,
        CivicEvidenceLevel.B: CivicEvidenceName.CLINICAL_EVIDENCE,
        CivicEvidenceLevel.C: CivicEvidenceName.CASE_STUDY,
        CivicEvidenceLevel.D: CivicEvidenceName.PRECLINICAL_EVIDENCE,
        CivicEvidenceLevel.E: CivicEvidenceName.INFERENTIAL_ASSOCIATION,
    }
)


class _CivicTransformedCache(_TransformedRecordsCache):
    """Create model for caching CIViC data"""

    variations: ClassVar[dict[str, _VariationCache]] = {}
    categorical_variants: ClassVar[dict[str, CategoricalVariant]] = {}
    evidence: ClassVar[
        dict[
            str,
            Statement,
        ]
    ] = {}


class CivicTransformer(Transformer):
    """A class for transforming CIViC to the common data model."""

    def __init__(
        self,
        data_dir: Path = APP_ROOT / "data",
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize CIViC Transformer class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested CIViC data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        # Method will always be the same
        self.processed_data.methods = [
            self.methods_mapping[MethodId.CIVIC_EID_SOP.value]
        ]
        self._cache = self._create_cache()

    def _create_cache(self) -> _CivicTransformedCache:
        """Create cache for transformed records"""
        return _CivicTransformedCache()

    @staticmethod
    def _mp_to_variant_mapping(molecular_profiles: list[dict]) -> tuple[list, dict]:
        """Get mapping from Molecular Profile ID to Variant ID.
        We currently do not handle complex molecular profiles (> 1 variant associated).

        :param molecular_profiles: List of civic molecular profiles represented as
            dictionaries
        :return: Tuple containing list of supported molecular profiles and mapping from
            Molecular Profile ID to Variant ID {mp_id: v_id}
        """
        mp_id_to_v_id: dict = {}
        supported_mps = []
        not_supported_mp_ids = set()
        for mp in molecular_profiles:
            mp_id = mp["id"]
            mp_variant_ids = mp["variant_ids"]
            if len(mp_variant_ids) != 1:
                mp_id_to_v_id[mp_id] = None
                not_supported_mp_ids.add(mp_id)
            else:
                supported_mps.append(mp)
                mp_id_to_v_id[mp_id] = mp_variant_ids[0]

        _logger.debug(
            "%s Molecular Profiles not supported: %s",
            len(not_supported_mp_ids),
            not_supported_mp_ids,
        )
        return supported_mps, mp_id_to_v_id

    async def transform(self, harvested_data: CivicHarvestedData) -> None:
        """Transform CIViC harvested json to common data model. Will store transformed
        results in ``processed_data`` instance variable.

        :param harvested_data: CIViC harvested data
        """
        evidence_items = harvested_data.evidence

        # Get list of supported molecular profiles and mapping to variant id
        molecular_profiles, mp_id_to_v_id_mapping = self._mp_to_variant_mapping(
            harvested_data.molecular_profiles
        )

        # Only want evidence with approved status and evidence type supported by MetaKB
        evidence_items = [
            e
            for e in evidence_items
            if e["status"] == "accepted"
            and e["evidence_type"] in _CivicEvidenceAssertionType.__members__
        ]

        # Only want assertions with approved status and assertion
        assertions = harvested_data.assertions
        assertions = [
            assertion
            for assertion in assertions
            if assertion["status"] == "accepted"
            and assertion["assertion_type"] in _CivicEvidenceAssertionType.__members__
        ]

        # Get all variant IDs from supported molecular profiles
        vids = {
            mp_id_to_v_id_mapping.get(e["molecular_profile_id"])
            for e in evidence_items
            if e["molecular_profile_id"]
        }
        vids |= {
            mp_id_to_v_id_mapping.get(assertion["molecular_profile_id"])
            for assertion in assertions
            if assertion["molecular_profile_id"]
        }
        vids.discard(None)

        # Add variant (only supported) and gene (all) data
        # (mutates `variations` and `genes`)
        variants = harvested_data.variants
        variants = [v for v in variants if v["id"] in vids]
        await self._add_variations(variants)
        self._add_genes(harvested_data.genes)

        mps = [
            mp
            for mp in molecular_profiles
            if f"civic.vid:{mp['variant_ids'][0]}" in self._cache.variations
        ]
        self._add_categorical_variants(mps, mp_id_to_v_id_mapping)

        for evidence_item in evidence_items:
            self._add_variant_study_stmt(
                evidence_item, mp_id_to_v_id_mapping, is_evidence=True
            )

        for assertion in assertions:
            self._add_variant_study_stmt(
                assertion, mp_id_to_v_id_mapping, is_evidence=False
            )

    def _add_variant_study_stmt(
        self, record: dict, mp_id_to_v_id_mapping: dict, is_evidence: bool = True
    ) -> None:
        """Create Variant Study Statement given CIViC Evidence Items.
        Will add associated values to ``processed_data`` instance variable
        (``therapies``, ``conditions``, and ``documents``).
        ``_cache`` will also be mutated for associated therapies and conditions.

        :param record: CIViC Evidence Item or Assertion
        :param mp_id_to_v_id_mapping: Molecular Profile ID to Variant ID mapping
            {mp_id: v_id}
        :param is_evidence: ``True`` if ``record`` is an evidence item. ``False`` if
            ``record`` is an assertion.
        """
        # Check cache for molecular profile, variation and gene data
        mp_id = f"civic.mpid:{record['molecular_profile_id']}"
        mp = self._cache.categorical_variants.get(mp_id)
        if not mp:
            _logger.debug("mp_id not supported: %s", mp_id)
            return

        variant_id = (
            f"civic.vid:{mp_id_to_v_id_mapping[record['molecular_profile_id']]}"
        )
        variation_gene_map = self._cache.variations.get(variant_id)
        if not variation_gene_map:
            _logger.debug("variant_id not supported: %s", variant_id)
            return

        extensions = []
        classification = None
        record_prefix = "evidence" if is_evidence else "assertion"
        direction = self._get_direction(record[f"{record_prefix}_direction"])

        if is_evidence:
            evidence_lines = None
            document = self._add_eid_document(record["source"])
            if not document:
                return

            reported_in = [document] if document else None

            evidence_level = CivicEvidenceLevel[record["evidence_level"]]
            strength = self._get_eid_strength(evidence_level)
        else:
            reported_in = None

            if record["amp_level"]:
                classification, strength = self._get_aid_classification_and_strength(
                    record["amp_level"]
                )
                if not classification and not strength:
                    _logger.debug("No classification and/or strength found")
                    return

            evidence_lines = []
            for eid in record["evidence_ids"]:
                civic_eid = f"civic.eid:{eid}"
                evidence_item = self._cache.evidence.get(civic_eid)
                if evidence_item:
                    evidence_lines.append(
                        EvidenceLine(
                            hasEvidenceItems=[evidence_item],
                            directionOfEvidenceProvided=Direction.SUPPORTS,
                        )
                    )

        record_type = record[f"{record_prefix}_type"]

        # Get predicate
        predicate = CLIN_SIG_TO_PREDICATE.get(record["significance"])

        # Don't support evidence that has  `None`, "N/A", or "Unknown" predicate
        if not predicate:
            return

        # Add disease
        disease = record["disease"]
        if not disease:
            return

        civic_disease = self._add_disease(disease)
        if not civic_disease:
            return

        civic_therapeutic = None
        if record_type == _CivicEvidenceAssertionType.PREDICTIVE:
            therapeutic_metadata = self._get_therapeutic_metadata(record)
            if therapeutic_metadata:
                civic_therapeutic = self._add_therapy(
                    therapeutic_metadata.therapy_id,
                    therapeutic_metadata.therapies,
                    therapeutic_metadata.membership_operator,
                )
            if not civic_therapeutic:
                return

            condition_key = "conditionQualifier"
        else:
            condition_key = "objectCondition"

        # Get qualifier
        civic_gene = self._cache.genes.get(variation_gene_map.civic_gene_id)

        variant_origin = record["variant_origin"].lower()
        allele_origin_qualifier = MappableConcept(name=variant_origin)
        statement_id = record["name"].lower()
        statement_id = (
            statement_id.replace("eid", "civic.eid:")
            if is_evidence
            else statement_id.replace("aid", "civic.aid:")
        )

        stmt_params = {
            "id": statement_id,
            "description": record["description"] or None,
            "direction": direction,
            "strength": strength,
            "specifiedBy": self.processed_data.methods[0],
            "reportedIn": reported_in,
            "extensions": extensions or None,
            "hasEvidenceLines": evidence_lines or None,
        }

        if not is_evidence:
            stmt_params["classification"] = classification

        prop_params = {
            "predicate": predicate,
            condition_key: civic_disease,
            "alleleOriginQualifier": allele_origin_qualifier,
            "geneContextQualifier": civic_gene,
            "subjectVariant": mp,
        }

        if record_type == _CivicEvidenceAssertionType.PREDICTIVE:
            prop_params["objectTherapeutic"] = civic_therapeutic
            stmt_params["proposition"] = VariantTherapeuticResponseProposition(
                **prop_params
            )
            statement = (
                Statement(**stmt_params)
                if is_evidence
                else VariantTherapeuticResponseStudyStatement(**stmt_params)
            )
        elif record_type == _CivicEvidenceAssertionType.PROGNOSTIC:
            stmt_params["proposition"] = VariantPrognosticProposition(**prop_params)
            statement = (
                Statement(**stmt_params)
                if is_evidence
                else VariantPrognosticStudyStatement(**stmt_params)
            )
        else:
            stmt_params["proposition"] = VariantDiagnosticProposition(**prop_params)
            statement = (
                Statement(**stmt_params)
                if is_evidence
                else VariantDiagnosticStudyStatement(**stmt_params)
            )

        if is_evidence:
            self._cache.evidence[statement_id] = statement
            self.processed_data.statements_evidence.append(statement)
        else:
            self.processed_data.statements_assertions.append(statement)

    def _get_eid_strength(self, evidence_level: CivicEvidenceLevel) -> MappableConcept:
        """Get CIViC Evidence Item strength

        :param evidence_level: CIViC evidence level
        :return: Strength for CIViC evidence item
        """
        return MappableConcept(
            name=CIVIC_EVIDENCE_LEVEL_TO_NAME[evidence_level],
            primaryCoding=Coding(
                system="https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                code=evidence_level.value,
            ),
            mappings=self.evidence_level_to_vicc_concept_mapping[evidence_level],
        )

    def _get_aid_classification_and_strength(
        self,
        amp_level: str,
    ) -> tuple[MappableConcept | None, MappableConcept | None]:
        """Get statement classification and strength

        :param amp_level: AMP/ASCO/CAP level
        :return: Classification and strength, if found
        """
        classification = None
        strength = None
        system = System.AMP_ASCO_CAP

        if amp_level != "NA":
            pattern = re.compile(r"TIER_(?P<tier>[IV]+)(?:_LEVEL_(?P<level>[A-D]))?")
            match = pattern.match(amp_level).groupdict()
            classification = MappableConcept(
                primaryCoding=Coding(
                    code=Classification(f"Tier {match['tier']}"), system=system
                ),
            )

            level = match["level"]
            evidence_strength = self._get_eid_strength(CivicEvidenceLevel(level))
            mappings = evidence_strength.mappings
            evidence_strength.primaryCoding.name = evidence_strength.name
            mappings.append(
                ConceptMapping(
                    coding=evidence_strength.primaryCoding,
                    relation=Relation.EXACT_MATCH,
                )
            )

            strength = MappableConcept(
                primaryCoding=Coding(code=Strength(f"Level {level}"), system=system),
                mappings=mappings,
            )

        return classification, strength

    def _get_direction(self, direction: str) -> Direction | None:
        """Get the normalized evidence or assertion direction

        :param direction: CIViC evidence item or assertion's direction
        :return: Normalized evidence or assertion direction
        """
        direction_upper = direction.upper()
        if direction_upper == "SUPPORTS":
            return Direction.SUPPORTS
        if direction_upper == "DOES_NOT_SUPPORT":
            return Direction.DISPUTES
        return None

    def _add_categorical_variants(
        self, molecular_profiles: list[dict], mp_id_to_v_id_mapping: dict
    ) -> None:
        """Create Categorical Variant objects for all supported MP records.
        Mutates instance variables ``_cache.categorical_variants`` and
        ``processed_data.categorical_variants``.

        :param molecular_profiles: List of supported Molecular Profiles in CIViC.
            The associated, single variant record for each MP
        :param mp_id_to_v_id_mapping: Mapping from Molecular Profile ID to Variant ID
            {mp_id: v_id}
        """
        for mp in molecular_profiles:
            mp_id = f"civic.mpid:{mp['id']}"
            vid = f"civic.vid:{mp_id_to_v_id_mapping[mp['id']]}"
            civic_variation_data: _VariationCache = self._cache.variations[vid]

            extensions = civic_variation_data.extensions or []

            # Get aliases from MP and Variant record
            aliases = civic_variation_data.aliases or []

            for a in mp["aliases"] or []:
                if not SNP_RE.match(a) and a not in aliases:
                    aliases.append(a)

            # Get molecular profile score data
            mp_score = mp["molecular_profile_score"]
            if mp_score:
                extensions.append(
                    Extension(name="CIViC Molecular Profile Score", value=mp_score)
                )

            # Get CIViC representative coordinate and Variant types data
            for ext_key, var_key in [
                ("CIViC representative coordinate", "coordinates"),
                ("Variant types", "variant_types"),
            ]:
                civic_variation_data_value = getattr(civic_variation_data, var_key)
                if civic_variation_data_value:
                    extensions.append(
                        Extension(name=ext_key, value=civic_variation_data_value)
                    )

            constraints = None
            if civic_variation_data.vrs_variation and isinstance(
                civic_variation_data.vrs_variation.root, Allele
            ):
                constraints = [
                    DefiningAlleleConstraint(
                        allele=civic_variation_data.vrs_variation.root,
                    )
                ]

            cv = CategoricalVariant(
                id=mp_id,
                description=mp["description"],
                name=mp["name"],
                constraints=constraints,
                aliases=aliases or None,
                mappings=civic_variation_data.mappings,
                extensions=extensions or None,
                members=civic_variation_data.members,
            )
            self.processed_data.categorical_variants.append(cv)
            self._cache.categorical_variants[mp_id] = cv

    @staticmethod
    def _get_variant_name(variant: dict) -> str:
        """Get variant name from CIViC Variant record.
        If 'c.' in name, use the cDNA name

        :param variant: CIViC Variant record
        :return: Variant name to use for query
        """
        if "c." in variant["name"]:
            variant_name = variant["name"]
            if "(" in variant_name:
                variant_name = variant_name.replace("(", "").replace(")", "")
            variant_name = variant_name.split()[-1]
        else:
            variant_name = variant["name"]
        return variant_name

    @staticmethod
    def _is_supported_variant_query(variant_name: str, variant_id: int) -> bool:
        """Determine if a variant name is supported by the variation-normalizer.
        This is used to skip normalization on variants that the variation-normalizer
        is known not to support

        :param variant_name: Variant name in CIViC
        :param variant_id: CIViC Variant ID
        :return: `True` if the variant_name is supported in the variation-normalizer.
            `False` otherwise
        """
        # Will remove as more get implemented in variation normalizer
        # Filtering to speed up transformation
        vname_lower = variant_name.lower()

        if vname_lower.endswith("fs") or "-" in vname_lower or "/" in vname_lower:
            _logger.debug(
                "Variation Normalizer does not support %s: %s", variant_id, variant_name
            )
            return False

        if set(vname_lower.split()) & UNABLE_TO_NORMALIZE_VAR_NAMES:
            _logger.debug(
                "Variation Normalizer does not support %s: %s", variant_id, variant_name
            )
            return False

        return True

    async def _get_variation_members(self, variant: dict) -> list[Variation]:
        """Get members field for variation object. This is the related variant concepts.

        :param variant: CIViC Variant record
        :return: List containing one VRS variation record for associated HGVS
            expression, if variation-normalizer was able to normalize
        """
        members = []
        for hgvs_expr in variant["hgvs_expressions"]:
            if hgvs_expr == "N/A" or "p." in hgvs_expr:
                continue

            if "c." in hgvs_expr:
                syntax = Syntax.HGVS_C
            elif "g." in hgvs_expr:
                syntax = Syntax.HGVS_G
            else:
                _logger.debug("Syntax not recognized: %s", hgvs_expr)
                continue

            vrs_variation = await self.vicc_normalizers.normalize_variation(hgvs_expr)

            if vrs_variation:
                variation_params = vrs_variation.model_dump(exclude_none=True)
                variation_params["extensions"] = (
                    None  # Don't care about capturing extensions for now
                )
                variation_params["name"] = hgvs_expr
                variation_params["expressions"] = [
                    Expression(syntax=syntax, value=hgvs_expr)
                ]
                members.append(Variation(**variation_params))
        return members

    async def _add_variations(self, variants: list[dict]) -> None:
        """Transform supported CIViC variant records.

        Mutates instance variables ``_cache.variations`` and
        ``processed_data.variations``

        :param variants: List of all CIViC variant records
        """
        for variant in variants:
            variant_id = f"civic.vid:{variant['id']}"
            variant_name = self._get_variant_name(variant)
            variant_query = f"{variant['entrez_name']} {variant_name}"
            vrs_variation = None
            civic_variation = None
            extensions = []

            if self._is_supported_variant_query(variant_name, variant_id):
                vrs_variation = await self.vicc_normalizers.normalize_variation(
                    variant_query
                )

            if not vrs_variation:
                _logger.debug(
                    "Variation Normalizer unable to normalize %s using query %s",
                    variant_id,
                    variant_query,
                )
                extensions.append(self._get_vicc_normalizer_failure_ext())
                members = None
            else:
                # Create VRS Variation object
                params = vrs_variation.model_dump(exclude_none=True)
                params["name"] = variant["name"]
                civic_variation = Variation(**params)

                # Get members
                members = await self._get_variation_members(variant)

            # Get expressions
            hgvs_exprs = self._get_expressions(variant)
            if hgvs_exprs:
                if civic_variation:
                    civic_variation.root.expressions = hgvs_exprs
                else:
                    extensions.append(Extension(name="expressions", value=hgvs_exprs))

            # Get variant types
            variant_types_value = [
                Coding(
                    id=vt["so_id"],
                    code=vt["so_id"],
                    system=f"{vt['url'].rsplit('/', 1)[0]}/",
                    name="_".join(vt["name"].lower().split()),
                )
                for vt in variant["variant_types"]
                if vt and vt["url"]  # system is required
            ]

            # Get mappings
            mappings = [
                ConceptMapping(
                    coding=Coding(
                        id=variant_id,
                        code=str(variant["id"]),
                        system="https://civicdb.org/variants/",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            ]

            if variant["allele_registry_id"]:
                mappings.append(
                    ConceptMapping(
                        coding=Coding(
                            code=variant["allele_registry_id"],
                            system="https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                        ),
                        relation=Relation.RELATED_MATCH,
                    )
                )

            mappings.extend(
                ConceptMapping(
                    coding=Coding(
                        code=ce,
                        system="https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                    ),
                    relation=Relation.RELATED_MATCH,
                )
                for ce in variant["clinvar_entries"]
            )

            aliases = []
            for a in variant["variant_aliases"]:
                if SNP_RE.match(a):
                    a = a.lower()
                    mappings.append(
                        ConceptMapping(
                            coding=Coding(
                                code=a,
                                system="https://www.ncbi.nlm.nih.gov/snp/",
                            ),
                            relation=Relation.RELATED_MATCH,
                        )
                    )
                else:
                    aliases.append(a)

            if variant["coordinates"]:
                coordinates = {
                    k: v for k, v in variant["coordinates"].items() if v is not None
                }
            else:
                coordinates = None

            if civic_variation:
                self.processed_data.variations.append(civic_variation.root)

            self._cache.variations[variant_id] = _VariationCache(
                vrs_variation=civic_variation,
                civic_gene_id=f"civic.gid:{variant['gene_id']}",
                variant_types=variant_types_value or None,
                mappings=mappings or None,
                aliases=aliases or None,
                extensions=extensions,
                coordinates=coordinates or None,
                members=members,
            )

    def _get_expressions(self, variant: dict) -> list[Expression]:
        """Get expressions for a given variant

        :param variant: A CIViC variant record
        :return: A list of expressions
        """
        expressions = []
        for hgvs_expr in variant["hgvs_expressions"]:
            if ":p." in hgvs_expr:
                syntax = Syntax.HGVS_P
            elif ":c." in hgvs_expr:
                syntax = Syntax.HGVS_C
            elif ":g." in hgvs_expr:
                syntax = Syntax.HGVS_G
            elif ":n." in hgvs_expr:
                syntax = Syntax.HGVS_N
            elif ":m." in hgvs_expr:
                syntax = Syntax.HGVS_M
            elif ":r." in hgvs_expr:
                syntax = Syntax.HGVS_R
            else:
                continue

            if hgvs_expr != "N/A":
                expressions.append(Expression(syntax=syntax, value=hgvs_expr))
        return expressions

    @staticmethod
    def _update_normalizer_mappings(
        mappings: list[ConceptMapping],
        civic_primary_id: str,
        get_concept_mapping_method: Callable,
    ) -> None:
        """Update ``mappings`` when concepts successfully normalize

        There are some instances where CIViC and the VICC Normalizer provide the same
        identifier, in these cases the mapping will contain both a VICC normalizer
        priority extension and CIViC annotation extension.

        Log instances where there is a mismatch between CIViC and the VICC normalizer

        :param mappings: List of normalized concept mappings from the VICC normalizer.
            This will be mutated
        :param civic_primary_id: The primary source identifier provided by CIViC
        :param get_concept_mapping_method: Method for getting concept mapping
        """
        civic_annotation_match = False
        for mapping in mappings:
            if mapping.coding.id.startswith(
                civic_primary_id[: civic_primary_id.find(":") + 1]
            ):
                if mapping.coding.id == civic_primary_id:
                    civic_annotation_ext = Extension(
                        name="civic_annotation", value=True
                    )
                    if mapping.extensions:
                        mapping.extensions.append(civic_annotation_ext)
                    else:
                        mapping.extensions = [civic_annotation_ext]
                    civic_annotation_match = True
                    break

                _logger.debug(
                    "CIViC primary concept identifier and Normalizer mismatch: %s vs %s",
                    civic_primary_id,
                    mapping.coding.id,
                )

                break

        if not civic_annotation_match:
            mappings.append(get_concept_mapping_method(civic_primary_id))

    def _add_genes(self, genes: list[dict]) -> None:
        """Create gene objects for all CIViC gene records.

        Mutates instance variables ``_cache.genes`` and ``processed_data.genes``

        :param genes: All genes in CIViC
        """

        def _get_ncbi_concept_mapping(ncbigene_id: str) -> ConceptMapping:
            """Get NCBI gene mapping

            :param ncbigene_id: ID for NCBI Gene
            :param gene: CIViC gene record
            :return: Concept Mapping for NCBI Gene
            """
            return ConceptMapping(
                coding=Coding(
                    id=ncbigene_id,
                    code=ncbigene_id.split(":")[-1],
                    system="https://www.ncbi.nlm.nih.gov/gene/",
                ),
                relation=Relation.EXACT_MATCH,
            )

        for gene in genes:
            gene_id = f"civic.gid:{gene['id']}"
            ncbigene = f"ncbigene:{gene['entrez_id']}"
            queries = [ncbigene, gene["name"]] + gene["aliases"]
            extensions = []

            for query in queries:
                gene_norm_resp, normalized_gene_id = (
                    self.vicc_normalizers.normalize_gene(query)
                )
                if normalized_gene_id:
                    break

            if not normalized_gene_id:
                _logger.debug(
                    "Gene Normalizer unable to normalize: %s using queries %s",
                    gene_id,
                    queries,
                )
                extensions.append(self._get_vicc_normalizer_failure_ext())
                mappings = [_get_ncbi_concept_mapping(ncbigene)]
            else:
                mappings = self._get_vicc_normalizer_mappings(
                    normalized_gene_id, gene_norm_resp
                )
                self._update_normalizer_mappings(
                    mappings, ncbigene, _get_ncbi_concept_mapping
                )

            if gene["aliases"]:
                extensions.append(Extension(name="aliases", value=gene["aliases"]))

            if gene["description"]:
                extensions.append(
                    Extension(name="description", value=gene["description"])
                )

            civic_gene = MappableConcept(
                id=gene_id,
                conceptType="Gene",
                name=gene["name"],
                mappings=mappings,
                extensions=extensions or None,
            )
            self._cache.genes[gene_id] = civic_gene
            self.processed_data.genes.append(civic_gene)

    def _add_disease(self, disease: dict) -> MappableConcept:
        """Create or get disease given CIViC disease.
        First looks in cache for existing disease, if not found will attempt to
        transform. Will add CIViC disease ID to ``processed_data.conditions`` and
        ``_cache.conditions``

        :param disease: CIViC Disease object
        :return: Disease represented as mappable concept
        """
        disease_id = f"civic.did:{disease['id']}"
        civic_disease = self._cache.conditions.get(disease_id)
        if civic_disease:
            return civic_disease

        civic_disease = self._get_disease(disease)
        self._cache.conditions[disease_id] = civic_disease
        self.processed_data.conditions.append(civic_disease)
        return civic_disease

    def _get_disease(self, disease: dict) -> MappableConcept:
        """Get Disease object for a CIViC disease

        :param disease: CIViC disease record
        :return: Disease represented as a mappable concept
        """

        def _get_doid_concept_mapping(doid: str) -> ConceptMapping:
            """Get DOID mapping

            :param doid: DO identifier
            :return: Concept mapping for DOID
            """
            return ConceptMapping(
                coding=Coding(
                    id=doid,
                    code=doid,
                    system="https://disease-ontology.org/?id=",
                ),
                relation=Relation.EXACT_MATCH,
            )

        disease_id = f"civic.did:{disease['id']}"
        display_name = disease["display_name"]
        doid = disease["doid"]

        if not doid:
            _logger.debug("%s (%s) has null DOID", disease_id, display_name)
            queries = [display_name]
        else:
            doid = f"DOID:{doid}"
            queries = [doid, display_name]

        for query in queries:
            (
                disease_norm_resp,
                normalized_disease_id,
            ) = self.vicc_normalizers.normalize_disease(query)
            if normalized_disease_id:
                break

        extensions = []

        if not normalized_disease_id:
            _logger.debug(
                "Disease Normalizer unable to normalize: %s using queries %s",
                disease_id,
                queries,
            )
            mappings = [_get_doid_concept_mapping(doid)] if doid else []
            extensions.append(self._get_vicc_normalizer_failure_ext())
        else:
            mappings = self._get_vicc_normalizer_mappings(
                normalized_disease_id, disease_norm_resp
            )

            if doid:
                self._update_normalizer_mappings(
                    mappings, doid, _get_doid_concept_mapping
                )

        return MappableConcept(
            id=disease_id,
            conceptType="Disease",
            name=display_name,
            mappings=mappings or None,
            extensions=extensions or None,
        )

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies_in: list[dict],
    ) -> TherapyGroup | None:
        """Get Therapeutic Substitute Group for CIViC therapies

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies_in: List of CIViC therapy objects
        :return: Therapeutic Substitute Group
        """
        therapies = []

        for therapy in therapies_in:
            therapy_id = f"civic.tid:{therapy['id']}"
            therapy = self._add_therapy(therapy_id, [therapy], membership_operator=None)
            if not therapy:
                return None

            therapies.append(therapy)

        try:
            tg = TherapyGroup(
                membershipOperator=MembershipOperator.OR,
                id=therapeutic_sub_group_id,
                therapies=therapies,
            )
        except ValidationError as e:
            # If substitutes validation checks fail
            _logger.debug(
                "ValidationError raised when attempting to create TherapeuticSubstituteGroup: %s",
                {e},
            )
            tg = None

        return tg

    def _get_therapy(self, therapy_id: str, therapy: dict) -> MappableConcept:
        """Get Therapy mappable concept for CIViC therapy

        :param therapy_id: ID for therapy
        :param therapy: CIViC therapy object
        :return: Therapy represented as a mappable concept
        """

        def _get_ncit_concept_mapping(ncit_id: str) -> ConceptMapping:
            """Get NCIt mapping

            :param ncit_id: NCIt identifier
            :return: Concept mapping for NCIt
            """
            return ConceptMapping(
                coding=Coding(
                    id=ncit_id,
                    code=ncit_id.split(":")[-1],
                    system="https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                ),
                relation=Relation.EXACT_MATCH,
            )

        name = therapy["name"]
        ncit_id = f"ncit:{therapy['ncit_id']}"
        queries = [ncit_id, name] if therapy["ncit_id"] else [name]

        extensions = []
        if therapy["aliases"]:
            extensions.append(Extension(name="aliases", value=therapy["aliases"]))

        for query in queries:  # Order matters (use highest match first)
            (
                therapy_norm_resp,
                normalized_therapeutic_id,
            ) = self.vicc_normalizers.normalize_therapy(query)
            if normalized_therapeutic_id:
                break

        if not normalized_therapeutic_id:
            _logger.debug(
                "Therapy Normalizer unable to normalize: using queries ncit:%s and %s",
                ncit_id,
                name,
            )

            mappings = (
                [_get_ncit_concept_mapping(ncit_id)] if therapy["ncit_id"] else []
            )
            extensions.append(self._get_vicc_normalizer_failure_ext())
        else:
            regulatory_approval_extension = (
                self.vicc_normalizers.get_regulatory_approval_extension(
                    therapy_norm_resp
                )
            )

            if regulatory_approval_extension:
                extensions.append(regulatory_approval_extension)

            mappings = self._get_vicc_normalizer_mappings(
                normalized_therapeutic_id, therapy_norm_resp
            )

            if therapy["ncit_id"]:
                self._update_normalizer_mappings(
                    mappings, ncit_id, _get_ncit_concept_mapping
                )

        return MappableConcept(
            id=therapy_id,
            name=name,
            conceptType="Therapy",
            mappings=mappings or None,
            extensions=extensions or None,
        )

    def _get_therapeutic_metadata(
        self, evidence_item: dict
    ) -> _TherapeuticMetadata | None:
        """Get therapeutic metadata

        :param evidence_item: CIViC Predictive Evidence Item
        :return: Therapeutic metadata, if interaction type is supported
        """
        therapies = evidence_item["therapies"]
        if len(therapies) == 1:
            # Add therapy
            therapy_id = f"civic.tid:{therapies[0]['id']}"
            membership_operator = None
        else:
            # Add therapy group
            therapy_interaction_type = evidence_item["therapy_interaction_type"]
            therapeutic_ids = [f"civic.tid:{t['id']}" for t in therapies]
            therapeutic_digest = self._get_digest_for_str_lists(therapeutic_ids)

            if therapy_interaction_type == _CivicInteractionType.SUBSTITUTES:
                therapy_id = f"civic.tsgid:{therapeutic_digest}"
                membership_operator = MembershipOperator.OR
            elif therapy_interaction_type == _CivicInteractionType.COMBINATION:
                therapy_id = f"civic.ctid:{therapeutic_digest}"
                membership_operator = MembershipOperator.AND
            else:
                _logger.debug(
                    "civic therapy_interaction_type not supported: %s",
                    therapy_interaction_type,
                )
                return None

        return _TherapeuticMetadata(
            therapy_id=therapy_id,
            membership_operator=membership_operator,
            therapies=therapies,
        )

    def _add_eid_document(self, source: dict) -> Document | None:
        """Create document object for CIViC source
        Mutates instance variable ``processed_data.documents``

        :param source: An evidence item's source
        :return: Document for Evidence Item if source type is supported
        """
        source_type = source["source_type"].upper()
        source_id = source["id"]
        if source_type in SourcePrefix.__members__:
            document = Document(
                id=f"civic.source:{source_id}",
                name=source["citation"],
                title=source["title"],
            )

            if source["source_type"] == SourcePrefix.PUBMED:
                document.pmid = int(source["citation_id"])

            if document not in self.processed_data.documents:
                self.processed_data.documents.append(document)
        else:
            _logger.warning(
                "Document, %s, not supported. %s not in SourcePrefix",
                source_id,
                source_type,
            )
            document = None

        return document
