"""Provide definitions and basic functions relating to assessments and methods

* Define source evidence levels and VICC evidence codes
* Provide functions for converting between different systems of evidence strength
* Provide a function for properly merging evidence into existing assertions

"""

import logging
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

from metakb.transformers.identifiers import generate_metakb_evidenceline_id

_logger = logging.getLogger(__name__)


# --- Global assertion method ---

METAKB_METHOD = Method(
    id="metakb.method:1",
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


def _get_vicc_strength(strength: MappableConcept) -> MappableConcept:
    """Return the VICC evidence code root for a strength concept.

    Evidence items usually carry source-native strength codings, while some may already provide
    a VICC-normalized strength. This helper accepts either shape and will return the VICC strength
    if it is already provided or return the converted VICC strength based on the source strength.

    :param strength: source or VICC-normalized strength concept
    :return: VICC evidence code root
    :raise ValueError: if the strength cannot be resolved to a VICC evidence code
    """
    if strength.primaryCoding.system == VICC_EVIDENCE_CODE_SYSTEM:
        return strength

    vicc_strength = src_strength_to_vicc_code(strength)
    if not vicc_strength:
        msg = f"Unable to resolve VICC evidence code for strength: {strength}"
        raise ValueError(msg)
    return vicc_strength


def _initialize_evidence_line(ev_item: Statement) -> EvidenceLine:
    """Create initial evidence line wrapped around new evidence item

    This function MUST define

    * ``id`` -- needed for dropping/recreating nodes in the DB
    * ``strengthOfEvidenceProvided`` (using VICC evidence codes)
    * ``directionOfEvidenceProvided``
    * ``evidenceOutcome`` (using a MetaKB star rating concept)
    * An extension for the star rating reason

    :param ev_item: new evidence item
    :return: complete evidence line containing provided statement
    """
    vicc_strength_code = _get_vicc_strength(ev_item.strength)
    if vicc_strength_code.primaryCoding.code.root in {"e000001", "e000002", "e000003"}:
        # Authoritative, FDA-recognized, and professional-guideline
        # evidence automatically make the assertion 4 stars, regardless of
        # source record type.
        star_rating = StarRating.FOUR_STAR
        reason = StarRatingReason.AUTHORITATIVE_EVIDENCE
    elif ev_item.id.startswith("civic.aid:"):
        # TODO: check if assertion is approved by a SC-VCEP organization,
        # if so, immediately set to 3 stars
        # Otherwise, CIViC assertions are at least 2 stars by default
        star_rating = StarRating.TWO_STAR
        reason = StarRatingReason.CONCORDANT_SUBMISSIONS
    else:
        star_rating = StarRating.ONE_STAR
        reason = StarRatingReason.SINGLE_SUBMISSION

    return EvidenceLine(
        id=generate_metakb_evidenceline_id(),
        directionOfEvidenceProvided=ev_item.direction,
        strengthOfEvidenceProvided=vicc_strength_code,
        evidenceOutcome=MappableConcept(
            primaryCoding=Coding(code=code(str(star_rating)), system="metakb")
        ),
        hasEvidenceItems=[ev_item],
        extensions=[Extension(name="metakb_star_rating_reason", value=reason.value)],
    )


def initialize_assertion(
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
    evidence_line = _initialize_evidence_line(evidence_item)
    return Statement(
        id=assertion_id,
        proposition=proposition,
        direction=evidence_line.directionOfEvidenceProvided,
        strength=evidence_line.strengthOfEvidenceProvided,
        specifiedBy=METAKB_METHOD,
        hasEvidenceLines=[evidence_line],
        extensions=[
            Extension(
                name="metakb_star_rating",
                value=evidence_line.evidenceOutcome.model_dump(exclude_none=True),
            ),
            Extension(
                name="metakb_star_rating_reason",
                value=evidence_line.extensions[0].value,
            ),
        ],
    )


def _update_grouped_low_star_line(ev_line: EvidenceLine) -> None:
    """Update aggregate direction/star rating for a grouped low-star evidence line.

    Rules:
    * If all child evidence lines are supports, grouped line is supports + 2 star
    * If all child evidence lines are disputes, grouped line is disputes + 2 star
    * Otherwise, grouped line is neutral + 1 star
    """
    child_lines = ev_line.hasEvidenceItems
    if len(child_lines) < 2:  # noqa: PLR2004
        raise ValueError

    directions = {child.directionOfEvidenceProvided for child in child_lines}
    if directions == {Direction.SUPPORTS}:
        ev_line.directionOfEvidenceProvided = Direction.SUPPORTS
        ev_line.evidenceOutcome = MappableConcept(
            primaryCoding=Coding(code=code(str(StarRating.TWO_STAR)), system="metakb")
        )
        reason = StarRatingReason.CONCORDANT_SUBMISSIONS
    elif directions == {Direction.DISPUTES}:
        ev_line.directionOfEvidenceProvided = Direction.DISPUTES
        ev_line.evidenceOutcome = MappableConcept(
            primaryCoding=Coding(code=code(str(StarRating.TWO_STAR)), system="metakb")
        )
        reason = StarRatingReason.CONCORDANT_SUBMISSIONS
    else:
        ev_line.directionOfEvidenceProvided = Direction.NEUTRAL
        ev_line.evidenceOutcome = MappableConcept(
            primaryCoding=Coding(code=code(str(StarRating.ONE_STAR)), system="metakb")
        )
        reason = StarRatingReason.DISCORDANT_EVIDENCE

    for ext in ev_line.extensions:
        if ext.name == "metakb_star_rating_reason":
            ext.value = reason.value
            break
    else:
        ev_line.extensions.append(
            Extension(name="metakb_star_rating_reason", value=reason.value)
        )


def _recompute_aggregate_assertion_values(assertion: Statement) -> None:
    """Recompute top-level assertion values from immediate child evidence lines.

    Updates argument in-place.

    Rules:
    * Consider only immediate child evidence lines under the assertion
    * Find the child with the highest star rating
    * Copy that child's direction and strength to the assertion
    * Copy that child's star rating and star rating reason into assertion extensions
    """
    if not assertion.hasEvidenceLines:
        return

    def get_star_rating(ev_line: EvidenceLine) -> StarRating:
        return StarRating(ev_line.evidenceOutcome.primaryCoding.code.root)

    best_line = max(assertion.hasEvidenceLines, key=get_star_rating)

    assertion.direction = best_line.directionOfEvidenceProvided
    assertion.strength = best_line.strengthOfEvidenceProvided

    star_rating_value = best_line.evidenceOutcome.model_dump(exclude_none=True)

    star_rating_reason = next(
        ext.value
        for ext in best_line.extensions
        if ext.name == "metakb_star_rating_reason"
    )

    found_star_rating = False
    found_star_rating_reason = False

    for ext in assertion.extensions:
        if ext.name == "metakb_star_rating":
            ext.value = star_rating_value
            found_star_rating = True
        elif ext.name == "metakb_star_rating_reason":
            ext.value = star_rating_reason
            found_star_rating_reason = True

    if not found_star_rating:
        assertion.extensions.append(
            Extension(name="metakb_star_rating", value=star_rating_value)
        )

    if not found_star_rating_reason:
        assertion.extensions.append(
            Extension(name="metakb_star_rating_reason", value=star_rating_reason)
        )


def _get_evidence_from_assertion(assertion: Statement) -> list[Statement]:
    """Get all evidence item Statements contained under a VA-Spec statement.

    Won't traverse past intermediate evidence (ie wont return items under civic assertions as separate results)

    :param statement: top-level assertion
    :return: evidence item Statements
    """
    results: list[Statement] = []

    def _walk_evidence_line(ev_line: EvidenceLine) -> None:
        for item in getattr(ev_line, "hasEvidenceItems", []) or []:
            if isinstance(item, Statement):
                # stop here — do not recurse into this statement
                results.append(item)
            elif isinstance(item, EvidenceLine):
                _walk_evidence_line(item)

    for ev_line in assertion.hasEvidenceLines:
        _walk_evidence_line(ev_line)
    return results


def merge_assertions(assertion: Statement, new_assertion: Statement) -> Statement:
    """Combine two assertions with the same proposition

    TODO this needs to be changed
    - we need to make sure the DB assertion is the one having stuff added to it

    :param assertion: assertion #1
    :param new_assertion: assertion #2
    :return: assertion #1, now containing all evidence items from #2
    :raise ValueError: if assertion IDs aren't matching
    """
    if assertion.id != new_assertion.id:
        raise ValueError

    assertion_item_ids = {s.id for s in _get_evidence_from_assertion(assertion)}
    new_assertion_items = _get_evidence_from_assertion(new_assertion)

    for item in new_assertion_items:
        # skip redundant evidence
        if item.id not in assertion_item_ids:
            add_evidence_to_assertion(assertion, item)

    _recompute_aggregate_assertion_values(assertion)
    return assertion


def add_evidence_to_assertion(assertion: Statement, new_item: Statement) -> Statement:
    """Fold new evidence item into assertion

    Generate new evidence line(s) + rearrange existing evidence if necessary, and
    update all aggregate values. Currently, there are no protections against addition of
    duplicate ev items.

    Generally, the rules for evidence line structure are

    * 3- and 4-star items are added directly under the assertion
    * If there's only a single 1- or 2-star item, it goes directly under the assertion
    * Once a second 1- or 2-star item is added, it gets moved down into another evidence
      line. All subsequent 1-star or 2-star items are added to that evidence line.

    :param assertion: existing metakb assertion
    :param new_item: incoming source statement that needs to be added
    :return: existing assertion, modified to accommodate new evidence
    """
    item_ev_line = _initialize_evidence_line(new_item)
    item_star_rating = StarRating(item_ev_line.evidenceOutcome.primaryCoding.code.root)
    if item_star_rating in {StarRating.THREE_STAR, StarRating.FOUR_STAR}:
        # definitive -- just add at the top
        assertion.hasEvidenceLines.append(item_ev_line)
    else:
        grouped_existing_low_star = False

        # enumerate  so that we can alter the array in-place if necessary
        for i, ev_line in enumerate(assertion.hasEvidenceLines):
            ev_line_star_rating = StarRating(
                ev_line.evidenceOutcome.primaryCoding.code.root
            )

            # If we already have a grouped low-star line under the assertion,
            # add the new item beneath that existing line and recompute concordance.
            # we determine that it's a "grouped" evidence line if it contains an EvidenceLine
            # in the first slot -- this assumption should be safe
            if ev_line_star_rating in {
                StarRating.ONE_STAR,
                StarRating.TWO_STAR,
            } and isinstance(ev_line.hasEvidenceItems[0], EvidenceLine):
                ev_line.hasEvidenceItems.append(item_ev_line)
                _update_grouped_low_star_line(ev_line)
                grouped_existing_low_star = True
                break

            # If we find a single low-star item directly under the assertion,
            # replace it with a new grouped parent evidence line containing both.
            if ev_line_star_rating == StarRating.ONE_STAR:
                grouped_line = EvidenceLine(
                    id=generate_metakb_evidenceline_id(),
                    directionOfEvidenceProvided=Direction.NEUTRAL,  # temporary
                    strengthOfEvidenceProvided=ev_line.strengthOfEvidenceProvided,
                    evidenceOutcome=MappableConcept(
                        primaryCoding=Coding(
                            code=code(str(StarRating.ONE_STAR)),
                            system="metakb",
                        )
                    ),
                    hasEvidenceItems=[ev_line, item_ev_line],
                    extensions=[
                        Extension(
                            name="metakb_star_rating_reason",
                            value=StarRatingReason.SINGLE_SUBMISSION.value,
                        )
                    ],
                )
                _update_grouped_low_star_line(grouped_line)
                assertion.hasEvidenceLines[i] = grouped_line
                grouped_existing_low_star = True
                break

        if not grouped_existing_low_star:
            # First low-star item goes directly under the assertion.
            assertion.hasEvidenceLines.append(item_ev_line)

    _recompute_aggregate_assertion_values(assertion)
    return assertion
