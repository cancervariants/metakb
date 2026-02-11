"""A module for the Transformer base class."""

import datetime
import json
import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from async_lru import alru_cache
from disease.schemas import NormalizationService as NormalizedDisease
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    DefiningAlleleConstraint,
    FeatureContextConstraint,
    Relation,
)
from ga4gh.cat_vrs.recipes import SystemUri
from ga4gh.core.models import Coding, MappableConcept, code
from ga4gh.va_spec.aac_2017 import (
    Classification,
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
from ga4gh.vrs.models import Allele, CopyNumberChange, CopyNumberCount
from gene.schemas import NormalizeService as NormalizedGene
from pydantic import BaseModel, StrictStr
from therapy.schemas import NormalizationService as NormalizedTherapy

from metakb import DATE_FMT
from metakb.config import get_config
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import ViccNormalizers

_logger = logging.getLogger(__name__)


# TODO figure out classification, method, etc
# Just a static value for now -- will need to write a classification calculation method
# and calculate/recalculate on a per-statement basis
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

METAKB_CLASSIFICATION = MappableConcept(
    id="metakb.classification:1",
    name="tmp metakb tr classification",
    primaryCoding=Coding(system=System.AMP_ASCO_CAP, code=code(Classification.TIER_I)),
)


class EcoLevel(str, Enum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class MethodId(str, Enum):
    """Create method id constants"""

    CIVIC_EID_SOP = "civic.method:2019"
    MOA_ASSERTION_BIORXIV = "moa.method:2021"


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

    statements: dict[str, Statement] = {}
    variants: dict[str, CategoricalVariant] = {}
    genes: dict[str, MappableConcept] = {}
    therapeutics: dict[str, MappableConcept] = {}
    conditions: dict[str, MappableConcept] = {}
    methods: dict[str, Method] = {}
    documents: dict[str, Document] = {}


class Transformer(ABC):
    """A base class for transforming harvester data."""

    _methods: ClassVar[list[Method]] = [
        Method(
            id=MethodId.CIVIC_EID_SOP,
            name="CIViC Curation SOP (2019)",
            reportedIn=Document(
                name="Danos et al., 2019, Genome Med.",
                title="Standard operating procedure for curation and clinical interpretation of variants in cancer",
                doi="10.1186/s13073-019-0687-x",
                pmid="31779674",
            ),
            methodType="variant curation standard operating procedure",
        ),
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            name="MOAlmanac (2021)",
            reportedIn=Document(
                name="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
                doi="10.1038/s43018-021-00243-3",
                pmid="35121878",
            ),
        ),
    ]
    methods_mapping: ClassVar[dict[MethodId, Method]] = {m.id: m for m in _methods}
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
        self.processed_data = TransformedData()
        self.evidence_level_to_vicc_concept_mapping = (
            self._evidence_level_to_vicc_concept_mapping()
        )

    @abstractmethod
    async def transform(self, *args, **kwargs) -> None:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """

    def extract_harvested_data(self) -> _HarvestedData:
        """Get harvested data from file.

        :return: Harvested data
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
        """
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

    @lru_cache(1024)  # noqa: B019
    def _send_disease_normalizer_query(self, term: str) -> NormalizedDisease:
        return self.vicc_normalizers.normalize_disease(term)[0]

    def _normalize_disease(self, disease: MappableConcept) -> MappableConcept | None:
        queries = []
        if disease.id:
            queries.append(disease.id)
        if disease.name:
            queries.append(disease.name)
        if disease.mappings:
            queries += [str(m.coding.code) for m in disease.mappings]
        if disease.extensions:
            for ext in disease.extensions:
                if ext.name == "Aliases":
                    queries += ext.value
        for query in queries:
            result = self._send_disease_normalizer_query(query)
            if result.disease:
                normalized_disease = result.disease
                normalized_disease.mappings = None
                normalized_disease.extensions = None
                return normalized_disease
        return None

    def _resolve_condition_set(
        self, condition_set: ConditionSet
    ) -> ConditionSet | None:
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
            conditions=members, membershipOperator=condition_set.membershipOperator
        )

    def _normalize_condition(self, condition: Condition) -> Condition | None:
        """Attempt full normalization of source Condition.

        Treat phenotypes as "normalized" and copy them up to the normalized object.

        :param condition: source Condition object
        :return: normalized equivalent, if available
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

    @lru_cache(1024)  # noqa: B019
    def _send_gene_normalizer_query(self, term: str) -> NormalizedGene:
        return self.vicc_normalizers.normalize_gene(term)[0]

    def _normalize_gene(self, gene: MappableConcept | None) -> MappableConcept | None:
        # the gene context in a proposition is often None, eg in a fusion
        # we don't know how to model this for now so we'll just skip it
        if gene is None:
            return None
        queries = []
        if gene.id:
            queries.append(gene.id)
        if gene.name:
            queries.append(gene.name)
        if gene.mappings:
            queries += [str(m.coding.code) for m in gene.mappings]
        if gene.extensions:
            for ext in gene.extensions:
                if ext.name == "Aliases":
                    queries += ext.value
        for query in queries:
            result = self._send_gene_normalizer_query(query)
            if result.gene:
                normalized_gene = result.gene
                normalized_gene.mappings = None
                normalized_gene.extensions = None
                return normalized_gene
        return None

    @alru_cache(1024)
    async def _send_variant_normalizer_query(
        self, query: str
    ) -> Allele | CopyNumberChange | CopyNumberCount | None:
        return await self.vicc_normalizers.normalize_variation(query)

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        queries = [variant.name]
        result = None
        for query in queries:
            if match := re.match(r"(.*) (Mutation|MUTATION)", query):
                gene_name = match.groups()[0]
                normalized_gene_result = self._send_gene_normalizer_query(gene_name)
                if normalized_gene_result.gene:
                    constraints = [
                        FeatureContextConstraint(
                            featureContext=normalized_gene_result.gene
                        )
                    ]
                    break
            result = await self._send_variant_normalizer_query(query)
            if result and isinstance(result, Allele):
                constraints = [
                    DefiningAlleleConstraint(
                        allele=result,
                        relations=[
                            MappableConcept(
                                primaryCoding=Coding(
                                    system=SystemUri.SEQUENCE_ONTOLOGY,
                                    code=code(Relation.LIFTOVER_TO),
                                ),
                            ),
                            MappableConcept(
                                primaryCoding=Coding(
                                    system=SystemUri.SEQUENCE_ONTOLOGY,
                                    code=code(Relation.TRANSLATION_OF),
                                ),
                            ),
                        ],
                    )
                ]
                break
        else:
            _logger.debug(
                "Failed to normalize variant: %s", variant.model_dump(exclude_none=True)
            )
            return None
        return CategoricalVariant(
            id="idk: some cv id pattern TODO",
            name="idk some pattern TODO",
            constraints=constraints,
        )

    @lru_cache(1024)  # noqa: B019
    def _send_therapy_normalizer_query(self, query: str) -> NormalizedTherapy:
        return self.vicc_normalizers.normalize_therapy(query)[0]

    def _normalize_drug(self, drug: MappableConcept) -> MappableConcept | None:
        queries = []
        if drug.id:
            queries.append(drug.id)
        if drug.name:
            queries.append(drug.name)
        if drug.mappings:
            queries += [str(m.coding.code) for m in drug.mappings]
        if drug.extensions:
            for ext in drug.extensions:
                if ext.name == "Aliases":
                    queries += ext.value
        for query in queries:
            result = self._send_therapy_normalizer_query(query)
            if result.therapy:
                normalized_drug = result.therapy
                normalized_drug.mappings = None
                normalized_drug.extensions = None
                return normalized_drug
        return None

    def _normalize_therapeutic(self, therapeutic: Therapeutic) -> Therapeutic | None:
        if isinstance(therapeutic.root, MappableConcept):
            drug_result = self._normalize_drug(therapeutic.root)
            if drug_result:
                return Therapeutic(root=drug_result)
            return None
        if isinstance(therapeutic.root, TherapyGroup):
            normalized_members = [
                self._normalize_drug(drug) for drug in therapeutic.root.therapies
            ]
            if all(normalized_members):
                return Therapeutic(
                    root=TherapyGroup(
                        id="make up a string TODO",
                        therapies=normalized_members,
                        membershipOperator=therapeutic.root.membershipOperator,
                    )
                )
            return None

        raise NotImplementedError

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
            return VariantDiagnosticStudyStatement(
                id="metakb:id that sums up the proposition parts",
                proposition=VariantDiagnosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                classification=METAKB_CLASSIFICATION,
                hasEvidenceLines=[
                    EvidenceLine(
                        hasEvidenceItems=[statement],
                        directionOfEvidenceProvided=Direction.SUPPORTS,
                    )
                ],
            )
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
            return VariantPrognosticStudyStatement(
                id="metakb:id that sums up the proposition parts",
                proposition=VariantPrognosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=statement.proposition.predicate,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                classification=METAKB_CLASSIFICATION,
                hasEvidenceLines=[
                    EvidenceLine(
                        hasEvidenceItems=[statement],
                        directionOfEvidenceProvided=Direction.SUPPORTS,
                    )
                ],
            )
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
            return VariantTherapeuticResponseStudyStatement(
                id="metakb:id that sums up the proposition parts",
                proposition=VariantTherapeuticResponseProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectTherapeutic=normalized_therapeutic,
                    conditionQualifier=normalized_disease,
                    predicate=statement.proposition.predicate,
                ),
                direction=statement.direction,
                specifiedBy=METAKB_METHOD,
                classification=METAKB_CLASSIFICATION,
                hasEvidenceLines=[
                    EvidenceLine(
                        hasEvidenceItems=[statement],
                        directionOfEvidenceProvided=Direction.SUPPORTS,
                    )
                ],
            )
        return None
