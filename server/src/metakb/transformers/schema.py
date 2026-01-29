"""Provide type definitions/data structure validation for objects used in transformers."""

from collections.abc import Sequence
from enum import Enum

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence
from ga4gh.core.models import (
    MappableConcept,
)
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    Document,
    Method,
    Statement,
    Therapeutic,
    TherapyGroup,
)
from ga4gh.vrs.models import Allele, CopyNumberChange, CopyNumberCount
from pydantic import BaseModel, Field, StrictStr


class NormalizedGenePair(BaseModel):
    """Contain a source-provided gene and its normalized equivalent if available"""

    normalized_gene: MappableConcept | None
    source_gene: MappableConcept


class NormalizedTherapeuticPair(BaseModel):
    """Contain a source-provided therapeutic and its normalized equivalent if available"""

    normalized_therapeutic: Therapeutic | None
    source_therapeutic: Therapeutic


class NormalizedConditionPair(BaseModel):
    """Contain a source-provided condition and its normalized equivalent if available"""

    normalized_condition: Condition | None
    source_condition: Condition


class NormalizedVariationPair(BaseModel):
    """Contain a source-provided variation and its normalized equivalent if available"""

    normalized_variation: CategoricalVariant | None
    source_variation: CategoricalVariant


class NormalizerExtensionName(str, Enum):
    """Define constraints for normalizer extension names"""

    PRIORITY = "vicc_normalizer_priority"  # concept mapping is merged concept ID
    FAILURE = "vicc_normalizer_failure"  # normalizer failed or is not supported


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

    statements_evidence: list[Statement] = Field(
        [], description="Statement objects for evidence records"
    )
    statements_assertions: Sequence[
        VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = Field([], description="Statement objects for assertion records")
    categorical_variants: Sequence[CategoricalVariant | ProteinSequenceConsequence] = []
    variations: Sequence[CopyNumberChange | CopyNumberCount | Allele] = []
    genes: Sequence[MappableConcept] = []
    therapies: Sequence[MappableConcept] = []
    therapy_groups: Sequence[TherapyGroup] = []
    conditions: Sequence[MappableConcept] = []
    condition_sets: Sequence[ConditionSet] = []
    methods: Sequence[Method] = []
    documents: Sequence[Document] = []
