"""Test methods in the Transformer base class, not tied to specific sources"""

import json
from pathlib import Path

import pytest
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    MembershipOperator,
    Therapeutic,
    TherapyGroup,
)

from metakb.transformers.base import Transformer
from metakb.transformers.civic import CivicTransformer


@pytest.fixture(scope="session")
def transformer() -> Transformer:
    return CivicTransformer()


@pytest.fixture(scope="session")
def unnormalized_conditions(test_data_dir: Path) -> dict[str, Condition]:
    with (
        test_data_dir / "transformers" / "base_normalize_conditions_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: Condition(**v) for k, v in data.items()}


@pytest.fixture(scope="session")
def unnormalized_therapeutics(test_data_dir: Path) -> dict[str, Therapeutic]:
    with (
        test_data_dir / "transformers" / "base_normalize_therapeutic_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: Therapeutic(**v) for k, v in data.items()}


def test_normalize_condition(
    transformer: Transformer, unnormalized_conditions: dict[str, Condition]
):
    result = transformer._normalize_condition(unnormalized_conditions["civic.did:8"])
    assert result is not None
    assert isinstance(result.root, MappableConcept)
    assert result.root.id == "normalize.disease.ncit:C2926"

    conditionset = unnormalized_conditions["civic_cs_plexiform_neurofibroma_nonadult"]

    result = transformer._normalize_condition(conditionset)
    assert result is not None
    assert isinstance(result.root, ConditionSet)
    assert result.root.id == "metakb.cs:LQCCZxv68jeT4Ngbaf4_ABKwEHZKoKDB"
    assert result.root.membershipOperator == MembershipOperator.AND
    assert result.root.conditions[0].id == "normalize.disease.ncit:C3797"

    assert isinstance(result.root.conditions[1], ConditionSet)
    assert result.root.conditions[1].id == "metakb.cs:xw9sBMfjiKmjf6Xda1sUamhi76oLETPO"

    assert result.root.conditions[1].membershipOperator == MembershipOperator.OR
    # eventually these should be normalized out of source IDs too
    # see https://github.com/cancervariants/metakb/issues/726
    assert result.root.conditions[1].conditions[0].id == "civic.phenotype:8121"
    assert result.root.conditions[1].conditions[1].id == "civic.phenotype:2656"
    assert result.root.conditions[1].conditions[2].id == "civic.phenotype:16642"

    # handle case of disease + secondary finding as phenotype
    # for now, we return the phenotype as-is, but in the phenotype normalizer issue,
    # we may want to handle it differently
    result = transformer._normalize_condition(
        unnormalized_conditions["civic_melanoma_brain_mets"]
    )
    assert result is not None
    assert isinstance(result.root, ConditionSet)
    assert result.root.id == "metakb.cs:"
    assert result.root.membershipOperator == MembershipOperator.AND
    assert result.root.conditions[0].id == "normalize.disease.ncit:"
    assert result.root.conditions[1].id == "civic.phenotype:10817"

    fake_disease = MappableConcept(
        id="src:12345", conceptType="Disease", name="asdfghjkl;"
    )
    assert transformer._normalize_condition(Condition(root=fake_disease)) is None, (
        "Handle normalization failure in simple disease"
    )

    fake_conditionset = Condition(
        root=ConditionSet(
            membershipOperator=MembershipOperator.OR,
            conditions=[fake_disease, unnormalized_conditions["civic.did:8"].root],
        )
    )
    assert transformer._normalize_condition(fake_conditionset) is None, (
        "Handle normalization failure within ConditionSet"
    )


def test_normalize_therapeutic(
    transformer: Transformer, unnormalized_therapeutics: dict[str, Therapeutic]
):
    # TODO maybe these need IDs added first? we'll see if they pass
    result = transformer._normalize_therapeutic(
        unnormalized_therapeutics["moa_bosutinib"]
    )
    assert result is not None
    assert isinstance(result.root, MappableConcept)
    assert result.root.id == "normalize.therapy.ncit:"

    result = transformer._normalize_therapeutic(
        unnormalized_therapeutics["moa_azacitidine_panobinostat"]
    )
    assert result is not None

    result = transformer._normalize_therapeutic(
        unnormalized_therapeutics["civic_trastuzumab"]
    )
    result = transformer._normalize_therapeutic(
        unnormalized_therapeutics["civic_cobimetinib_vemurafenib_combo"]
    )

    fake_drug = MappableConcept(id="src:12345", conceptType="Drug", name="asdfghjkl;")
    assert transformer._normalize_therapeutic(Therapeutic(root=fake_drug)) is None, (
        "Handle failed normalization of simple drug"
    )

    fake_combo_therapy = Therapeutic(
        root=TherapyGroup(
            membershipOperator=MembershipOperator.AND,
            therapies=[unnormalized_therapeutics["moa_bosutinib"].root, fake_drug],
        )
    )
    assert transformer._normalize_therapeutic(fake_combo_therapy) is None, (
        "Handle normalization failure inside combo therapy"
    )


@pytest.mark.asyncio
async def test_build_aggregate_statement(transformer: Transformer):
    # maybe one for each type of statement
    statement = None  # TODO
    result = await transformer._build_aggregated_diag_statement(statement)
    assert result is not None
    assert result.id == "metakb.assertion:"
