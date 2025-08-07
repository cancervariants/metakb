"""A module for to transform CIViC."""

import inspect
import logging
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from civicpy import civic as civicpy
from civicpy.exports.civic_gks_record import (
    CivicGksDisease,
    CivicGksEvidence,
    CivicGksGene,
    CivicGksMolecularProfile,
    CivicGksTherapy,
    create_gks_record_from_assertion,
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
    Document,
    Statement,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele, Expression, Syntax, Variation

from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.transformers.base import (
    Transformer,
    _TransformedRecordsCache,
)

_logger = logging.getLogger(__name__)

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


class _CivicTransformedCache(_TransformedRecordsCache):
    """Create model for caching CIViC data"""

    categorical_variants: ClassVar[
        dict[str, CategoricalVariant | ProteinSequenceConsequence]
    ] = {}
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

        self._cache = self._create_cache()
        self._concept_norm_method = MappingProxyType(
            {
                ConceptType.DISEASE: self.vicc_normalizers.normalize_disease,
                ConceptType.GENE: self.vicc_normalizers.normalize_gene,
                ConceptType.THERAPY: self.vicc_normalizers.normalize_therapy,
            }
        )

    async def transform(self) -> None:
        """Normalize CIViC evidence items and assertions and add annotations

        Updated records will store results in ``processed_data`` and ``_cache`` instance
        variables.
        """

        async def _resolve_evidence(
            ev: CivicGksEvidence, assertion_id: str
        ) -> Statement | None:
            """Get annotated evidence from cache or create annotated evidence
            (and add to cache)

            :param ev: CIViC GKS evidence item
            :param assertion_id: ID of assertion that ``ev`` belongs to
            :return: Annotated evidence, if able to resolve
            """
            cached_evidence = self._cache.evidence.get(ev.id)
            if cached_evidence:
                return cached_evidence

            annotated_evidence = await self._annotate_evidence(ev)
            if not annotated_evidence:
                _logger.warning(
                    "%s missing evidence item %s in evidence lines",
                    assertion_id,
                    ev.id,
                )
            return annotated_evidence

        approved_evidence_items = civicpy.get_all_evidence(include_status=["accepted"])
        for evidence_item in approved_evidence_items:
            await self._annotate_evidence(evidence_item)

        approved_assertions = civicpy.get_all_assertions(include_status=["accepted"])
        for a in approved_assertions:
            try:
                gks_assertion = create_gks_record_from_assertion(a)
            except Exception as e:
                _logger.warning(e)
                continue

            updated_proposition = await self._get_updated_proposition(
                gks_assertion.proposition
            )
            if not updated_proposition:
                continue

            for el in gks_assertion.hasEvidenceLines or []:
                el.hasEvidenceItems = [
                    annotated_ev
                    for ev_item in el.hasEvidenceItems
                    if (
                        annotated_ev := await _resolve_evidence(
                            ev_item, gks_assertion.id
                        )
                    )
                ]

            annotated_assertion = gks_assertion.__class__.__base__(
                **gks_assertion.model_dump(exclude_none=True, exclude={"proposition"}),
                proposition=updated_proposition,
            )
            self.processed_data.statements_assertions.append(annotated_assertion)

    def _create_cache(self) -> _CivicTransformedCache:
        """Create cache for transformed records"""
        return _CivicTransformedCache()

    async def _annotate_evidence(
        self, evidence_item: civicpy.Evidence | CivicGksEvidence
    ) -> Statement | None:
        """Annotate evidence with additional information, such as normalizer info

        Annotated evidence will be added to the ``processed_data.statements_evidence``
        and ``_cache.evidence`` instance variables.

        :param evidence_item: CIViC evidence item
        :return: Statement for CIViC evidence item, if able to annotate
        """
        if not isinstance(evidence_item, CivicGksEvidence):
            try:
                gks_evidence_item = CivicGksEvidence(evidence_item)
            except Exception as e:
                _logger.warning(e)
                return None

        updated_proposition = await self._get_updated_proposition(
            gks_evidence_item.proposition
        )
        if not updated_proposition:
            return None

        if not self.processed_data.methods:
            self.processed_data.methods.append(gks_evidence_item.specifiedBy)

        for document in gks_evidence_item.reportedIn or []:
            if (
                isinstance(document, Document)
                and document not in self.processed_data.documents
            ):
                self.processed_data.documents.append(document)

        annotated_gks_evidence_item = Statement(
            **gks_evidence_item.model_dump(exclude_none=True, exclude={"proposition"}),
            proposition=updated_proposition,
        )
        self._cache.evidence[gks_evidence_item.id] = annotated_gks_evidence_item
        self.processed_data.statements_evidence.append(annotated_gks_evidence_item)
        return annotated_gks_evidence_item

    async def _get_updated_proposition(
        self,
        proposition: VariantDiagnosticProposition
        | VariantPrognosticProposition
        | VariantTherapeuticResponseProposition,
    ) -> (
        VariantDiagnosticProposition
        | VariantPrognosticProposition
        | VariantTherapeuticResponseProposition
    ):
        """Get updated proposition

        The updated proposition will include additional information, such as normalizer
        info.

        :param proposition: Proposition for a given statement
        """

        async def _add_therapy(therapy: CivicGksTherapy) -> MappableConcept:
            """Create or get therapy given CIViC therapy.
            First looks in cache for existing therapy, if not found will attempt to
            transform. Will add CIViC therapy ID to ``processed_data.therapies`` and
            ``_cache.therapies``

            :param therapy: CIViC Therapy object
            :return: Therapy represented as mappable concept
            """
            return await self._resolve_entity(
                therapy,
                self._cache.therapies,
                self.processed_data.therapies,
            )

        if getattr(proposition, "objectCondition", None):
            condition_key = "objectCondition"
        else:
            condition_key = "conditionQualifier"

        condition = getattr(proposition, condition_key)
        if condition and isinstance(condition.root, ConditionSet):
            # This will be added in issue-194
            return None

        updated_condition = await self._resolve_entity(
            condition.root,
            self._cache.conditions,
            self.processed_data.conditions,
        )

        updated_gene = await self._resolve_entity(
            proposition.geneContextQualifier,
            self._cache.genes,
            self.processed_data.genes,
        )

        updated_molecular_profile = await self._resolve_entity(
            proposition.subjectVariant,
            self._cache.categorical_variants,
            self.processed_data.categorical_variants,
        )

        updated_mappings = {
            condition_key: updated_condition,
            "geneContextQualifier": updated_gene,
            "subjectVariant": updated_molecular_profile,
        }
        therapeutic = getattr(proposition, "objectTherapeutic", None)
        if therapeutic:
            if isinstance(therapeutic.root, TherapyGroup):
                updated_therapeutic = TherapyGroup(
                    **therapeutic.model_dump(exclude_none=True, exclude={"therapies"}),
                    therapies=[
                        await _add_therapy(therapy_member)
                        for therapy_member in therapeutic.root.therapies
                    ],
                )

            else:
                updated_therapeutic = await _add_therapy(therapeutic.root)

            updated_mappings["objectTherapeutic"] = updated_therapeutic

        return proposition.model_copy(update=updated_mappings)

    async def _resolve_entity(
        self,
        entity: CivicGksTherapy
        | CivicGksDisease
        | CivicGksGene
        | CivicGksMolecularProfile,
        cache: dict,
        processed_list: list,
    ) -> CategoricalVariant | ProteinSequenceConsequence | MappableConcept:
        """Get annotated entity from cache or create annotated entity

        Annotated entity will be added to the ``processed_list`` and ``cache``

        :param entity: The entity to annotate with the VICC normalizers
        :param cache: Concept cache
        :param processed_list: List of processed data
        :return: _description_
        """
        entityt_id = entity.id
        entity_obj = cache.get(entityt_id)
        if entity_obj:
            return entity_obj

        if isinstance(entity, CivicGksMolecularProfile):
            annotated_entity = await self._get_annotated_mp(entity)
        else:
            annotated_entity = self._get_annotated_mappable_concept(entity)

        if inspect.isawaitable(annotated_entity):
            annotated_entity = await annotated_entity

        cache[entityt_id] = annotated_entity
        processed_list.append(annotated_entity)
        return annotated_entity

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
            profile successfully normalizes, otherwise a Categorical Variant will be
            returned.
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
        mp_name = self._get_protein_change(molecular_profile.name)

        constraints = None
        members = None
        normalized_variation = None
        annotated_variation = None
        extensions = molecular_profile.extensions or []

        if self._is_supported_variant_query(mp_name, mp_id):
            normalized_variation = await self.vicc_normalizers.normalize_variation(
                mp_name
            )

        if not normalized_variation:
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
            protein_expressions = []
            if expressions_ext := next(
                (
                    ext
                    for ext in molecular_profile.extensions
                    if ext.name == "expressions"
                ),
                None,
            ):
                expressions = expressions_ext.value
                members = await self._get_mp_members(expressions, incl_protein=False)
                protein_expressions = [
                    expr for expr in expressions if expr.syntax == Syntax.HGVS_P
                ]

            annotated_variation_root = annotated_variation.root
            if isinstance(annotated_variation_root, Allele):
                if protein_expressions:
                    annotated_variation_root.expressions = protein_expressions

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
        self, expressions: list[Expression], incl_protein: bool = False
    ) -> list[Variation]:
        """Get molecular profile members. This is the related variant concepts.

        Successfully normalized variants will be stored in ``processed_data.variations``

        :param expressions: List of HGVS expressions
        :param incl_protein: Whether or not protein expression should be included in
            members. Usually set to ``False`` if it's included in the defining allele
            constraint.
        :return: List containing one VRS variation record for each associated HGVS
            expression, if variation-normalizer was able to normalize
        """
        members = []
        for expression in expressions:
            # Protein variant is stored as defining allele constraint
            if expression.syntax == Syntax.HGVS_P and not incl_protein:
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
    def _get_protein_change(molecular_profile_name: str) -> str:
        """Get molecular profile name from CIViC Molecular Profile record.
        If 'c.' in name, use the cDNA name

        :param molecular_profile_name: CIViC Molecular Profile name
        :return: Molecular Profile name to use for query
        """
        if "c." in molecular_profile_name and "(" in molecular_profile_name:
            return molecular_profile_name.replace("(", "").replace(")", "").split()[-1]

        return molecular_profile_name

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
