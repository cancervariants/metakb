"""A module for to transform CIViC."""

import logging
from enum import Enum, StrEnum
from pathlib import Path
from types import MappingProxyType

from civicpy import civic as civicpy
from civicpy.exports.civic_gks_record import (
    CivicGksEvidence,
    CivicGksRecordError,
    CivicGksTherapyGroup,
)
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    Relation,
)
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence, SystemUri
from ga4gh.core.models import (
    Coding,
    MappableConcept,
)
from ga4gh.va_spec.base import (
    ConditionSet,
    MembershipOperator,
    Statement,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele, Syntax, Variation
from pydantic.dataclasses import dataclass

from metakb.config import get_config
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.transformers.base import (
    Transformer,
)

_logger = logging.getLogger(__name__)

MP_NAME_PATTERN = (
    r"(?P<gene>\w+)(?:\s+(?P<p_change>\w+))?(?:\s+(?P<c_change>\(?c\..*\)?))?"
)

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


class ConceptType(str, Enum):
    """Define constraints for Concept Types"""

    GENE = "Gene"
    DISEASE = "Disease"
    THERAPY = "Therapy"


class TherapyGroupNamespacePrefix(StrEnum):
    """Define therapy group namespace prefixes"""

    COMBINATION = "civic.ctid"
    SUBSTITUTES = "civic.tsgid"


class ConditionSetNamespacePrefix(StrEnum):
    """Define condition set namespace prefixes"""

    UNION = "civic.condset_union"
    INTERSECTION = "civic.condset_intersect"


NAMESPACE_PREFIX_MAP = MappingProxyType(
    {
        CivicGksTherapyGroup: {
            MembershipOperator.OR: TherapyGroupNamespacePrefix.SUBSTITUTES,
            MembershipOperator.AND: TherapyGroupNamespacePrefix.COMBINATION,
        },
        ConditionSet: {
            MembershipOperator.OR: ConditionSetNamespacePrefix.UNION,
            MembershipOperator.AND: ConditionSetNamespacePrefix.INTERSECTION,
        },
    }
)


@dataclass
class MolecularProfileNameComponents:
    """Define components for molecular profile name"""

    gene: str
    p_change: str | None
    c_change: str | None


class CivicTransformer(Transformer):
    """A class for transforming CIViC to the common data model."""

    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize CIViC Transformer class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested CIViC data
        :param normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transformer")[0]
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = get_config().data_dir / self.name
        self.harvester_path = harvester_path
        self.vicc_normalizers = (
            ViccNormalizers() if normalizers is None else normalizers
        )

    async def transform(self) -> None:
        """Normalize CIViC evidence items and assertions and add annotations"""
        accepted_evidence_items = civicpy.get_all_evidence(include_status=["accepted"])
        statements = []
        for evidence_item in accepted_evidence_items:
            if not isinstance(evidence_item, CivicGksEvidence):
                try:
                    statement = Statement(
                        **CivicGksEvidence(evidence_item).model_dump()
                    )
                except CivicGksRecordError:
                    _logger.warning(
                        "Unable to model civic evidence item %s as a GKS statement",
                        evidence_item,
                    )
                    continue
            else:
                statement = Statement(**evidence_item.model_dump())

            statements += [statement]

            if isinstance(statement.proposition, VariantTherapeuticResponseProposition):
                aggregate_statement = await self._build_aggregated_tr_statement(
                    statement
                )
            elif isinstance(statement.proposition, VariantDiagnosticProposition):
                aggregate_statement = await self._build_aggregated_diag_statement(
                    statement
                )
            elif isinstance(statement.proposition, VariantPrognosticProposition):
                aggregate_statement = await self._build_aggregated_prog_statement(
                    statement
                )
            else:
                raise NotImplementedError

            if aggregate_statement:
                statements += [aggregate_statement]

        # TODO assertions could get weird
        # accepted_assertions = civicpy.get_all_assertions(include_status=["accepted"])
        # for assertion in accepted_assertions:
        #     await self._annotate_assertion(assertion)

    async def _get_annotated_mp(
        self, molecular_profile: civicpy.MolecularProfile
    ) -> CategoricalVariant | ProteinSequenceConsequence:
        """Get annotated info for a CIViC molecular profile

        :param molecular_profile: CIViC molecular profile
        :return: Categorical Variant or Protein Sequence Consequence with additional
            info, such as normalizer info.
            A Protein Sequence Consequence will be returned only if the molecular
            profile is a protein variant and it successfully normalizes, otherwise a
            Categorical Variant will be returned.
        :raises NotImplementedError: For molecular profiles with c. in the name.
            This will be added in issue-225.
        """

        def _get_psc_constraints(allele: Allele) -> list[Constraint]:
            """Get protein sequence consequence constraints

            :param allele: VRS allele
            :return: Protein sequence consequence constraints
            """
            return [
                Constraint(
                    type="DefiningAlleleConstraint",
                    allele=allele,
                    relations=[
                        MappableConcept(
                            primaryCoding=Coding(
                                system=SystemUri.SEQUENCE_ONTOLOGY,
                                code=Relation.LIFTOVER_TO,
                            ),
                        ),
                        MappableConcept(
                            primaryCoding=Coding(
                                system=SystemUri.SEQUENCE_ONTOLOGY,
                                code=Relation.TRANSLATION_OF,
                            ),
                        ),
                    ],
                )
            ]

        mp_id = molecular_profile.id
        constraints = None
        members = None
        normalized_variation = None
        annotated_variation = None
        extensions = molecular_profile.extensions or []

        mp_match = self._parse_mp_name(molecular_profile.name)
        if not mp_match:
            _logger.warning(
                "Unable to parse molecular profile %i name %s",
                mp_id,
                molecular_profile.name,
            )
            mp_name = None
        else:
            is_cdna = bool(mp_match.c_change)
            if is_cdna:
                msg = "cDNA variant not yet supported. This will be added in issue-225"
                _logger.warning(msg)
                raise NotImplementedError(msg)

            mp_name = f"{mp_match.gene} {mp_match.p_change}"

            is_supported_query = self._is_supported_variant_query(mp_name, mp_id)

            if is_supported_query:
                normalized_variation = await self.vicc_normalizers.normalize_variation(
                    mp_name
                )

        if not normalized_variation:
            if is_supported_query:
                _logger.debug(
                    "Variation Normalizer unable to normalize %s using query %s",
                    mp_id,
                    mp_name,
                )
            extensions.append(self._get_vicc_normalizer_failure_ext())
        else:
            # Create VRS Variation object
            variant_concept_mapping = next(
                m
                for m in molecular_profile.mappings
                if m.coding.id.startswith("civic.vid")
            )
            annotated_variation = Variation(
                **normalized_variation.model_dump(exclude_none=True),
                name=variant_concept_mapping.coding.name,
            )

            # Get members
            syntax = Syntax.HGVS_P
            syntax_expressions = []
            if expressions_ext := next(
                (
                    ext
                    for ext in molecular_profile.extensions
                    if ext.name == "expressions"
                ),
                None,
            ):
                expressions = expressions_ext.value
                members = await self._get_mp_members(
                    expressions, syntax_to_exclude=syntax
                )
                syntax_expressions = [
                    expr for expr in expressions if expr.syntax == syntax
                ]

            annotated_variation_root = annotated_variation.root
            if isinstance(annotated_variation_root, Allele):
                if syntax_expressions:
                    annotated_variation_root.expressions = syntax_expressions

                constraints = _get_psc_constraints(annotated_variation_root)

        cat_vrs_cls = (
            CategoricalVariant if not constraints else ProteinSequenceConsequence
        )
        return cat_vrs_cls(
            **molecular_profile.model_dump(
                exclude_none=True, exclude={"members", "constraints", "extensions"}
            ),
            members=members,
            constraints=constraints,
            extensions=extensions or None,
        )

    # async def _get_mp_members(
    #     self, expressions: list[Expression], syntax_to_exclude: Syntax
    # ) -> list[Variation]:
    #     """Get molecular profile members. This is the related variant concepts.
    #
    #     Successfully normalized variants will be stored in ``processed_data.variations``
    #
    #     :param expressions: List of HGVS expressions
    #     :param syntax_to_exclude: Syntax expression to exclude since it's included in
    #         the defining allele constraint
    #     :return: List containing one VRS variation record for each associated HGVS
    #         expression, if variation-normalizer was able to normalize
    #     """
    #     members = []
    #     for expression in expressions:
    #         if expression.syntax == syntax_to_exclude:
    #             continue
    #
    #         hgvs_expr = expression.value
    #         normalized_variation = await self.vicc_normalizers.normalize_variation(
    #             hgvs_expr
    #         )
    #
    #         if normalized_variation:
    #             updated_variation = Variation(
    #                 **normalized_variation.model_dump(
    #                     exclude_none=True, exclude={"extensions", "name", "expressions"}
    #                 ),
    #                 extensions=None,
    #                 name=hgvs_expr,
    #                 expressions=[expression],
    #             )
    #             members.append(updated_variation)
    #             self.processed_data.variations.append(updated_variation.root)
    #     return members

    # @staticmethod
    # def _parse_mp_name(
    #     molecular_profile_name: str,
    # ) -> MolecularProfileNameComponents | None:
    #     """Extract components from molecular profile name
    #
    #     :param molecular_profile_name: CIViC Molecular Profile name
    #     :return: Molecular profile name components if pattern matches, otherwise None
    #     """
    #     match = re.match(MP_NAME_PATTERN, molecular_profile_name)
    #     return MolecularProfileNameComponents(**match.groupdict()) if match else None

    # @staticmethod
    # def _is_supported_variant_query(molecular_profile_name: str, mpid: int) -> bool:
    #     """Determine if a molecular profile name is supported by the
    #     variation-normalizer.
    #
    #     This is used to skip normalization on variants that the variation-normalizer
    #     is known not to support
    #
    #     :param molecular_profile_name: CIViC Molecular Profile name
    #     :param mpid: CIViC molecular profile ID
    #     :return: ``True`` if the molecular_profile_name is supported in the
    #         variation-normalizer. ``False`` otherwise
    #     """
    #     vname_lower = molecular_profile_name.lower()
    #
    #     is_frameshift = vname_lower.endswith("fs")
    #     has_unsupported_chars = any(c in vname_lower for c in ("-", "/"))
    #     unable_to_normalize_names = bool(
    #         set(vname_lower.split()) & UNABLE_TO_NORMALIZE_VAR_NAMES
    #     )
    #
    #     if is_frameshift or has_unsupported_chars or unable_to_normalize_names:
    #         _logger.debug(
    #             "Variation Normalizer does not support %s: %s",
    #             mpid,
    #             molecular_profile_name,
    #         )
    #         return False
    #
    #     return True
