"""A module for the Transformer base class."""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
    iriReference,
)
from ga4gh.va_spec.aac_2017 import Classification as AacClassification
from ga4gh.va_spec.aac_2017 import Strength as AacStrength
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
from pydantic import BaseModel, StrictStr

from metakb import DATE_FMT
from metakb.config import get_config
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.identifiers import compute_aggr_statement_id, compute_combo_id
from metakb.transformers.methodology import get_aac_strength, get_assertion_strength

logger = logging.getLogger(__name__)

# TODO figure out method, etc for MetaKB assertions
# https://github.com/cancervariants/metakb/issues/739
METAKB_METHOD = Method(
    id="metakb.method:2026",
    name="MetaKB (2026)",
    reportedIn=Document(
        name="Wagnerds et al",
        title="MetaKB v2",
        doi="10.1038/1111-1-1111-111-1111",
        pmid="9999999",
    ),
)


class EcoLevel(str, Enum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class CivicEvidenceLevel(str, Enum):
    """Define constraints for CIViC evidence levels"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class MoaEvidenceLevel(str, Enum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "FDA-Approved"
    GUIDELINE = "Guideline"
    CLINICAL_TRIAL = "Clinical trial"
    CLINICAL_EVIDENCE = "Clinical evidence"
    PRECLINICAL = "Preclinical evidence"
    INFERENTIAL = "Inferential evidence"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: list[StrictStr] = []
    exact_mappings: set[CivicEvidenceLevel | MoaEvidenceLevel | EcoLevel] = set()
    definition: StrictStr


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

    _vicc_concept_vocabs: ClassVar[list[ViccConceptVocab]] = [
        ViccConceptVocab(
            id="vicc:e000000",
            domain="EvidenceStrength",
            term="evidence",
            parents=[],
            exact_mappings={EcoLevel.EVIDENCE},
            definition="A type of information that is used to support statements.",
        ),
        ViccConceptVocab(
            id="vicc:e000001",
            domain="EvidenceStrength",
            term="authoritative evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.A},
            definition="Evidence derived from an authoritative source describing a proven or consensus statement.",
        ),
        ViccConceptVocab(
            id="vicc:e000002",
            domain="EvidenceStrength",
            term="FDA recognized evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.FDA_APPROVED},
            definition="Evidence derived from statements recognized by the US Food and Drug Administration.",
        ),
        ViccConceptVocab(
            id="vicc:e000003",
            domain="EvidenceStrength",
            term="professional guideline evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.GUIDELINE},
            definition="Evidence derived from statements by professional society guidelines",
        ),
        ViccConceptVocab(
            id="vicc:e000004",
            domain="EvidenceStrength",
            term="clinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
            definition="Evidence derived from clinical research studies",
        ),
        ViccConceptVocab(
            id="vicc:e000005",
            domain="EvidenceStrength",
            term="clinical cohort evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.B},
            definition="Evidence derived from the clinical study of a participant cohort",
        ),
        ViccConceptVocab(
            id="vicc:e000006",
            domain="EvidenceStrength",
            term="interventional study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
            definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)",
        ),
        ViccConceptVocab(
            id="vicc:e000007",
            domain="EvidenceStrength",
            term="observational study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
            definition="Evidence derived from observational studies of clinical cohorts",
        ),
        ViccConceptVocab(
            id="vicc:e000008",
            domain="EvidenceStrength",
            term="case study evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.C},
            definition="Evidence derived from clinical study of a single participant",
        ),
        ViccConceptVocab(
            id="vicc:e000009",
            domain="EvidenceStrength",
            term="preclinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
            definition="Evidence derived from the study of model organisms",
        ),
        ViccConceptVocab(
            id="vicc:e000010",
            domain="EvidenceStrength",
            term="inferential evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
            definition="Evidence derived by inference",
        ),
    ]

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
        self.evidence_level_to_vicc_concept_mapping = (
            self._evidence_level_to_vicc_concept_mapping()
        )

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

    @staticmethod
    def _get_assertion_classification(evidence: list[EvidenceLine]) -> MappableConcept:  # noqa: ARG004
        """Get classification for the assertion supported by the provided evidence

        See above re placeholder values

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
            aac_strength = get_aac_strength(statement.strength)
            if not aac_strength:
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=Direction.SUPPORTS,
                    strengthOfEvidenceProvided=aac_strength,
                )
            ]
            statement = VariantDiagnosticStudyStatement(
                proposition=VariantDiagnosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                hasEvidenceLines=evidence,
                strength=get_assertion_strength(evidence),
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
            aac_strength = get_aac_strength(statement.strength)
            if not aac_strength:
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=Direction.SUPPORTS,
                    strengthOfEvidenceProvided=aac_strength,
                )
            ]
            statement = VariantPrognosticStudyStatement(
                proposition=VariantPrognosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                hasEvidenceLines=evidence,
                strength=get_assertion_strength(evidence),
                classification=self._get_assertion_classification(evidence),
            )
            statement.id = compute_aggr_statement_id(statement)
            return statement
        return None

    async def _build_aggregated_tr_statement(
        self, statement: Statement
    ) -> VariantTherapeuticResponseStudyStatement | None:
        """Attempt construction of an aggregate therapeutic reseponse study statement given a source statement

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
            aac_strength = get_aac_strength(statement.strength)
            if not aac_strength:
                return None
            evidence = [
                EvidenceLine(
                    hasEvidenceItems=[statement],
                    directionOfEvidenceProvided=Direction.SUPPORTS,
                    strengthOfEvidenceProvided=aac_strength,
                )
            ]
            aggr_statement = VariantTherapeuticResponseStudyStatement(
                proposition=VariantTherapeuticResponseProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectTherapeutic=normalized_therapeutic,
                    conditionQualifier=normalized_disease,
                    predicate=statement.proposition.predicate,
                    alleleOriginQualifier=prop.alleleOriginQualifier,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                hasEvidenceLines=evidence,
                strength=get_assertion_strength(evidence),
                classification=self._get_assertion_classification(evidence),
            )
            aggr_statement.id = compute_aggr_statement_id(aggr_statement)
            return aggr_statement
        return None

    ### Handle evidence

    def _evidence_level_to_vicc_concept_mapping(
        self,
    ) -> dict[MoaEvidenceLevel | CivicEvidenceLevel, list[ConceptMapping]]:
        """Get mapping of source evidence level to vicc concept vocab

        :return: Dictionary containing mapping from source evidence level (key)
            to corresponding vicc concept vocab (value) represented as a list of
            ConceptMapping
        """
        concept_mappings: dict[str, list[ConceptMapping]] = {}
        for item in self._vicc_concept_vocabs:
            for exact_mapping in item.exact_mappings:
                concept_mappings[exact_mapping] = [
                    ConceptMapping(
                        coding=Coding(
                            system="https://go.osu.edu/evidence-codes",
                            code=code(item.id.split("vicc:")[-1]),
                            name=item.term,
                        ),
                        relation=Relation.EXACT_MATCH,
                    )
                ]
        return concept_mappings
