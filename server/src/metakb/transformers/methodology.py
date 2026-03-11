"""Provide definitions and basic functions relating to assessments and methods."""

import logging
from collections.abc import Sequence
from enum import StrEnum

from ga4gh.core.models import Coding, Relation, code
from ga4gh.va_spec.aac_2017.models import Strength as AmpAscoCapStrength
from ga4gh.va_spec.base import (
    Direction,
    Document,
    EvidenceLine,
    Method,
    Statement,
    System,
)
from gene.query import ConceptMapping, MappableConcept
from pydantic import BaseModel, StrictStr

_logger = logging.getLogger()


AMP_ASCO_CAP_METHOD = Method(
    id="amp_asco_cap.method:2017",
    name="AMP/ASCO/CAP Interpretation Guidelines",
    reportedIn=Document(
        title=" Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",
        doi="10.1016/j.jmoldx.2016.10.002 ",
        pmid="27993330",
    ),
)


class _EvidenceLevelMixin:
    """Abstract EvidenceLevel enum class

    abc.ABC doesn't play nicely with enums so this doesn't implement any instance guards
    """

    _SYSTEM: str

    def get_system(self) -> str:
        """Get evidence coding system value"""
        return self._SYSTEM

    def get_mapcon(self) -> MappableConcept:
        """Create MappableConcept for evidence strength"""
        return MappableConcept(
            primaryCoding=Coding(
                system=self.get_system(),
                code=code(self.value),
            ),
        )


ECO_SYSTEM = "http://purl.obolibrary.org/obo/eco.owl"


class EcoLevel(_EvidenceLevelMixin, StrEnum):
    """Define constraints for Evidence Ontology levels"""

    _SYSTEM = ECO_SYSTEM

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


CIVIC_SYSTEM = "https://civic.readthedocs.io/en/latest/model/evidence/level.html"


class CivicEvidenceLevel(_EvidenceLevelMixin, StrEnum):
    """Define constraints for CIViC evidence levels"""

    _SYSTEM = CIVIC_SYSTEM

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


MOA_SYSTEM = "https://moalmanac.org/about"


class MoaEvidenceLevel(_EvidenceLevelMixin, StrEnum):
    """Define constraints MOAlmanac evidence levels"""

    _SYSTEM = MOA_SYSTEM

    FDA_APPROVED = "FDA-Approved"
    GUIDELINE = "Guideline"
    CLINICAL_TRIAL = "Clinical trial"
    CLINICAL_EVIDENCE = "Clinical evidence"
    PRECLINICAL = "Preclinical evidence"
    INFERENTIAL = "Inferential evidence"


EVIDENCE_LEVEL_MAPPING = {
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


def normalize_evidence_level(
    src_level: CivicEvidenceLevel | MoaEvidenceLevel,
) -> AmpAscoCapStrength | None:
    """Convert source evidence levels into a normalized AMP/ASCO/CAP level

    Use to generate assessment strength values.

    :param src_level: evidence level from source statement
    :return: normalized equivalent if available
    """
    return EVIDENCE_LEVEL_MAPPING[src_level]


class ViccConceptVocabEntry(BaseModel):
    """Define VICC Concept Vocab model

    We use a custom pydantic class rather than a base mappableconcept to preserve
    richer data (e.g. concept parentage)
    """

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: list[StrictStr] = []
    exact_mappings: set[CivicEvidenceLevel | MoaEvidenceLevel | EcoLevel] = set()
    definition: StrictStr

    def to_mapcon(self) -> MappableConcept:
        """Construct Mappable Concept instance

        :return: simple MappableConcept equivalent
        """
        exact_mappings = [
            ConceptMapping(
                coding=Coding(system=em.get_system(), code=code(em.value)),
                relation=Relation.EXACT_MATCH,
            )
            for em in self.exact_mappings
        ]
        return MappableConcept(
            name=self.term,
            primaryCoding=Coding(
                system="https://go.osu.edu/evidence-codes",
                code=code(self.id.split("vicc:")[-1]),
            ),
            mappings=exact_mappings,
        )


_vicc_concept_vocab = [
    ViccConceptVocabEntry(
        id="vicc:e000000",
        domain="EvidenceStrength",
        term="evidence",
        parents=[],
        exact_mappings={EcoLevel.EVIDENCE},
        definition="A type of information that is used to support statements.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000001",
        domain="EvidenceStrength",
        term="authoritative evidence",
        parents=["vicc:e000000"],
        exact_mappings={CivicEvidenceLevel.A},
        definition="Evidence derived from an authoritative source describing a proven or consensus statement.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000002",
        domain="EvidenceStrength",
        term="FDA recognized evidence",
        parents=["vicc:e000001"],
        exact_mappings={MoaEvidenceLevel.FDA_APPROVED},
        definition="Evidence derived from statements recognized by the US Food and Drug Administration.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000003",
        domain="EvidenceStrength",
        term="professional guideline evidence",
        parents=["vicc:e000001"],
        exact_mappings={MoaEvidenceLevel.GUIDELINE},
        definition="Evidence derived from statements by professional society guidelines",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000004",
        domain="EvidenceStrength",
        term="clinical evidence",
        parents=["vicc:e000000"],
        exact_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
        definition="Evidence derived from clinical research studies",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000005",
        domain="EvidenceStrength",
        term="clinical cohort evidence",
        parents=["vicc:e000004"],
        exact_mappings={CivicEvidenceLevel.B},
        definition="Evidence derived from the clinical study of a participant cohort",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000006",
        domain="EvidenceStrength",
        term="interventional study evidence",
        parents=["vicc:e000005"],
        exact_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
        definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000007",
        domain="EvidenceStrength",
        term="observational study evidence",
        parents=["vicc:e000005"],
        exact_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
        definition="Evidence derived from observational studies of clinical cohorts",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000008",
        domain="EvidenceStrength",
        term="case study evidence",
        parents=["vicc:e000004"],
        exact_mappings={CivicEvidenceLevel.C},
        definition="Evidence derived from clinical study of a single participant",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000009",
        domain="EvidenceStrength",
        term="preclinical evidence",
        parents=["vicc:e000000"],
        exact_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
        definition="Evidence derived from the study of model organisms",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000010",
        domain="EvidenceStrength",
        term="inferential evidence",
        parents=["vicc:e000000"],
        exact_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
        definition="Evidence derived by inference",
    ),
]

# source evidence level enum instance -> vicc concept vocab entry
vicc_concept_vocab_exact_mapping_index = {
    mapping: entry for entry in _vicc_concept_vocab for mapping in entry.exact_mappings
}

# vicc concept ID -> vocab entry
vicc_concept_vocab_index = {v.id: v for v in _vicc_concept_vocab}

# AMP/ASCO/CAP strength level enum values -> Strength MappableConcepts
aac_strength_index = {
    i: MappableConcept(
        primaryCoding=Coding(system=System.AMP_ASCO_CAP, code=code(i.value))
    )
    for i in AmpAscoCapStrength
}


def get_aac_strength(
    strength: MappableConcept,
) -> MappableConcept | None:
    """Get AMP/ASCO/CAP strength from a source-provided strength of evidence value

    :param strength: source strength instance
    :return: the equivalent AMP/ASCO/CAP strength concept, if available
    :raise NotImplementedError: if unrecognized concept system is provided
    """
    if strength.primaryCoding.system == CIVIC_SYSTEM:
        src_level = CivicEvidenceLevel(strength.primaryCoding.code.root)
        aac_strength_level = normalize_evidence_level(src_level)
    elif strength.primaryCoding.system == MOA_SYSTEM:
        src_level = MoaEvidenceLevel(strength.primaryCoding.code.root)
        aac_strength_level = normalize_evidence_level(src_level)
    elif strength.primaryCoding.system == System.AMP_ASCO_CAP:
        aac_strength_level = AmpAscoCapStrength(strength.primaryCoding.code.root)
    else:
        _logger.debug(
            "Tried to get A/A/C strength equivalent for unrecognized strength object: %s",
            strength,
        )
        raise NotImplementedError
    if not aac_strength_level:
        return None
    return aac_strength_index[aac_strength_level]


_AAC_STRENGTH_RANK = {
    AmpAscoCapStrength.LEVEL_A.value: 0,
    AmpAscoCapStrength.LEVEL_B.value: 1,
    AmpAscoCapStrength.LEVEL_C.value: 2,
    AmpAscoCapStrength.LEVEL_D.value: 3,
}


def calculate_aggregate_values(
    evidence_lines: Sequence[EvidenceLine],
) -> tuple[MappableConcept, Direction]:
    """Calculate aggregate values for the assertion supported by provided evidence

    * Get the highest single strength value in any contained evidence item
    * Take directionality from the highest-strength evidence. In the case of a tie,
      direction is "neutral"

    :param evidence_lines: supporting evidence lines for the assertion
    :return: aggregate strength and direction
    """
    if not evidence_lines:
        msg = "evidence_lines must not be empty"
        raise ValueError(msg)

    best_line = evidence_lines[0]
    best_strength = best_line.strengthOfEvidenceProvided
    best_rank = _AAC_STRENGTH_RANK[best_strength.primaryCoding.code.root]
    tied_directions = {best_line.directionOfEvidenceProvided}

    for line in evidence_lines[1:]:
        strength = line.strengthOfEvidenceProvided
        rank = _AAC_STRENGTH_RANK[strength.primaryCoding.code.root]
        direction = line.directionOfEvidenceProvided

        if rank < best_rank:
            best_line = line
            best_strength = strength
            best_rank = rank
            tied_directions = {direction}
        elif rank == best_rank:
            tied_directions.add(direction)

    aggregate_direction = (
        tied_directions.pop() if len(tied_directions) == 1 else Direction.NEUTRAL
    )

    return best_strength, aggregate_direction


def merge_assertions(existing_assertion: Statement, new_assertion: Statement) -> None:
    """Fold evidence lines from a new assertion into ``existing_assertion`` and recalculate aggregate values

    **``existing_assertion`` is modified in place!!!** This is on purpose, to enable
    us to modify previous instances of an assertion that are located in array without
    having to pop the instance out, get the updated version, and add it back in

    This currently recalculates the strength value for the assertion, but it could also
    be a good place to calculate evidence star rating in the future.

    :param existing_assertion: the existing version of the assertion
    :param new_assertion: the newly-generated copy of the assertion
    :raise ValueError: if attempting to merge two assertions with different propositions/IDs
    """
    if existing_assertion.id != new_assertion.id:
        _logger.error(
            "Attempting to merge assertions %s with %s. This should be impossible -- investigate further.",
            existing_assertion.id,
            new_assertion.id,
        )
        msg = "Tried to merge assertions of distinct propositions"
        raise ValueError(msg)

    for line in new_assertion.hasEvidenceLines:
        for existing_line in existing_assertion.hasEvidenceLines:
            if (
                (
                    line.strengthOfEvidenceProvided.primaryCoding
                    == existing_line.strengthOfEvidenceProvided.primaryCoding
                )
                and line.directionOfEvidenceProvided
                == existing_line.directionOfEvidenceProvided
            ):
                existing_line.hasEvidenceItems.extend(line.hasEvidenceItems)
                break
        else:
            existing_assertion.hasEvidenceLines.append(line)

    existing_assertion.strength, existing_assertion.direction = (
        calculate_aggregate_values(existing_assertion.hasEvidenceLines)
    )
