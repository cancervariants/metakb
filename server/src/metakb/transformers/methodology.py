"""Provide definitions and basic functions relating to assessments and methods."""

from enum import StrEnum

from ga4gh.core.models import Coding, code
from ga4gh.va_spec.aac_2017.models import Strength as AmpAscoCapStrength
from ga4gh.va_spec.base import EvidenceLine, System
from gene.query import MappableConcept
from pydantic import BaseModel, StrictStr


class EcoLevel(StrEnum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class CivicEvidenceLevel(StrEnum):
    """Define constraints for CIViC evidence levels"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class MoaEvidenceLevel(StrEnum):
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


vicc_concept_vocabs = [
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


def get_aac_strength(
    strength: MappableConcept,
) -> MappableConcept | None:
    if (
        strength.primaryCoding.system
        == "https://civic.readthedocs.io/en/latest/model/evidence/level.html"
    ):
        src_level = CivicEvidenceLevel(strength.primaryCoding.code.root)
    elif strength.primaryCoding.system == "https://moalmanac.org/about":
        src_level = MoaEvidenceLevel(strength.primaryCoding.code.root)
    else:
        raise NotImplementedError
    normalized_level = normalize_evidence_level(src_level)
    if not normalized_level:
        return None
    return MappableConcept(
        primaryCoding=Coding(system=System.AMP_ASCO_CAP, code=code(normalized_level)),
    )


def normalize_evidence_level(
    src_level: CivicEvidenceLevel | MoaEvidenceLevel,
) -> AmpAscoCapStrength | None:
    """Convert source evidence levels into a normalized AMP/ASCO/CAP level

    Use to generate assessment strength values

    :param src_level: evidence level from source statement
    :return: normalized equivalent if available
    """
    level_mapping = {
        CivicEvidenceLevel.A: AmpAscoCapStrength.LEVEL_A,
        CivicEvidenceLevel.B: AmpAscoCapStrength.LEVEL_B,
        CivicEvidenceLevel.C: AmpAscoCapStrength.LEVEL_C,
        CivicEvidenceLevel.D: AmpAscoCapStrength.LEVEL_D,
        CivicEvidenceLevel.E: None,
        MoaEvidenceLevel.CLINICAL_EVIDENCE: AmpAscoCapStrength.LEVEL_C,
        MoaEvidenceLevel.CLINICAL_TRIAL: AmpAscoCapStrength.LEVEL_C,
        MoaEvidenceLevel.FDA_APPROVED: AmpAscoCapStrength.LEVEL_A,
        MoaEvidenceLevel.GUIDELINE: AmpAscoCapStrength.LEVEL_A,
        MoaEvidenceLevel.INFERENTIAL: None,
        MoaEvidenceLevel.PRECLINICAL: AmpAscoCapStrength.LEVEL_D,
    }
    return level_mapping[src_level]


def get_assertion_strength(evidence_lines: list[EvidenceLine]) -> MappableConcept:  # noqa: ARG004
    """Get strength for the assertion supported by provided evidence

    I don't really know what I'm doing here. This should be figured out in #639 and #739,
    hopefully I have the interface right.

    :param evidence: supporting evidence for the assertion
    :return: strength concept
    """
    max_strength = evidence_lines[0].strengthOfEvidenceProvided
    for line in evidence_lines[1:]:
        if (
            line.strengthOfEvidenceProvided.primaryCoding.code.root
            < max_strength.primaryCoding.code.root
        ):
            max_strength = line.strengthOfEvidenceProvided
    return max_strength
