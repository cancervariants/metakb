"""A module for the Transformer base class."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    Statement,
    Therapeutic,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)

from metakb.normalizers import ViccNormalizers
from metakb.schemas.data import TransformedData
from metakb.source_data import SourceDataStore
from metakb.transformers.identifiers import (
    compute_assertion_id,
    compute_combo_id,
)
from metakb.transformers.methodology import (
    add_evidence_to_assertion,
    initialize_assertion,
)

_logger = logging.getLogger(__name__)


# TypeVar constrained to the specific Proposition subclasses.
# This is used to indicate that a function operates on a single concrete
# proposition type and returns the *same* type, rather than a generic union.
# It preserves the relationship between input and output types for static typing.
PropositionType = TypeVar(
    "PropositionType",
    VariantTherapeuticResponseProposition,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
)


class Transformer(ABC):
    """A base class for transforming harvester data."""

    def __init__(
        self,
        src_data_store: SourceDataStore,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize Transformer base class.

        :param src_data_store: wrapper around source data location
        :param normalizers: normalizer collection instance
        """
        self.src_data_store = src_data_store
        self.vicc_normalizers = (
            ViccNormalizers() if normalizers is None else normalizers
        )

    ### Basic/public behavior

    @abstractmethod
    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform harvested data into GKS statements with MetaKB-required annotations."""

    ### Entity normalization

    @staticmethod
    def _get_mappableconcept_queries(concept: MappableConcept) -> list[str]:
        """Get queries to submit to normalizer for a given entity concept

        Note the assumption that aliases live in an extension named ``"Aliases"``

        :param concept: gene/drug/disease object
        :return: list of relevant queries for normalization
        :raise ValueError: if Aliases extension doesn't contain a list for its value
        """
        queries = []
        if concept.id:
            queries.append(concept.id)
        if concept.name:
            queries.append(concept.name)
        if concept.mappings:
            queries += [str(m.coding.code) for m in concept.mappings]
        if concept.extensions:
            for ext in concept.extensions:
                if ext.name == "Aliases":
                    if isinstance(ext.value, list):
                        queries += ext.value
                    else:
                        raise ValueError
        return queries

    def _normalize_disease(self, disease: MappableConcept) -> MappableConcept | None:
        """Retrieve normalized disease concept

        :param disease: source-derived disease concept
        :return: either a successful normalized object, or ``None`` if unsuccessful
        """
        for query in self._get_mappableconcept_queries(disease):
            result = self.vicc_normalizers.normalize_disease(query)[0]
            # deepcopying creates some redundant work, but avoids non idempotent strangeness
            result = result.model_copy(deep=True)
            if result.disease:
                normalized_disease = result.disease
                normalized_disease.id = normalized_disease.id.replace(":", "_")
                normalized_disease.id = normalized_disease.id.replace(
                    "normalize.disease.", "metakb.disease:"
                )
                normalized_disease.mappings = None
                normalized_disease.extensions = None
                return normalized_disease
        return None

    def _normalize_phenotype(
        self, phenotype: MappableConcept
    ) -> MappableConcept | ConditionSet | None:
        """Retrieve normalized phenotype concept

        By default, this function is just a pass-through; we'd like to do some kind of
        generalized phenotype normalization someday.

        :param phenotype: phenotype concept from source
        :return: normalized equivalent, if available
        """
        return phenotype

    def _resolve_condition_set(
        self, condition_set: ConditionSet
    ) -> ConditionSet | None:
        """Return normalized equivalent of ConditionSet

        :param condition_set: source-derived ConditionSet
        :return: concept set with normalized equivalents of all inputs, or ``None`` if unsuccessful
        :raise ValueError: if unrecognized concept type
        :raise TypeError: if a member isn't a conditionset or mappableconcept
        """
        members: list[MappableConcept | ConditionSet] = []
        for condition in condition_set.conditions:
            if isinstance(condition, MappableConcept):
                if condition.conceptType == "Phenotype":
                    normalized_phenotype = self._normalize_phenotype(condition)
                    if not normalized_phenotype:
                        return None
                    members.append(normalized_phenotype)
                elif condition.conceptType == "Disease":
                    normalized_disease = self._normalize_disease(condition)
                    if not normalized_disease:
                        return None
                    members.append(normalized_disease)
                else:
                    msg = f"ConditionSet contains unexpected type: {{{condition}}}"
                    _logger.error(msg)
                    raise ValueError(msg)
            elif isinstance(condition, ConditionSet):
                normalized_condition_set = self._resolve_condition_set(condition)
                if not normalized_condition_set:
                    return None
                members.append(normalized_condition_set)
            else:
                raise TypeError
        return ConditionSet(
            conditions=members,
            membershipOperator=condition_set.membershipOperator,
            id=compute_combo_id(
                "metakb",
                ConditionSet,
                condition_set.membershipOperator,
                [c.id for c in members],
            ),
        )

    def _normalize_condition(self, condition: Condition) -> Condition | None:
        """Attempt full normalization of source Condition.

        Treat phenotypes as "normalized" and copy them up to the normalized object. In
        the future, we might want to be more careful about this, maybe check for a
        preferred namespace or try to map over to HPO.

        Note that `condition.root` might be a `ConditionSet` of arbitrary depth, so
        the calls to `_resolve_condition_set` can be recursive.

        :param condition: source Condition object
        :return: normalized equivalent, if available
        :raise ValueError: if concept has an unrecognized concept type
        """
        if isinstance(condition.root, ConditionSet):
            normalized_condition_set = self._resolve_condition_set(condition.root)
            if normalized_condition_set:
                return Condition(root=normalized_condition_set)
            return None
        if condition.root.conceptType == "Phenotype":
            return condition
        if condition.root.conceptType == "Disease":
            normalized_disease = self._normalize_disease(condition.root)
            if normalized_disease:
                return Condition(root=normalized_disease)
            return None
        raise ValueError

    def _normalize_gene(self, gene: MappableConcept | None) -> MappableConcept | None:
        """Attempt normalization of a source Gene

        :param gene: source-derived gene object
        :return: normalized equivalent if successful, else ``None``
        """
        # the gene context in a proposition is often None, eg in a fusion
        # we don't know how to model this for now so we'll just skip it
        if gene is None:
            return None
        for query in self._get_mappableconcept_queries(gene):
            result = self.vicc_normalizers.normalize_gene(query)[0]
            # deepcopying creates some redundant work, but avoids non idempotent strangeness
            result = result.model_copy(deep=True)
            if result.gene:
                normalized_gene = result.gene
                normalized_gene.id = normalized_gene.id.replace(":", "_")
                normalized_gene.id = normalized_gene.id.replace(
                    "normalize.gene.", "metakb.gene:"
                )
                normalized_gene.mappings = None
                normalized_gene.extensions = None
                return normalized_gene
        return None

    def _normalize_drug(self, drug: MappableConcept) -> MappableConcept | None:
        """Attempt normalization of a drug

        :param drug: source drug object
        :return: normalized drug, if successful
        """
        for query in self._get_mappableconcept_queries(drug):
            result = self.vicc_normalizers.normalize_therapy(query)[0]
            # deepcopying creates some redundant work, but avoids non idempotent strangeness
            result = result.model_copy(deep=True)
            if result.therapy:
                normalized_drug = result.therapy
                normalized_drug.id = normalized_drug.id.replace(":", "_")
                normalized_drug.id = normalized_drug.id.replace(
                    "normalize.therapy.", "metakb.therapy:"
                )
                normalized_drug.mappings = None
                normalized_drug.extensions = None
                return normalized_drug
        return None

    def _normalize_therapeutic(self, therapeutic: Therapeutic) -> Therapeutic | None:
        """Attempt normalization of a Therapeutic (drug or drug combo)

        :param therapeutic: source entity
        :return: normalized equivalent, if successful
        """
        if isinstance(therapeutic.root, MappableConcept):
            drug_result = self._normalize_drug(therapeutic.root)
            if drug_result:
                return Therapeutic(root=drug_result)
            return None
        normalized_members = [
            self._normalize_drug(drug) for drug in therapeutic.root.therapies
        ]
        if all(normalized_members):
            return Therapeutic(
                root=TherapyGroup(
                    id=compute_combo_id(
                        "metakb",
                        TherapyGroup,
                        therapeutic.root.membershipOperator,
                        [d.id for d in normalized_members],
                    ),
                    therapies=normalized_members,
                    membershipOperator=therapeutic.root.membershipOperator,
                )
            )
        return None

    @abstractmethod
    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        """Attempt normalization of a source variant object.

        It's tricky to build universal normalization techniques that grab the right
        data from each source, so for now, we'll require each source transformer
        to reimplement it. It's plausible that it could be made generic in the future.

        :param variant: incoming source variant object
        :return: either a normalized CatVar, or None
        """

    ### evidence/assertion construction

    def _ensure_conditionset_id(self, condition_set: ConditionSet) -> None:
        """Ensure that a ConditionSet, and everything it contains, has an ID

        Modifies incoming object in-place if necessary. Source transformers should use
        if incoming ConditionSet objects don't already have IDs.

        :param condition_set: incoming condition set that may or may not have an ID
        """
        if condition_set.id:
            _logger.info("Condition set already has an ID: %s", condition_set.id)
            return
        for member in condition_set.conditions:
            if isinstance(member, ConditionSet):
                self._ensure_conditionset_id(member)
        condition_set.id = compute_combo_id(
            self.src_data_store.src_name,
            ConditionSet,
            condition_set.membershipOperator,
            [c.id for c in condition_set.conditions],
        )

    async def _get_normalized_proposition(
        self, proposition: PropositionType
    ) -> PropositionType | None:
        """Attempt to construct normalized equivalent of evidence item proposition.

        :param proposition: original evidence item proposition
        """
        prop_kwargs = {
            "geneContextQualifier": self._normalize_gene(
                proposition.geneContextQualifier
            ),
            "subjectVariant": await self._normalize_variant(proposition.subjectVariant),
        }

        if isinstance(proposition, VariantTherapeuticResponseProposition):
            normalized_therapeutic = self._normalize_therapeutic(
                proposition.objectTherapeutic
            )
            normalized_condition = self._normalize_condition(
                proposition.conditionQualifier
            )
            prop_kwargs["objectTherapeutic"] = normalized_therapeutic
            prop_kwargs["conditionQualifier"] = normalized_condition
        else:
            normalized_condition = self._normalize_condition(
                proposition.objectCondition
            )
            prop_kwargs["objectCondition"] = normalized_condition

        # Collect failures for logging
        failures = []
        for key, value in prop_kwargs.items():
            if not value:
                original = getattr(proposition, key)
                failures.append((key, original))

        if failures:
            _logger.debug(
                "Failed to normalize proposition components: {%s}",
                "}, {".join(f"{k}={v}" for k, v in failures),
            )
            return None

        return type(proposition)(
            predicate=proposition.predicate,
            alleleOriginQualifier=proposition.alleleOriginQualifier,
            **prop_kwargs,
        )

    async def _upsert_assertion_from_evidence(
        self, evidence_item: Statement, assertions_map: dict[str, Statement]
    ) -> None:
        """Create or update an assertion from a single evidence item.

        The transformer workflow's assertions tracker is borrowed and updated in-place.

        If the proposition cannot be normalized, no assertion is created.

        :param evidence_item: source statement to incorporate as evidence
        :param assertions_map: mapping of assertion_id -> Statement, updated in place
        """
        normalized_proposition = await self._get_normalized_proposition(
            evidence_item.proposition
        )
        if not normalized_proposition:
            _logger.debug(
                "Unable to normalize all proposition terms for ev item %s",
                evidence_item.id,
            )
            return
        assertion_id = compute_assertion_id(normalized_proposition)
        if assertion := assertions_map.get(assertion_id):
            assertion = add_evidence_to_assertion(assertion, evidence_item)
        else:
            assertion = initialize_assertion(
                assertion_id, normalized_proposition, evidence_item
            )
        assertions_map[assertion_id] = assertion
