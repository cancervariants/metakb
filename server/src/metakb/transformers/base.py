"""A module for the Transformer base class."""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import Extension, MappableConcept
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
from pydantic import BaseModel

from metakb import DATE_FMT
from metakb.config import get_config
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.identifiers import (
    compute_combo_id,
)
from metakb.transformers.methodology import (
    calculate_star_rating,
)

_logger = logging.getLogger(__name__)


class TransformedData(BaseModel):
    """Define model for transformed data"""

    evidence: list[Statement] = []
    assertions: list[Statement] = []


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
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize Transformer base class.

        :param data_dir: Path to source data directory. If not given, use a subdirectory
            off of the MetaKB data directory as configured in the ``metakb.config`` module.
        :param harvester_path: Path to previously harvested data
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
        self.processed_data = None

    ### Basic/public behavior

    @abstractmethod
    async def transform(self, *args, **kwargs) -> None:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """

    def extract_harvested_data(self) -> _HarvestedData:
        """Get harvested data from file.

        :return: Harvested data
        :raise FileNotFoundError: harvest file not found
        """
        if self.harvester_path is None:
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            default_fname = f"{self.name}_harvester_{today}.json"
            default_path = self.data_dir / "harvester" / default_fname
            if not default_path.exists():
                msg = f"Unable to open harvest file under default filename: {default_path.absolute().as_uri()}"
                raise FileNotFoundError(msg)
            self.harvester_path = default_path
        elif not self.harvester_path.exists():
            msg = f"Unable to open harvester file: {self.harvester_path}"
            raise FileNotFoundError(msg)

        with self.harvester_path.open() as f:
            _harvested_data_child = _HarvestedData.get_subclass_by_prefix(self.name)
            return _harvested_data_child(**json.load(f))

    def create_json(self, cdm_filepath: Path | None = None) -> None:
        """Create a composite JSON for transformed data.

        :param cdm_filepath: Path to the JSON file locatio at which the CDM output will be
            saved. If not provided, will use the default path of
            ``<METAKB_DATA_DIR>/<src_name>/transformers/<src_name>_cdm_YYYYMMDD.json``,
            where ``<METAKB_DATA_DIR>`` is the configurable data root directory.
            See the :ref:`configuration <config-data-directory>` entry in the docs for more information.
        :raise ValueError: if data variable hasn't been populated by transform method yet
        """
        if self.processed_data is None:
            raise ValueError
        if not cdm_filepath:
            transformers_dir = self.data_dir / "transformers"
            transformers_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            cdm_filepath = transformers_dir / f"{self.name}_cdm_{today}.json"

        cdm_filepath.parent.mkdir(parents=True, exist_ok=True)

        with cdm_filepath.open("w+") as f:
            json.dump(self.processed_data.model_dump(exclude_none=True), f, indent=2)

    @staticmethod
    def _set_star_rating_extensions(statement: Statement) -> None:
        """Attach or refresh star-rating extensions for an aggregate statement."""
        if not statement.hasEvidenceLines:
            return

        star_rating = calculate_star_rating(statement.hasEvidenceLines)
        existing_exts = statement.extensions or []
        existing_exts = [
            ext
            for ext in existing_exts
            if ext.name not in {"star_rating", "star_rating_reason"}
        ]
        statement.extensions = [
            *existing_exts,
            Extension(name="star_rating", value=star_rating.star_rating),
            Extension(name="star_rating_reason", value=star_rating.reason.value),
        ]

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
                    members.append(condition)
                elif condition.conceptType == "Disease":
                    normalized_disease = self._normalize_disease(condition)
                    if not normalized_disease:
                        return None
                    members.append(normalized_disease)
                else:
                    raise ValueError
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

    ### statement construction

    async def _get_normalized_proposition(
        self, proposition: PropositionType
    ) -> PropositionType | None:
        """Attempt to construct normalized equivalent of evidence item proposition"""
        normalized_gene = self._normalize_gene(proposition.geneContextQualifier)
        normalized_variation = await self._normalize_variant(proposition.subjectVariant)
        if isinstance(proposition, VariantTherapeuticResponseProposition):
            prop_kwargs = {
                "objectTherapeutic": self._normalize_therapeutic(
                    proposition.objectTherapeutic
                ),
                "conditionQualifier": self._normalize_condition(
                    proposition.conditionQualifier
                ),
            }
        else:
            prop_kwargs = {
                "objectCondition": self._normalize_condition(
                    proposition.objectCondition
                )
            }
        if not all(
            [normalized_gene, normalized_variation, *list(prop_kwargs.values())]
        ):
            return None
        return type(proposition)(
            geneContextQualifier=normalized_gene,
            subjectVariant=normalized_variation,
            predicate=proposition.predicate,
            alleleOriginQualifier=proposition.alleleOriginQualifier,
            **prop_kwargs,
        )
