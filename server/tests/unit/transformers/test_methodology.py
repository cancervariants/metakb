import re

import pytest
from ga4gh.core.models import Coding, ConceptMapping, Extension, MappableConcept, code
from ga4gh.core.models import Relation as CoreRelation
from ga4gh.va_spec.aac_2017.models import Strength as AmpAscoCapStrength
from ga4gh.va_spec.base import (
    DiagnosticPredicate,
    Direction,
    EvidenceLine,
    Statement,
    System,
    VariantDiagnosticProposition,
)
from ga4gh.vrs.models import iriReference

from metakb.transformers.methodology import (
    AAC_STRENGTH_INDEX,
    CivicEvidenceLevel,
    MoaEvidenceLevel,
    StarRatingReason,
    _get_vicc_strength_code,
    calculate_aggregate_values,
    calculate_star_rating,
    get_evidence_level_coding,
    merge_assertions,
    src_strength_to_vicc_code,
)


def _make_source_strength(evidence_level: MoaEvidenceLevel) -> MappableConcept:
    return MappableConcept(primaryCoding=get_evidence_level_coding(evidence_level))


def _make_source_evidence_line(
    statement_id: str,
    direction: Direction,
    evidence_level: MoaEvidenceLevel,
) -> EvidenceLine:
    source_strength = _make_source_strength(evidence_level)
    statement = _make_statement(statement_id, direction, source_strength)
    return _make_evidence_line(statement, src_strength_to_vicc_code(source_strength))


@pytest.fixture
def supporting_line_level_a() -> EvidenceLine:
    return _make_source_evidence_line(
        "stmt:supporting_level_a_moa",
        Direction.SUPPORTS,
        MoaEvidenceLevel.FDA_APPROVED,
    )


@pytest.fixture
def disputing_line_level_a() -> EvidenceLine:
    return _make_source_evidence_line(
        "stmt:disputing_level_a_moa",
        Direction.DISPUTES,
        MoaEvidenceLevel.FDA_APPROVED,
    )


@pytest.fixture
def supporting_line_level_c() -> EvidenceLine:
    return _make_source_evidence_line(
        "stmt:supporting_level_c_moa",
        Direction.SUPPORTS,
        MoaEvidenceLevel.CLINICAL_EVIDENCE,
    )


@pytest.fixture
def disputing_line_level_c() -> EvidenceLine:
    return _make_source_evidence_line(
        "stmt:disputing_level_c_moa",
        Direction.DISPUTES,
        MoaEvidenceLevel.CLINICAL_EVIDENCE,
    )


def _make_statement(
    statement_id: str,
    direction: Direction,
    strength: MappableConcept,
) -> Statement:
    return Statement(
        id=statement_id,
        direction=direction,
        strength=strength,
        proposition=VariantDiagnosticProposition(
            subjectVariant=iriReference("metakb.cv:abcdef"),
            predicate=DiagnosticPredicate.INCLUSIVE,
            objectCondition=iriReference("metakb.disease:abcdef"),
        ),
    )


def _make_evidence_line(
    statement: Statement, strength: MappableConcept
) -> EvidenceLine:
    return EvidenceLine(
        hasEvidenceItems=[statement],
        directionOfEvidenceProvided=statement.direction,
        strengthOfEvidenceProvided=strength,
    )


def _make_vicc_strength_with_mapping(mapped_code: str) -> MappableConcept:
    return MappableConcept(
        id=f"vicc:{mapped_code}",
        primaryCoding=Coding(
            system="https://go.osu.edu/evidence-codes",
            code=code(mapped_code),
        ),
        mappings=[
            ConceptMapping(
                relation=CoreRelation.EXACT_MATCH,
                coding=Coding(system=System.AMP_ASCO_CAP, code=code(mapped_code)),
            )
        ],
    )


@pytest.mark.ci_ok
@pytest.mark.parametrize(
    (
        "line_fixtures",
        "expected",
    ),
    [
        (
            ["supporting_line_level_a"],
            (AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_A], Direction.SUPPORTS),
        ),
        (
            ["supporting_line_level_a", "supporting_line_level_c"],
            (AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_A], Direction.SUPPORTS),
        ),
        (
            ["supporting_line_level_c", "disputing_line_level_c"],
            (AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_C], Direction.NEUTRAL),
        ),
    ],
)
def test_calculate_aggregate_values(line_fixtures, expected, request):
    lines = [request.getfixturevalue(name) for name in line_fixtures]
    assert calculate_aggregate_values(lines) == expected


def test_calculate_aggregate_values_empty():
    with pytest.raises(ValueError, match=re.escape("evidence_lines must not be empty")):
        calculate_aggregate_values([])


@pytest.mark.ci_ok
def test_get_vicc_strength_code_converts_source_strength():
    """Test that source-native strength concepts are converted to VICC codes."""
    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.A)
    )
    assert _get_vicc_strength_code(source_strength) == "e000001"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.FDA_APPROVED)
    )
    assert _get_vicc_strength_code(source_strength) == "e000002"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.GUIDELINE)
    )
    assert _get_vicc_strength_code(source_strength) == "e000003"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.B)
    )
    assert _get_vicc_strength_code(source_strength) == "e000005"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_TRIAL)
    )
    assert _get_vicc_strength_code(source_strength) == "e000006"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_EVIDENCE)
    )
    assert _get_vicc_strength_code(source_strength) == "e000007"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.C)
    )
    assert _get_vicc_strength_code(source_strength) == "e000008"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.PRECLINICAL)
    )
    assert _get_vicc_strength_code(source_strength) == "e000009"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.D)
    )
    assert _get_vicc_strength_code(source_strength) == "e000009"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.E)
    )
    assert _get_vicc_strength_code(source_strength) == "e000010"

    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.INFERENTIAL)
    )
    assert _get_vicc_strength_code(source_strength) == "e000010"


@pytest.mark.ci_ok
@pytest.mark.parametrize(
    ("lines", "expected_rating", "expected_reason"),
    [
        (
            ["supporting_line_level_c"],
            1,
            StarRatingReason.SINGLE_SUBMISSION,
        ),
        (
            ["supporting_line_level_c", "supporting_line_level_c"],
            2,
            StarRatingReason.CONCORDANT_SUBMISSIONS,
        ),
        (
            ["supporting_line_level_c", "disputing_line_level_c"],
            1,
            StarRatingReason.DISCORDANT_EVIDENCE,
        ),
    ],
)
def test_calculate_star_rating(lines, expected_rating, expected_reason, request):
    evidence_lines = [request.getfixturevalue(name) for name in lines]

    result = calculate_star_rating(evidence_lines)

    assert result.star_rating == expected_rating
    assert result.reason == expected_reason


@pytest.mark.ci_ok
def test_calculate_star_rating_authoritative_evidence():
    """Test that authoritative evidence returns 4 stars"""
    strength = _make_vicc_strength_with_mapping("e000002")
    statement = _make_statement(
        "stmt:authoritative",
        Direction.SUPPORTS,
        strength,
    )
    evidence_line = _make_evidence_line(statement, strength)

    result = calculate_star_rating([evidence_line])

    assert result.star_rating == 4
    assert result.reason == StarRatingReason.AUTHORITATIVE_EVIDENCE


@pytest.mark.ci_ok
def test_calculate_star_rating_authoritative_civic_assertion_returns_four_star():
    """Test that authoritative evidence takes precedence for a CIViC assertion"""
    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.A)
    )
    vicc_strength = src_strength_to_vicc_code(source_strength)
    statement = _make_statement(
        "civic.aid:123",
        Direction.SUPPORTS,
        vicc_strength,
    )
    evidence_line = _make_evidence_line(statement, vicc_strength)

    result = calculate_star_rating([evidence_line])

    assert result.star_rating == 4
    assert result.reason == StarRatingReason.AUTHORITATIVE_EVIDENCE


@pytest.mark.ci_ok
def test_calculate_star_rating_sc_vcep_civic_assertion_returns_three_star():
    """Test that a CIViC assertion with SC-VCEP approval returns 3 stars."""
    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.B)
    )
    vicc_strength = src_strength_to_vicc_code(source_strength)
    statement = _make_statement(
        "civic.aid:123",
        Direction.SUPPORTS,
        vicc_strength,
    )
    statement.extensions = [Extension(name="has_vcep_approval", value=True)]
    evidence_line = _make_evidence_line(statement, vicc_strength)

    result = calculate_star_rating([evidence_line])

    assert result.star_rating == 3
    assert result.reason == StarRatingReason.SC_VCEP_SUBMISSIONS


@pytest.mark.ci_ok
def test_calculate_star_rating_authoritative_civic_assertion_overrides_sc_vcep():
    """Test that authoritative CIViC evidence still takes precedence over SC-VCEP."""
    source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.A)
    )
    vicc_strength = src_strength_to_vicc_code(source_strength)
    statement = _make_statement(
        "civic.aid:123",
        Direction.SUPPORTS,
        vicc_strength,
    )
    statement.extensions = [Extension(name="has_vcep_approval", value=True)]
    evidence_line = _make_evidence_line(statement, vicc_strength)

    result = calculate_star_rating([evidence_line])

    assert result.star_rating == 4
    assert result.reason == StarRatingReason.AUTHORITATIVE_EVIDENCE


@pytest.mark.ci_ok
def test_calculate_star_rating_concordant_evidence():
    """Test that multiple concordant pieces of evidence returns 2 stars (outside of a civic assertion)"""
    moa_source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_EVIDENCE)
    )
    moa_vicc_strength = src_strength_to_vicc_code(moa_source_strength)
    moa_statement = _make_statement(
        "moa.aid:123",
        Direction.SUPPORTS,
        moa_vicc_strength,
    )
    moa_evidence_line = _make_evidence_line(moa_statement, moa_vicc_strength)

    civic_source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.B)
    )
    civic_vicc_strength = src_strength_to_vicc_code(civic_source_strength)
    civic_statement = _make_statement(
        "civic.eid:123",
        Direction.SUPPORTS,
        civic_vicc_strength,
    )
    civic_evidence_line = _make_evidence_line(civic_statement, civic_vicc_strength)

    result = calculate_star_rating([moa_evidence_line, civic_evidence_line])

    assert result.star_rating == 2
    assert result.reason == StarRatingReason.CONCORDANT_SUBMISSIONS


@pytest.mark.ci_ok
def test_calculate_star_rating_discordant_evidence():
    """Test that multiple discordant pieces of evidence returns 1 star"""
    moa_source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_EVIDENCE)
    )
    moa_vicc_strength = src_strength_to_vicc_code(moa_source_strength)
    moa_statement = _make_statement(
        "moa.aid:123",
        Direction.DISPUTES,
        moa_vicc_strength,
    )
    moa_evidence_line = _make_evidence_line(moa_statement, moa_vicc_strength)

    civic_source_strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(CivicEvidenceLevel.B)
    )
    civic_vicc_strength = src_strength_to_vicc_code(civic_source_strength)
    civic_statement = _make_statement(
        "civic.eid:123",
        Direction.SUPPORTS,
        civic_vicc_strength,
    )
    civic_evidence_line = _make_evidence_line(civic_statement, civic_vicc_strength)

    result = calculate_star_rating([moa_evidence_line, civic_evidence_line])

    assert result.star_rating == 1
    assert result.reason == StarRatingReason.DISCORDANT_EVIDENCE


def test_merge_assertions_lines(supporting_line_level_a: EvidenceLine):
    """Test merging assertions where items join existing evidence lines, aggregate values unchanged"""
    existing_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_a.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_a.directionOfEvidenceProvided,
        strength=supporting_line_level_a.strengthOfEvidenceProvided,
        hasEvidenceLines=[supporting_line_level_a],
    )
    line_copy = supporting_line_level_a.model_copy(deep=True)
    new_assertion = Statement(
        id="asdf",
        proposition=line_copy.hasEvidenceItems[0].proposition,
        direction=line_copy.directionOfEvidenceProvided,
        strength=line_copy.strengthOfEvidenceProvided,
        hasEvidenceLines=[line_copy],
    )
    existing_assertion_copy, new_assertion_copy = (
        existing_assertion.model_copy(deep=True),
        new_assertion.model_copy(deep=True),
    )  # preserve input state to check later

    merge_assertions(existing_assertion, new_assertion)
    assert existing_assertion != existing_assertion_copy, "First arg modified in-place"
    assert new_assertion == new_assertion_copy, "Second arg not modified"
    assert len(existing_assertion.hasEvidenceLines[0].hasEvidenceItems) == 2
    assert (
        existing_assertion.hasEvidenceLines[0].hasEvidenceItems[0].id
        == "stmt:supporting_level_a_moa"
    )
    assert (
        existing_assertion.hasEvidenceLines[0].hasEvidenceItems[1].id
        == "stmt:supporting_level_a_moa"
    )


@pytest.mark.ci_ok
def test_merge_assertions_recalc_strength(
    supporting_line_level_c: EvidenceLine, supporting_line_level_a: EvidenceLine
):
    existing_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_c.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_c.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_C],
        hasEvidenceLines=[supporting_line_level_c],
    )
    existing_assertion_copy = existing_assertion.model_copy(deep=True)
    new_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_a.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_a.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_A],
        hasEvidenceLines=[supporting_line_level_a],
    )
    merge_assertions(existing_assertion, new_assertion)

    assert len(existing_assertion.hasEvidenceLines) == 2
    assert existing_assertion.strength != existing_assertion_copy.strength
    assert existing_assertion.strength == new_assertion.strength
    assert existing_assertion.direction == existing_assertion_copy.direction


@pytest.mark.ci_ok
def test_merge_assertions_updates_star_rating_extensions(
    supporting_line_level_c: EvidenceLine, disputing_line_level_c: EvidenceLine
):
    existing_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_c.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_c.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_C],
        extensions=[
            Extension(name="foo", value="bar"),
            Extension(name="star_rating", value=2),
            Extension(name="star_rating_reason", value="stale"),
        ],
        hasEvidenceLines=[supporting_line_level_c],
    )
    new_assertion = Statement(
        id="asdf",
        proposition=disputing_line_level_c.hasEvidenceItems[0].proposition,
        direction=disputing_line_level_c.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_C],
        hasEvidenceLines=[disputing_line_level_c],
    )

    merge_assertions(existing_assertion, new_assertion)

    assert existing_assertion.extensions is not None
    star_extensions = {
        ext.name: ext.value
        for ext in existing_assertion.extensions
        if ext.name in {"star_rating", "star_rating_reason"}
    }
    assert star_extensions == {
        "star_rating": 1,
        "star_rating_reason": StarRatingReason.DISCORDANT_EVIDENCE.value,
    }
    assert len([ext for ext in existing_assertion.extensions if ext.name == "foo"]) == 1
    assert (
        len([ext for ext in existing_assertion.extensions if ext.name == "star_rating"])
        == 1
    )
    assert (
        len(
            [
                ext
                for ext in existing_assertion.extensions
                if ext.name == "star_rating_reason"
            ]
        )
        == 1
    )


@pytest.mark.ci_ok
def test_merge_assertions_recalc_strength_and_direction(
    supporting_line_level_c: EvidenceLine, disputing_line_level_a: EvidenceLine
):
    existing_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_c.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_c.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_C],
        hasEvidenceLines=[supporting_line_level_c],
    )
    existing_assertion_copy = existing_assertion.model_copy(deep=True)
    new_assertion = Statement(
        id="asdf",
        proposition=disputing_line_level_a.hasEvidenceItems[0].proposition,
        direction=disputing_line_level_a.directionOfEvidenceProvided,
        strength=AAC_STRENGTH_INDEX[AmpAscoCapStrength.LEVEL_A],
        hasEvidenceLines=[disputing_line_level_a],
    )
    merge_assertions(existing_assertion, new_assertion)

    assert len(existing_assertion.hasEvidenceLines) == 2
    assert existing_assertion.strength != existing_assertion_copy.strength
    assert existing_assertion.strength == new_assertion.strength
    assert existing_assertion.direction != existing_assertion_copy.direction
    assert existing_assertion.direction == new_assertion.direction


@pytest.mark.ci_ok
def test_merge_assertions_check_id(supporting_line_level_c: EvidenceLine):
    existing_assertion = Statement(
        id="asdf",
        proposition=supporting_line_level_c.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_c.directionOfEvidenceProvided,
        strength=supporting_line_level_c.strengthOfEvidenceProvided,
        hasEvidenceLines=[supporting_line_level_c],
    )
    new_assertion = Statement(
        id="zzzz-a-different-id",
        proposition=supporting_line_level_c.hasEvidenceItems[0].proposition,
        direction=supporting_line_level_c.directionOfEvidenceProvided,
        strength=supporting_line_level_c.strengthOfEvidenceProvided,
        hasEvidenceLines=[supporting_line_level_c],
    )
    with pytest.raises(
        ValueError,
        match=re.escape("Tried to merge assertions of distinct propositions"),
    ):
        merge_assertions(existing_assertion, new_assertion)
