"""A module for the Transformer base class."""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence
from ga4gh.core.models import Coding, MappableConcept, code, iriReference
from ga4gh.va_spec.aac_2017 import Classification as AacClassification
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    Direction,
    Document,
    EvidenceLine,
    Method,
    Statement,
    System,
    Therapeutic,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele
from pydantic import BaseModel

from metakb import DATE_FMT
from metakb.config import get_config
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.identifiers import compute_aggr_statement_id, compute_combo_id
from metakb.transformers.methodology import (
    AMP_ASCO_CAP_METHOD,
    calculate_aggregate_values,
    src_strength_to_vicc_code,
)

_logger = logging.getLogger(__name__)


class StarRatingReason(str, Enum):
    """Explain why an aggregate statement received a star rating."""

    # 1 star
    SINGLE_SUBMISSION = "single submission from a clinical lab or online resource"
    DISCORDANT_EVIDENCE = "multiple dissenting submissions"

    # 2 star
    CONCORDANT_SUBMISSIONS = (
        "submissions from multiple evidence records that are concordant"
    )

    # 3 star
    SC_VCEP_SUBMISSIONS = (
        "submissions from ClinGen Somatic Cancer Variant Curation Expert Panels"
    )

    # 4 star
    AUTHORITATIVE_EVIDENCE = (
        "knowledge from WHO / NCCN / FDA / other regulatory or professional guidelines"
    )


class StarRatingResult(BaseModel):
    """Structured star rating result for an aggregate statement."""

    star_rating: int
    reason: StarRatingReason


class TransformedData(BaseModel):
    """Define model for transformed data"""

    statements: list[Statement] = []
    categorical_variants: list[CategoricalVariant | ProteinSequenceConsequence] = []
    variations: list[Allele] = []
    genes: list[MappableConcept] = []
    therapies: list[MappableConcept] = []
    therapy_groups: list[TherapyGroup] = []
    conditions: list[MappableConcept] = []
    condition_sets: list[ConditionSet] = []
    methods: list[Method] = []
    documents: list[Document | iriReference] = []


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

    # TODO finish in #766

    @staticmethod
    def _get_assertion_classification(evidence: list[EvidenceLine]) -> MappableConcept:  # noqa: ARG004
        """Get classification for the assertion supported by the provided evidence

        TODO this is a placeholder! it is not final!

        :param evidence: supporting evidence for the assertion
        :return: classification concept
        """
        return MappableConcept(
            primaryCoding=Coding(
                system=System.AMP_ASCO_CAP, code=code(AacClassification.TIER_IV)
            )
        )

    async def _create_aggregate_statement(
        self, statement: Statement
    ) -> (
        VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
        | None
    ):
        """Attempt to build higher-order MetaKB assertion that wraps provided statement

        Try normalization of contained entities. If successful, then create a normalized
        statement, and insert the provided source statement into a supporting ``EvidenceLine``.

        :param statement: raw statement from source
        :return: higher-order MetaKB assertion if successful
        :raise ValueError: if unrecognized proposition type
        """
        if isinstance(statement.proposition, VariantTherapeuticResponseProposition):
            return await self._build_aggregated_tr_statement(statement)
        if isinstance(statement.proposition, VariantDiagnosticProposition):
            return await self._build_aggregated_diag_statement(statement)
        if isinstance(statement.proposition, VariantPrognosticProposition):
            return await self._build_aggregated_prog_statement(statement)
        raise ValueError

    @staticmethod
    def calculate_star_rating(
        aggregate_statement: (
            VariantDiagnosticStudyStatement
            | VariantPrognosticStudyStatement
            | VariantTherapeuticResponseStudyStatement
        ),
    ) -> StarRatingResult:
        """Calculate star rating for an aggregate statement.

        The criteria at the time of writing is as follows:
            - 1-star: single submission from a clinical lab or online resource OR multiple, dissenting submissions
            - 2-star: submissions from multiple evidence records that are concordant (CIViC AIDs demonstrate concordance)
            - 3-star: submissions from ClinGen Somatic Cancer Variant Curation Expert Panels (currently only applies to CIViC records)
            - 4-star: knowledge from WHO / NCCN / FDA Pediatric Approvals / other regulatory or professional guidelines

        :param aggregate_statement: The MetaKB assertion
        :return: Structured star rating result
        """
        star_rating = 1
        reason = StarRatingReason.SINGLE_SUBMISSION
        seen_directions: set[Direction] = set()
        evidence_count = 0

        for evidence_line in aggregate_statement.hasEvidenceLines or []:
            for evidence_item in evidence_line.hasEvidenceItems or []:
                if not isinstance(evidence_item, Statement):
                    continue

                evidence_count += 1
                seen_directions.add(evidence_item.direction)

                evidence_id = (evidence_item.id or "").lower()
                evidence_strength = evidence_item.strength
                strength_mappings = (
                    evidence_strength.mappings if evidence_strength else []
                )

                for mapping in strength_mappings or []:
                    mapped_code = mapping.coding.code
                    if getattr(mapped_code, "root", mapped_code) in {
                        "e000001",
                        "e000002",
                        "e000003",
                    }:
                        # any authoritative, professional guideline, or FDA-approved therapy evidence automatically makes the assertion 4 stars
                        return StarRatingResult(
                            star_rating=4,
                            reason=StarRatingReason.AUTHORITATIVE_EVIDENCE,
                        )

                if "civic.aid:" in evidence_id:
                    # TODO: check if assertion is approved by a SC-VCEP organization, if so, return 3 stars

                    # CIViC assertions are at least 2 stars by default
                    star_rating = 2
                    reason = StarRatingReason.CONCORDANT_SUBMISSIONS

        # if multiple dissenting directions, downgrade to 1 star
        if len(seen_directions) > 1:
            return StarRatingResult(
                star_rating=1,
                reason=StarRatingReason.DISCORDANT_EVIDENCE,
            )

        # if multiple submissions that are concordant, return 2 stars
        if evidence_count > 1:
            return StarRatingResult(
                star_rating=2,
                reason=StarRatingReason.CONCORDANT_SUBMISSIONS,
            )

        return StarRatingResult(star_rating=star_rating, reason=reason)

    async def _build_aggregated_diag_statement(
        self, statement: Statement
    ) -> VariantDiagnosticStudyStatement | None:
        """Attempt construction of an aggregate diagnostic study statement given a source statement

        :param statement: diagnostic statement
        :return: aggregate statement if all terms normalize
        """
        prop: VariantDiagnosticProposition = statement.proposition
        normalized_disease = self._normalize_condition(prop.objectCondition)
        normalized_gene = self._normalize_gene(prop.geneContextQualifier)
        normalized_variant = await self._normalize_variant(prop.subjectVariant)
        if all([normalized_disease, normalized_gene, normalized_variant]):
            vicc_ev_code = src_strength_to_vicc_code(statement.strength)
            if not vicc_ev_code:
                _logger.debug(
                    "Source evidence strength (%s) is too low or unsupported for statement ID %s",
                    statement.strength,
                    statement.id,
                )
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=statement.direction,
                    strengthOfEvidenceProvided=vicc_ev_code,
                )
            ]
            strength, direction = calculate_aggregate_values(evidence)
            statement = VariantDiagnosticStudyStatement(
                proposition=VariantDiagnosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=direction,
                specifiedBy=AMP_ASCO_CAP_METHOD,
                hasEvidenceLines=evidence,
                strength=strength,
                classification=self._get_assertion_classification(evidence),
            )
            statement.id = compute_aggr_statement_id(statement)
            return statement
        return None

    async def _build_aggregated_prog_statement(
        self, statement: Statement
    ) -> VariantPrognosticStudyStatement | None:
        """Attempt construction of an aggregate prognostic study statement given a source statement

        :param statement: prognostic statement
        :return: aggregate statement if all terms normalize
        """
        prop: VariantPrognosticProposition = statement.proposition
        normalized_disease = self._normalize_condition(prop.objectCondition)
        normalized_gene = self._normalize_gene(prop.geneContextQualifier)
        normalized_variant = await self._normalize_variant(prop.subjectVariant)
        if all((normalized_disease, normalized_gene, normalized_variant)):
            vicc_ev_code = src_strength_to_vicc_code(statement.strength)
            if not vicc_ev_code:
                _logger.debug(
                    "Source evidence strength (%s) is too low or unsupported for statement ID %s",
                    statement.strength,
                    statement.id,
                )
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=Direction.SUPPORTS,
                    strengthOfEvidenceProvided=vicc_ev_code,
                )
            ]
            strength, direction = calculate_aggregate_values(evidence)
            statement = VariantPrognosticStudyStatement(
                proposition=VariantPrognosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=direction,
                specifiedBy=AMP_ASCO_CAP_METHOD,
                hasEvidenceLines=evidence,
                strength=strength,
                classification=self._get_assertion_classification(evidence),
            )
            statement.id = compute_aggr_statement_id(statement)
            return statement
        return None

    async def _build_aggregated_tr_statement(
        self, statement: Statement
    ) -> VariantTherapeuticResponseStudyStatement | None:
        """Attempt construction of an aggregate therapeutic response study statement given a source statement

        :param statement: source TR assertion
        :return: aggregate statement if all terms normalize
        """
        prop: VariantTherapeuticResponseProposition = statement.proposition
        normalized_disease = self._normalize_condition(prop.conditionQualifier)
        normalized_gene = self._normalize_gene(prop.geneContextQualifier)
        normalized_variant = await self._normalize_variant(prop.subjectVariant)
        normalized_therapeutic = self._normalize_therapeutic(prop.objectTherapeutic)
        if all(
            (
                normalized_disease,
                normalized_gene,
                normalized_variant,
                normalized_therapeutic,
            )
        ):
            vicc_ev_code = src_strength_to_vicc_code(statement.strength)
            if not vicc_ev_code:
                _logger.debug(
                    "Source evidence strength (%s) is too low or unsupported for statement ID %s",
                    statement.strength,
                    statement.id,
                )
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=Direction.SUPPORTS,
                    strengthOfEvidenceProvided=vicc_ev_code,
                )
            ]
            strength, direction = calculate_aggregate_values(evidence)
            aggr_statement = VariantTherapeuticResponseStudyStatement(
                proposition=VariantTherapeuticResponseProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectTherapeutic=normalized_therapeutic,
                    conditionQualifier=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=direction,
                specifiedBy=AMP_ASCO_CAP_METHOD,
                hasEvidenceLines=evidence,
                strength=strength,
                classification=self._get_assertion_classification(evidence),
            )
            aggr_statement.id = compute_aggr_statement_id(aggr_statement)
            return aggr_statement
        return None
