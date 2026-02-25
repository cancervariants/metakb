import json
from pathlib import Path

import pytest
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import Condition, ConditionSet

from metakb.transformers.base import Transformer
from metakb.transformers.civic import CivicTransformer


@pytest.fixture(scope="session")
def transformer() -> Transformer:
    return CivicTransformer()


@pytest.fixture(scope="session")
def conditions(test_data_dir: Path) -> dict[str, Condition]:
    with (test_data_dir / "conditions.json").open() as f:
        data = json.load(f)
        return {k: Condition(**v) for k, v in data.items()}


def test_normalize_disease(transformer: Transformer, conditions: dict[str, Condition]):
    civic_lnscc = conditions["civic.did:8"]
    result = transformer._normalize_condition(civic_lnscc)
    assert result is not None
    assert isinstance(result.root, MappableConcept)
    assert result.root.id == "normalize.disease.ncit:C2926"


def test_normalize_conditionset(
    transformer: Transformer, conditions: dict[str, Condition]
):
    conditionset = conditions["civic_plexiform_neurofibroma_nonadult"]
    assert conditionset.root.id is None, "This is supposed to be null for testing"
    assert conditionset.root.conditions[1].id is None, (
        "This is supposed to be null for testing"
    )

    result = transformer._normalize_condition(conditionset)
    assert result is not None
    assert isinstance(result.root, ConditionSet)
    assert conditionset.root.id == "civic.cs:ri5aNePF5Ixr88FSebPlLvh2fiGDwwe8", (
        "Check that input ID is added in-place"
    )
    assert result.root.id == "idk"
    assert result.root.membershipOperator == "AND"
    assert result.root.conditions[0].id == "civic.did:1215"

    assert (
        conditionset.root.conditions[1].id
        == "civic.cs:9JGUt5j3jvRoENkOSxHOi8SUk0Tabgxk"
    ), "Check that input ID of contained conditionset is added in-place"
    assert isinstance(result.root.conditions[1], ConditionSet)
