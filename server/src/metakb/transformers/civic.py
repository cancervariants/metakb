"""A module for to transform CIViC."""

import inspect
import logging
import re
from enum import Enum, StrEnum
from pathlib import Path
from types import MappingProxyType

from civicpy import civic as civicpy
from civicpy.exports.civic_gks_record import (
    CivicGksDisease,
    CivicGksEvidence,
    CivicGksGene,
    CivicGksMolecularProfile,
    CivicGksPhenotype,
    CivicGksTherapy,
    CivicGksTherapyGroup,
    create_gks_record_from_assertion,
)
from ga4gh.cat_vrs.models import CategoricalVariant, Constraint, Relation
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence, SystemUri
from ga4gh.core.models import Coding, MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    MembershipOperator,
    Statement,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele, Expression, Syntax, Variation
from pydantic.dataclasses import dataclass
from tqdm import tqdm

from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import Transformer

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
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        self._concept_norm_method = MappingProxyType(
            {
                ConceptType.DISEASE: self.vicc_normalizers.normalize_disease,
                ConceptType.GENE: self.vicc_normalizers.normalize_gene,
                ConceptType.THERAPY: self.vicc_normalizers.normalize_therapy,
            }
        )

    async def transform(self) -> None:
        """Normalize CIViC evidence items and assertions and add annotations

        Updated records will store results in ``processed_data`` variables.
        """
        accepted_evidence_items = civicpy.get_all_evidence(include_status=["accepted"])
        accepted_assertions = civicpy.get_all_assertions(include_status=["accepted"])
        pbar = tqdm(
            total=len(accepted_evidence_items) + len(accepted_assertions),
        )
        for item in accepted_evidence_items:
            await self._annotate_evidence(item)
            pbar.update(1)
        for item in accepted_assertions:
            await self._annotate_assertion(item)
            pbar.update(1)

        pbar.close()

    async def _annotate_evidence(
        self, evidence_item: civicpy.Evidence | CivicGksEvidence
    ) -> Statement | None:
        """Annotate evidence with additional information, such as normalizer info

        Annotated evidence will be added to ``processed_data.statements_evidence``

        :param evidence_item: CIViC evidence item
        :return: Statement for CIViC evidence item, if able to annotate
        """
        if not isinstance(evidence_item, CivicGksEvidence):
            try:
                gks_evidence_item = CivicGksEvidence(evidence_item)
            except Exception as e:
                _logger.warning(e)
                return None
        else:
            gks_evidence_item = evidence_item

        try:
            updated_proposition = await self._get_updated_proposition(
                gks_evidence_item.proposition
            )
        except NotImplementedError:
            return None

        if not self.processed_data.methods:
            self.processed_data.methods.append(gks_evidence_item.specifiedBy)

        for document in gks_evidence_item.reportedIn or []:
            if document not in self.processed_data.documents:
                self.processed_data.documents.append(document)

        annotated_gks_evidence_item = Statement(
            **gks_evidence_item.model_dump(exclude_none=True, exclude={"proposition"}),
            proposition=updated_proposition,
        )
        self.processed_data.statements_evidence.append(annotated_gks_evidence_item)
        return annotated_gks_evidence_item

    async def _annotate_assertion(self, assertion: civicpy.Assertion) -> None:
        """Annotate assertion with additional information, such as normalizer info

        Annotated assertion will be added to the
        ``processed_data.statements_assertions`` instance variable.

        :param assertion: CIViC assertion
        :return: AAC Study Statement for CIViC assertion, if able to annotate
        """

        async def _resolve_evidence(
            ev: CivicGksEvidence, assertion_id: str
        ) -> Statement | None:
            """Create annotated evidence

            :param ev: CIViC GKS evidence item
            :param assertion_id: ID of assertion that ``ev`` belongs to
            :return: Annotated evidence, if able to resolve
            """
            annotated_evidence = await self._annotate_evidence(ev)
            if not annotated_evidence:
                _logger.warning(
                    "%s is unable to resolve evidence item %s in evidence lines",
                    assertion_id,
                    ev.id,
                )
            return annotated_evidence

        try:
            gks_assertion = create_gks_record_from_assertion(assertion)
        except Exception as e:
            _logger.warning(e)
            return

        try:
            updated_proposition = await self._get_updated_proposition(
                gks_assertion.proposition
            )
        except NotImplementedError:
            return

        for el in gks_assertion.hasEvidenceLines or []:
            el.hasEvidenceItems = [
                annotated_ev
                for ev_item in el.hasEvidenceItems
                if (annotated_ev := await _resolve_evidence(ev_item, gks_assertion.id))
            ]

        annotated_assertion = gks_assertion.__class__.__base__(
            **gks_assertion.model_dump(exclude_none=True, exclude={"proposition"}),
            proposition=updated_proposition,
        )
        self.processed_data.statements_assertions.append(annotated_assertion)

    async def _get_updated_proposition(
        self,
        proposition: VariantDiagnosticProposition
        | VariantPrognosticProposition
        | VariantTherapeuticResponseProposition,
    ) -> (
        VariantDiagnosticProposition
        | VariantPrognosticProposition
        | VariantTherapeuticResponseProposition
        | None
    ):
        """Get updated proposition

        The updated proposition will include additional information, such as normalizer
        info.

        :param proposition: Proposition for a given statement
        :return: Annotated proposition
        """
        updated_molecular_profile = await self._resolve_entity(
            proposition.subjectVariant,
            self.processed_data.categorical_variants,
        )

        if getattr(proposition, "objectCondition", None):
            condition_key = "objectCondition"
        else:
            condition_key = "conditionQualifier"

        condition = getattr(proposition, condition_key)
        if condition and isinstance(condition.root, ConditionSet):
            updated_condition = await self._resolve_condition_set(condition.root)
        else:
            updated_condition = await self._resolve_entity(
                condition.root,
                self.processed_data.conditions,
            )
        updated_condition = Condition(root=updated_condition)

        updated_gene = await self._resolve_entity(
            proposition.geneContextQualifier,
            self.processed_data.genes,
        )

        updated_mappings = {
            condition_key: updated_condition,
            "geneContextQualifier": updated_gene,
            "subjectVariant": updated_molecular_profile,
        }
        therapeutic = getattr(proposition, "objectTherapeutic", None)
        if therapeutic:
            if isinstance(therapeutic.root, TherapyGroup):
                therapy_member_ids = []
                therapies = []
                for therapy_member in therapeutic.root.therapies:
                    therapy_member_ids.append(therapy_member.id)
                    therapies.append(
                        await self._resolve_entity(
                            therapy_member, self.processed_data.therapies
                        )
                    )

                updated_therapeutic = TherapyGroup(
                    **therapeutic.model_dump(exclude_none=True, exclude={"therapies"}),
                    id=self._compute_combo_id(
                        self.name,
                        TherapyGroup,
                        therapeutic.root.membershipOperator,
                        therapy_member_ids,
                    ),
                    therapies=therapies,
                )
                if updated_therapeutic not in self.processed_data.therapy_groups:
                    self.processed_data.therapy_groups.append(updated_therapeutic)

            else:
                updated_therapeutic = await self._resolve_entity(
                    therapeutic, self.processed_data.therapies
                )

            updated_mappings["objectTherapeutic"] = updated_therapeutic

        return proposition.model_copy(update=updated_mappings)

    async def _resolve_entity(
        self,
        entity: CivicGksTherapy
        | CivicGksDisease
        | CivicGksPhenotype
        | CivicGksGene
        | CivicGksMolecularProfile,
        processed_list: list,
    ) -> CategoricalVariant | ProteinSequenceConsequence | MappableConcept:
        """Create annotated entity

        Annotated entity will be added to the ``processed_list``

        :param entity: The entity to annotate with the VICC normalizers. If entity is
            CivicGksPhenotype, will not attempt to annotate
        :param processed_list: List of processed data
        :return: Annotated entity
        """
        if isinstance(entity, CivicGksMolecularProfile):
            annotated_entity = await self._get_annotated_mp(entity)
        elif isinstance(entity, CivicGksDisease | CivicGksGene | CivicGksTherapy):
            annotated_entity = self._get_annotated_mappable_concept(entity)
        else:
            annotated_entity = entity

        if inspect.isawaitable(annotated_entity):
            annotated_entity = await annotated_entity

        processed_list.append(annotated_entity)
        return annotated_entity

    async def _resolve_condition_set(self, condition_set: ConditionSet) -> ConditionSet:
        """Get annotated condition set

        Conditions will be added to ``processed_data.conditions``

        :param condition_set: Condition set
        :return: Annotated condition set
        """
        updated_conditions = []
        condition_ids = []
        for condition in condition_set.conditions:
            if isinstance(condition, CivicGksDisease | CivicGksPhenotype):
                condition_ids.append(condition.id)
                updated_conditions.append(
                    await self._resolve_entity(
                        condition,
                        self.processed_data.conditions,
                    )
                )
            elif isinstance(condition, ConditionSet):
                _condition_set = await self._resolve_condition_set(condition)
                condition_ids.append(_condition_set.id)
                updated_conditions.append(_condition_set)

        condition_set = ConditionSet(
            **condition_set.model_dump(
                exclude_none=True,
                exclude={
                    "conditions",
                },
            ),
            conditions=updated_conditions,
            id=self._compute_combo_id(
                self.name, ConditionSet, condition_set.membershipOperator, condition_ids
            ),
        )
        if condition_set not in self.processed_data.condition_sets:
            self.processed_data.condition_sets.append(condition_set)
        return condition_set

    def _get_annotated_mappable_concept(
        self,
        entity: CivicGksGene | CivicGksDisease | CivicGksTherapy,
    ) -> MappableConcept:
        """Get annotated info for a CIViC entity

        :param entity: CIViC entity (gene, disease, or therapy) that can be represented
            as a mappable concept
        :return: Mappable concept with additional info, such as normalizer info
        """
        concept_type = entity.conceptType
        entity_id = entity.id
        entity_mappings = entity.mappings or []

        queries = [
            mapping.coding.code.root
            if concept_type == ConceptType.DISEASE
            else mapping.coding.id
            for mapping in entity_mappings
        ]
        queries.append(entity.name)

        extensions = entity.extensions or []
        if aliases_ext := next(
            (ext for ext in extensions if ext.name == "aliases"), None
        ):
            queries.extend(aliases_ext.value)

        normalized_id = None
        for query in queries:
            norm_resp, normalized_id = self._concept_norm_method[concept_type](query)
            if normalized_id:
                break

        if not normalized_id:
            _logger.debug(
                "Unable to normalize concept %s using queries: %s", entity_id, queries
            )
            extensions.append(self._get_vicc_normalizer_failure_ext())
            mappings = entity_mappings
        else:
            if concept_type == ConceptType.THERAPY:
                regulatory_approval_extension = (
                    self.vicc_normalizers.get_regulatory_approval_extension(norm_resp)
                )

                if regulatory_approval_extension:
                    extensions.append(regulatory_approval_extension)

            normalizer_mappings = self._get_vicc_normalizer_mappings(
                normalized_id, norm_resp
            )
            mappings = self._merge_mappings(entity_mappings, normalizer_mappings)

        return MappableConcept(
            **entity.model_dump(exclude_none=True, exclude={"extensions", "mappings"}),
            extensions=extensions or None,
            mappings=mappings or None,
        )

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

    async def _get_mp_members(
        self, expressions: list[Expression], syntax_to_exclude: Syntax
    ) -> list[Variation]:
        """Get molecular profile members. This is the related variant concepts.

        Successfully normalized variants will be stored in ``processed_data.variations``

        :param expressions: List of HGVS expressions
        :param syntax_to_exclude: Syntax expression to exclude since it's included in
            the defining allele constraint
        :return: List containing one VRS variation record for each associated HGVS
            expression, if variation-normalizer was able to normalize
        """
        members = []
        for expression in expressions:
            if expression.syntax == syntax_to_exclude:
                continue

            hgvs_expr = expression.value
            normalized_variation = await self.vicc_normalizers.normalize_variation(
                hgvs_expr
            )

            if normalized_variation:
                updated_variation = Variation(
                    **normalized_variation.model_dump(
                        exclude_none=True, exclude={"extensions", "name", "expressions"}
                    ),
                    extensions=None,
                    name=hgvs_expr,
                    expressions=[expression],
                )
                members.append(updated_variation)
                self.processed_data.variations.append(updated_variation.root)
        return members

    @staticmethod
    def _parse_mp_name(
        molecular_profile_name: str,
    ) -> MolecularProfileNameComponents | None:
        """Extract components from molecular profile name

        :param molecular_profile_name: CIViC Molecular Profile name
        :return: Molecular profile name components if pattern matches, otherwise None
        """
        match = re.match(MP_NAME_PATTERN, molecular_profile_name)
        return MolecularProfileNameComponents(**match.groupdict()) if match else None

    @staticmethod
    def _is_supported_variant_query(molecular_profile_name: str, mpid: int) -> bool:
        """Determine if a molecular profile name is supported by the
        variation-normalizer.

        This is used to skip normalization on variants that the variation-normalizer
        is known not to support

        :param molecular_profile_name: CIViC Molecular Profile name
        :param mpid: CIViC molecular profile ID
        :return: ``True`` if the molecular_profile_name is supported in the
            variation-normalizer. ``False`` otherwise
        """
        vname_lower = molecular_profile_name.lower()

        is_frameshift = vname_lower.endswith("fs")
        has_unsupported_chars = any(c in vname_lower for c in ("-", "/"))
        unable_to_normalize_names = bool(
            set(vname_lower.split()) & UNABLE_TO_NORMALIZE_VAR_NAMES
        )

        if is_frameshift or has_unsupported_chars or unable_to_normalize_names:
            _logger.debug(
                "Variation Normalizer does not support %s: %s",
                mpid,
                molecular_profile_name,
            )
            return False

        return True
