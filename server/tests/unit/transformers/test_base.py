"""Test methods in the Transformer base class, not tied to specific sources"""

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
    conditionset = conditions["civic_cs_plexiform_neurofibroma_nonadult"]

    result = transformer._normalize_condition(conditionset)
    assert result is not None
    assert isinstance(result.root, ConditionSet)
    assert result.root.id == "metakb.cs:LQCCZxv68jeT4Ngbaf4_ABKwEHZKoKDB"
    assert result.root.membershipOperator == "AND"
    assert result.root.conditions[0].id == "normalize.disease.ncit:C3797"

    assert isinstance(result.root.conditions[1], ConditionSet)
    assert result.root.conditions[1].id == "metakb.cs:xw9sBMfjiKmjf6Xda1sUamhi76oLETPO"

    assert result.root.conditions[1].membershipOperator == "OR"
    # eventually these should be normalized out of source IDs too
    # see https://github.com/cancervariants/metakb/issues/726
    assert result.root.conditions[1].conditions[0].id == "civic.phenotype:8121"
    assert result.root.conditions[1].conditions[1].id == "civic.phenotype:2656"
    assert result.root.conditions[1].conditions[2].id == "civic.phenotype:16642"
