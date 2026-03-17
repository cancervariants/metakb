"""Provide definitions and basic functions relating to assessments and methods

* Define source evidence levels and VICC evidence codes
* Provide functions for converting between different systems of evidence strength
* Provide a function for properly merging evidence into existing assertions

"""

import logging
from collections.abc import Sequence
from enum import StrEnum

from ga4gh.core.models import Coding, Extension, Relation, code
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

_logger = logging.getLogger(__name__)


# --- Global assertion method ---

AMP_ASCO_CAP_METHOD = Method(
    id="amp_asco_cap.method:2017",
    name="AMP/ASCO/CAP Interpretation Guidelines",
    reportedIn=Document(
        title=" Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",
        doi="10.1016/j.jmoldx.2016.10.002 ",
        pmid="27993330",
    ),
)

# --- Evidence levels and coding systems ---


ECO_SYSTEM = "http://purl.obolibrary.org/obo/eco.owl"
CIVIC_SYSTEM = "https://civic.readthedocs.io/en/latest/model/evidence/level.html"
MOA_SYSTEM = "https://moalmanac.org/about"
VICC_EVIDENCE_CODE_SYSTEM = "https://go.osu.edu/evidence-codes"


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


def get_evidence_level_coding(
    evidence_level: EcoLevel
    | CivicEvidenceLevel
    | MoaEvidenceLevel
    | AmpAscoCapStrength,
) -> Coding:
    """Create a GKS Coding object for an evidence level instance

    :param evidence_level: instance of known source evidence level enum
    :return: complete coding (incl level + system)
    """
    match evidence_level:
        case EcoLevel():
            system = ECO_SYSTEM
        case CivicEvidenceLevel():
            system = CIVIC_SYSTEM
        case MoaEvidenceLevel():
            system = MOA_SYSTEM
        case AmpAscoCapStrength():
            system = System.AMP_ASCO_CAP
        case _:
            raise ValueError  # just in case
    return Coding(system=system, code=code(evidence_level.value))


class ViccConceptVocabEntry(BaseModel):
    """Define VICC Concept Vocab model

    We use a custom pydantic class rather than a base mappableconcept to preserve
    richer data (e.g. concept parentage)
    """

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: list[StrictStr] = []
    source_mappings: set[CivicEvidenceLevel | MoaEvidenceLevel | EcoLevel] = set()
    aac_mapping: AmpAscoCapStrength | None = None
    definition: StrictStr


_vicc_concept_vocab = [
    ViccConceptVocabEntry(
        id="vicc:e000000",
        domain="EvidenceStrength",
        term="evidence",
        parents=[],
        source_mappings={EcoLevel.EVIDENCE},
        aac_mapping=AmpAscoCapStrength.LEVEL_A,
        definition="A type of information that is used to support statements.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000001",
        domain="EvidenceStrength",
        term="authoritative evidence",
        parents=["vicc:e000000"],
        source_mappings={CivicEvidenceLevel.A},
        aac_mapping=AmpAscoCapStrength.LEVEL_A,
        definition="Evidence derived from an authoritative source describing a proven or consensus statement.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000002",
        domain="EvidenceStrength",
        term="FDA recognized evidence",
        parents=["vicc:e000001"],
        source_mappings={MoaEvidenceLevel.FDA_APPROVED},
        aac_mapping=AmpAscoCapStrength.LEVEL_A,
        definition="Evidence derived from statements recognized by the US Food and Drug Administration.",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000003",
        domain="EvidenceStrength",
        term="professional guideline evidence",
        parents=["vicc:e000001"],
        source_mappings={MoaEvidenceLevel.GUIDELINE},
        aac_mapping=AmpAscoCapStrength.LEVEL_A,
        definition="Evidence derived from statements by professional society guidelines",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000004",
        domain="EvidenceStrength",
        term="clinical evidence",
        parents=["vicc:e000000"],
        source_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
        aac_mapping=AmpAscoCapStrength.LEVEL_B,
        definition="Evidence derived from clinical research studies",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000005",
        domain="EvidenceStrength",
        term="clinical cohort evidence",
        parents=["vicc:e000004"],
        source_mappings={CivicEvidenceLevel.B},
        aac_mapping=AmpAscoCapStrength.LEVEL_B,
        definition="Evidence derived from the clinical study of a participant cohort",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000006",
        domain="EvidenceStrength",
        term="interventional study evidence",
        parents=["vicc:e000005"],
        source_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
        aac_mapping=AmpAscoCapStrength.LEVEL_C,
        definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000007",
        domain="EvidenceStrength",
        term="observational study evidence",
        parents=["vicc:e000005"],
        source_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
        aac_mapping=AmpAscoCapStrength.LEVEL_C,
        definition="Evidence derived from observational studies of clinical cohorts",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000008",
        domain="EvidenceStrength",
        term="case study evidence",
        parents=["vicc:e000004"],
        source_mappings={CivicEvidenceLevel.C},
        aac_mapping=AmpAscoCapStrength.LEVEL_C,
        definition="Evidence derived from clinical study of a single participant",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000009",
        domain="EvidenceStrength",
        term="preclinical evidence",
        parents=["vicc:e000000"],
        source_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
        aac_mapping=AmpAscoCapStrength.LEVEL_D,
        definition="Evidence derived from the study of model organisms",
    ),
    ViccConceptVocabEntry(
        id="vicc:e000010",
        domain="EvidenceStrength",
        term="inferential evidence",
        parents=["vicc:e000000"],
        source_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
        definition="Evidence derived by inference",
    ),
]

# source evidence level enum instance -> vicc concept vocab entry
vicc_concept_vocab_exact_mapping_index = {
    mapping: entry for entry in _vicc_concept_vocab for mapping in entry.source_mappings
}

# vicc concept ID -> vocab entry
vicc_concept_vocab_index = {v.id: v for v in _vicc_concept_vocab}

# --- Helper functions for converting/normalizing evidence and performing aggregation ---


def get_evidence_code(strength: MappableConcept) -> MappableConcept | None:
    """Convert source strength object into a VICC evidence code concept"""
    if strength.primaryCoding.system == System.AMP_ASCO_CAP:
        # TODO these are pending final signoff for handling civic assertions
        match strength.primaryCoding.code.root:
            case AmpAscoCapStrength.LEVEL_A:
                vicc_vocab_entry = vicc_concept_vocab_index["vicc:e000001"]
            case AmpAscoCapStrength.LEVEL_B:
                vicc_vocab_entry = vicc_concept_vocab_index["vicc:e000005"]
            case AmpAscoCapStrength.LEVEL_C:
                vicc_vocab_entry = vicc_concept_vocab_index["vicc:e000008"]
            case AmpAscoCapStrength.LEVEL_D:
                vicc_vocab_entry = vicc_concept_vocab_index["vicc.e000009"]
            case _:
                raise ValueError
    else:
        if strength.primaryCoding.system == CIVIC_SYSTEM:
            src_level = CivicEvidenceLevel(strength.primaryCoding.code.root)
        elif strength.primaryCoding.system == MOA_SYSTEM:
            src_level = MoaEvidenceLevel(strength.primaryCoding.code.root)
        else:
            _logger.debug(
                "Tried to get A/A/C strength equivalent for unrecognized strength object: %s",
                strength,
            )
            raise NotImplementedError
        vicc_vocab_entry = vicc_concept_vocab_exact_mapping_index[src_level]
    if not vicc_vocab_entry.aac_mapping:
        return None

    return MappableConcept(
        id=vicc_vocab_entry.id,
        name=vicc_vocab_entry.term,
        primaryCoding=Coding(
            system=VICC_EVIDENCE_CODE_SYSTEM,
            code=code(vicc_vocab_entry.id.split("vicc:")[-1]),
        ),
        mappings=[
            ConceptMapping(
                relation=Relation.EXACT_MATCH, coding=get_evidence_level_coding(i)
            )
            for i in vicc_vocab_entry.source_mappings
        ],
        extensions=[
            Extension(
                name="metakb_display_value", value=vicc_vocab_entry.aac_mapping.value
            )
        ],
    )


def get_aac_strength(
    strength: MappableConcept,
) -> MappableConcept | None:
    """Get AMP/ASCO/CAP strength from a VICC evidence code

    :param strength:
    :return: the corresponding AMP/ASCO/CAP strength concept, if available
    :raise ValueError:
    """
    if strength.primaryCoding.system != VICC_EVIDENCE_CODE_SYSTEM or not strength.id:
        raise ValueError
    vocab_entry = vicc_concept_vocab_index[strength.id]
    aac_level = vocab_entry.aac_mapping
    if not aac_level:
        raise ValueError
    return MappableConcept(
        primaryCoding=Coding(system=System.AMP_ASCO_CAP, code=code(aac_level.value))
    )


def calculate_aggregate_values(
    evidence_lines: Sequence[EvidenceLine],
) -> tuple[MappableConcept, Direction]:
    """Calculate aggregate values for the assertion supported by provided evidence

    * Get the highest single strength value in any contained evidence item
    * Take directionality from the highest-strength evidence. In the case of a tie,
      direction is "neutral"

    :param evidence_lines: supporting evidence lines for the assertion. Each line must
        have a ``strengthOfEvidenceProvided`` property which is a MappableConcept for
        a VICC evidence coding.
    :return: aggregated AMP/ASCO/CAP strength mapping, and direction
    """
    if not evidence_lines:
        msg = "evidence_lines must not be empty"
        raise ValueError(msg)

    best_line = evidence_lines[0]
    best_strength = get_aac_strength(best_line.strengthOfEvidenceProvided)
    tied_directions = {best_line.directionOfEvidenceProvided}

    for line in evidence_lines[1:]:
        ev_code = line.strengthOfEvidenceProvided
        strength = get_aac_strength(ev_code)
        direction = line.directionOfEvidenceProvided

        if strength.primaryCoding.code.root < best_strength.primaryCoding.code.root:
            best_line = line
            best_strength = strength
            tied_directions = {direction}
        elif strength.primaryCoding.code.root == best_strength.primaryCoding.code.root:
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
