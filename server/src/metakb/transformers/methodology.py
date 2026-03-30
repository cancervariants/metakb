"""Provide definitions and basic functions relating to assessments and methods

* Define source evidence levels and VICC evidence codes
* Provide functions for converting between different systems of evidence strength
* Provide a function for properly merging evidence into existing assertions

"""

import logging
from collections.abc import Sequence
from enum import StrEnum

from ga4gh.core.models import Coding, Extension, Relation, code
from ga4gh.va_spec.aac_2017 import Strength as AmpAscoCapStrength
from ga4gh.va_spec.base import (
    Direction,
    Document,
    EvidenceLine,
    Method,
    Statement,
    System,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from gene.query import ConceptMapping, MappableConcept
from pydantic import BaseModel, StrictStr

_logger = logging.getLogger(__name__)


# --- Global assertion method ---

METAKB_METHOD = Method(
    id="genomicmedlab:metakb",
    name="MetaKB Computational Assertion Protocol",
    reportedIn=Document(
        name="cancervariants/metakb",
        doi="10.5281/zenodo.15675452",
        urls=["https://github.com/cancervariants/metakb"],
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
        aac_mapping=AmpAscoCapStrength.LEVEL_D,
        definition="Evidence derived by inference",
    ),
]

# source evidence level enum instance -> vicc concept vocab entry
VICC_CODE_EXACT_MAPPING_INDEX = {
    mapping: entry for entry in _vicc_concept_vocab for mapping in entry.source_mappings
}

# vicc concept ID -> vocab entry
VICC_CODE_INDEX = {v.id: v for v in _vicc_concept_vocab}


# --- Star rating classes


class StarRating(StrEnum):
    """Constrain values for assertion star rating

    Enum values are defined so that inequality checks are intuitive:

        >>> from metakb.transformers.methodology import StarRating
        >>> StarRating.FOUR_STAR > StarRating.TWO_STAR
        True

    """

    ONE_STAR = "1_star"
    TWO_STAR = "2_star"
    THREE_STAR = "3_star"
    FOUR_STAR = "4_star"


class StarRatingReason(StrEnum):
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

    star_rating: StarRating
    reason: StarRatingReason


# --- Helper functions for converting/normalizing evidence and performing aggregation ---


def src_strength_to_vicc_code(strength: MappableConcept) -> MappableConcept | None:
    """Convert source strength object into a VICC evidence code concept

    :param strength: strength object used in a source statement
    :return: the equivalent VICC code strength object, if available
    :raise ValueError: if input arg has an unknown coding system
    """
    if strength.primaryCoding.system == System.AMP_ASCO_CAP:
        # TODO these are pending final signoff for handling civic assertions
        match strength.primaryCoding.code.root:
            case AmpAscoCapStrength.LEVEL_A:
                vicc_vocab_entry = VICC_CODE_INDEX["vicc:e000001"]
            case AmpAscoCapStrength.LEVEL_B:
                vicc_vocab_entry = VICC_CODE_INDEX["vicc:e000005"]
            case AmpAscoCapStrength.LEVEL_C:
                vicc_vocab_entry = VICC_CODE_INDEX["vicc:e000008"]
            case AmpAscoCapStrength.LEVEL_D:
                vicc_vocab_entry = VICC_CODE_INDEX["vicc.e000009"]
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
            raise ValueError
        vicc_vocab_entry = VICC_CODE_EXACT_MAPPING_INDEX[src_level]
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


def get_vicc_strength_code(strength: MappableConcept) -> str:
    """Return the VICC evidence code root for a strength concept.

    Evidence items usually carry source-native strength codings, while some may already provide
    a VICC-normalized strength. This helper accepts either shape and will return the VICC strength
    if it is already provided or return the converted VICC strength based on the source strength.

    :param strength: source or VICC-normalized strength concept
    :return: VICC evidence code root
    :raise ValueError: if the strength cannot be resolved to a VICC evidence code
    """
    if strength.primaryCoding.system == VICC_EVIDENCE_CODE_SYSTEM:
        return strength.primaryCoding.code.root

    vicc_strength = src_strength_to_vicc_code(strength)
    if not vicc_strength:
        msg = f"Unable to resolve VICC evidence code for strength: {strength}"
        raise ValueError(msg)
    return vicc_strength.primaryCoding.code.root


def calculate_star_rating(
    evidence_lines: Sequence[EvidenceLine],
) -> StarRatingResult:
    """Calculate star rating for an aggregate statement.

    The criteria at the time of writing is as follows:
        - 1-star: single submission from a clinical lab or online resource OR multiple, dissenting submissions
        - 2-star: submissions from multiple evidence records that are concordant (CIViC AIDs demonstrate concordance)
        - 3-star: submissions from ClinGen Somatic Cancer Variant Curation Expert Panels (currently only applies to CIViC records)
        - 4-star: knowledge from WHO / NCCN / FDA Pediatric Approvals / other regulatory or professional guidelines

    :param evidence_lines: supporting evidence lines for the assertion
    :return: Structured star rating result
    """
    star_rating = 1
    reason = StarRatingReason.SINGLE_SUBMISSION
    seen_directions: set[Direction] = set()
    evidence_count = 0

    def _has_true_extension(statement: Statement, name: str) -> bool:
        return any(
            ext.name == name and ext.value is True
            for ext in (statement.extensions or [])
        )

    for evidence_line in evidence_lines:
        for evidence_item in evidence_line.hasEvidenceItems or []:
            if not isinstance(evidence_item, Statement):
                continue

            evidence_count += 1
            seen_directions.add(evidence_item.direction)

            evidence_id = (evidence_item.id or "").lower()
            evidence_strength = evidence_item.strength
            vicc_strength = get_vicc_strength_code(evidence_strength)
            if vicc_strength in [
                "e000001",
                "e000002",
                "e000003",
            ]:
                # Authoritative, FDA-recognized, and professional-guideline
                # evidence automatically make the assertion 4 stars, regardless of
                # source record type.
                return StarRatingResult(
                    star_rating=4,
                    reason=StarRatingReason.AUTHORITATIVE_EVIDENCE,
                )
            if "civic.aid:" in evidence_id:
                if _has_true_extension(evidence_item, "has_vcep_approval"):
                    star_rating = 3
                    reason = StarRatingReason.SC_VCEP_SUBMISSIONS
                else:
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


def calculate_aggregate_values(
    evidence_lines: Sequence[EvidenceLine],
) -> tuple[MappableConcept, Direction]:
    """Calculate aggregate values for the assertion supported by provided evidence

    * Get the highest single strength value in any contained evidence item
    * Take directionality from the highest-strength evidence. In the case of a tie,
      direction is "neutral"

    :param evidence_lines: supporting evidence lines for the assertion. Each line must
        have a ``strengthOfEvidenceProvided`` property which is a MappableConcept for
        a VICC evidence coding. Must be non-empty
    :return: aggregated AMP/ASCO/CAP strength mapping, and direction
    :raise ValueError: if evidence lines array is empty
    """
    if not evidence_lines:
        msg = "evidence_lines must not be empty"
        raise ValueError(msg)

    best_line = evidence_lines[0]
    best_strength = vicc_code_to_aac(best_line.strengthOfEvidenceProvided)
    tied_directions = {best_line.directionOfEvidenceProvided}

    for line in evidence_lines[1:]:
        ev_code = line.strengthOfEvidenceProvided
        strength = vicc_code_to_aac(ev_code)
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

    # Recalculate and update star rating
    star_rating = calculate_star_rating(existing_assertion.hasEvidenceLines)

    new_star_exts = [
        Extension(name="star_rating", value=star_rating.star_rating),
        Extension(name="star_rating_reason", value=star_rating.reason.value),
    ]

    existing_exts = existing_assertion.extensions or []
    existing_exts = [
        ext
        for ext in existing_exts
        if ext.name not in {"star_rating", "star_rating_reason"}
    ]
    existing_assertion.extensions = [*existing_exts, *new_star_exts]


def initialize_evidence_line(ev_item: Statement) -> EvidenceLine:
    """Create initial evidence line wrapped around new evidence item

    :param ev_item: new evidence item
    :return: complete evidence line containing provided statement
    """
    vicc_strength_code = get_vicc_strength_code(ev_item.strength)
    if vicc_strength_code in {"e000001", "e000002", "e000003"}:
        # Authoritative, FDA-recognized, and professional-guideline
        # evidence automatically make the assertion 4 stars, regardless of
        # source record type.
        star_rating = StarRating.FOUR_STAR
    elif ev_item.id.startswith("civic.aid:"):
        # TODO: check if assertion is approved by a SC-VCEP organization,
        # if so, immediately set to 3 stars
        # Otherwise, CIViC assertions are at least 2 stars by default
        star_rating = StarRating.TWO_STAR
    else:
        star_rating = StarRating.ONE_STAR

    return EvidenceLine(
        directionOfEvidenceProvided=ev_item.direction,
        strengthOfEvidenceProvided=None,
        evidenceOutcome=MappableConcept(
            primaryCoding=Coding(code=code(str(star_rating)), system="metakb")
        ),
        hasEvidenceItems=[ev_item],
    )


def add_evidence_to_assertion(assertion: Statement, new_item: Statement) -> None:
    """Fold new item into assertion

    modifies in place

    Todo:

    """
    item_ev_line = initialize_evidence_line(new_item)
    item_star_rating = StarRating(item_ev_line.evidenceOutcome.primaryCoding.code.root)
    is_definitive = item_star_rating in {StarRating.THREE_STAR, StarRating.FOUR_STAR}
    for ev_line in assertion.hasEvidenceLines:
        if (
            is_definitive
            and item_star_rating == ev_line.evidenceOutcome.primaryCoding.code.root
        ):
            pass


def build_new_assertion(
    assertion_id: str,
    proposition: VariantDiagnosticProposition
    | VariantPrognosticProposition
    | VariantTherapeuticResponseProposition,
    evidence_item: Statement,
) -> Statement:
    """Create a new metakb assertion given some previously-computed parameters

    Implementation makes use of some stuff that the existing ingest/transform pipeline
    will have already computed, but that makes it relatively brittle to new changes

    :param assertion_id: expected ID for the assertion ("metakb.assertion:")
    :param proposition: proposition using normalized biomedical entities
    :param evidence_item: evidence item from source
    :return: full metakb assertion containing a single evidence line
    """
    evidence_line = initialize_evidence_line(evidence_item)
    return Statement(
        id=assertion_id,
        proposition=proposition,
        direction=evidence_line.directionOfEvidenceProvided,
        strength=evidence_line.strengthOfEvidenceProvided,
        specifiedBy=METAKB_METHOD,
        hasEvidenceLines=[evidence_line],
    )
