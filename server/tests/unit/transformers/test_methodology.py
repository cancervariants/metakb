import re

import pytest
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.aac_2017.models import Strength as AmpAscoCapStrength
from ga4gh.va_spec.base import (
    DiagnosticPredicate,
    Direction,
    EvidenceLine,
    Statement,
    VariantDiagnosticProposition,
)
from ga4gh.vrs.models import iriReference

from metakb.transformers.methodology import (
    AAC_STRENGTH_INDEX,
    MoaEvidenceLevel,
    calculate_aggregate_values,
    get_evidence_level_coding,
    merge_assertions,
    src_strength_to_vicc_code,
)


@pytest.fixture
def supporting_line_level_a() -> EvidenceLine:
    strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.FDA_APPROVED)
    )
    stmt = Statement(
        id="stmt:supporting_level_a_moa",
        direction=Direction.SUPPORTS,
        strength=strength,
        proposition=VariantDiagnosticProposition(
            subjectVariant=iriReference("metakb.cv:abcdef"),
            predicate=DiagnosticPredicate.INCLUSIVE,
            objectCondition=iriReference("metakb.disease:abcdef"),
        ),
    )
    return EvidenceLine(
        hasEvidenceItems=[stmt],
        directionOfEvidenceProvided=stmt.direction,
        strengthOfEvidenceProvided=src_strength_to_vicc_code(strength),
    )


@pytest.fixture
def disputing_line_level_a() -> EvidenceLine:
    strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.FDA_APPROVED)
    )
    stmt = Statement(
        id="stmt:disputing_level_a_moa",
        direction=Direction.DISPUTES,
        strength=strength,
        proposition=VariantDiagnosticProposition(
            subjectVariant=iriReference("metakb.cv:abcdef"),
            predicate=DiagnosticPredicate.INCLUSIVE,
            objectCondition=iriReference("metakb.disease:abcdef"),
        ),
    )
    return EvidenceLine(
        hasEvidenceItems=[stmt],
        directionOfEvidenceProvided=stmt.direction,
        strengthOfEvidenceProvided=src_strength_to_vicc_code(strength),
    )


@pytest.fixture
def supporting_line_level_c() -> EvidenceLine:
    strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_EVIDENCE)
    )
    stmt = Statement(
        id="stmt:supporting_level_c_moa",
        direction=Direction.SUPPORTS,
        strength=strength,
        proposition=VariantDiagnosticProposition(
            subjectVariant=iriReference("metakb.cv:abcdef"),
            predicate=DiagnosticPredicate.INCLUSIVE,
            objectCondition=iriReference("metakb.disease:abcdef"),
        ),
    )
    return EvidenceLine(
        hasEvidenceItems=[stmt],
        directionOfEvidenceProvided=stmt.direction,
        strengthOfEvidenceProvided=src_strength_to_vicc_code(strength),
    )


@pytest.fixture
def disputing_line_level_c() -> EvidenceLine:
    strength = MappableConcept(
        primaryCoding=get_evidence_level_coding(MoaEvidenceLevel.CLINICAL_EVIDENCE)
    )
    stmt = Statement(
        id="stmt:disputing_level_c_moa",
        direction=Direction.DISPUTES,
        strength=strength,
        proposition=VariantDiagnosticProposition(
            subjectVariant=iriReference("metakb.cv:abcdef"),
            predicate=DiagnosticPredicate.INCLUSIVE,
            objectCondition=iriReference("metakb.disease:abcdef"),
        ),
    )
    return EvidenceLine(
        hasEvidenceItems=[stmt],
        directionOfEvidenceProvided=stmt.direction,
        strengthOfEvidenceProvided=src_strength_to_vicc_code(strength),
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
