"""Common data model"""
from enum import Enum
from typing import List, Union, Set

from pydantic import BaseModel, StrictStr


class MethodId(str, Enum):
    """Create method id constants"""

    CIVIC_EID_SOP = "civic.method:2019"
    CIVIC_AID_AMP_ASCO_CAP = "metakb.method:2"
    CIVIC_AID_ACMG = "metakb.method:3"
    MOA_ASSERTION_BIORXIV = "metakb.method:4"


class CivicEvidenceLevel(str, Enum):
    """Define constraints for CIViC evidence levels"""

    A = "civic.evidence_level:A"
    B = "civic.evidence_level:B"
    C = "civic.evidence_level:C"
    D = "civic.evidence_level:D"
    E = "civic.evidence_level:E"


class MoaEvidenceLevel(str, Enum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "moa.evidence_level:fda_approved"
    GUIDELINE = "moa.evidence_level:guideline"
    CLINICAL_TRIAL = "moa.evidence_level:clinical_trial"
    CLINICAL_EVIDENCE = "moa.evidence_level:clinical_evidence"
    PRECLINICAL = "moa.evidence_level:preclinical_evidence"
    INFERENTIAL = "moa.evidence_level:inferential_evidence"


class EcoLevel(str, Enum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: List[StrictStr] = []
    exact_mappings: Set[Union[CivicEvidenceLevel, MoaEvidenceLevel, EcoLevel]] = {}
    definition: StrictStr


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = "PUBMED"
    ASCO = "asco"
