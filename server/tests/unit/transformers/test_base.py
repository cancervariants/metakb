"""Test methods in the Transformer base class, not tied to specific sources"""

import json
from pathlib import Path

import pytest
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    MembershipOperator,
    Statement,
    Therapeutic,
    TherapyGroup,
)

from metakb.schemas.app import SourceName
from metakb.source_data import SourceDataStore
from metakb.transformers.base import Transformer
from metakb.transformers.civic import CivicTransformer


@pytest.fixture(scope="session")
def transformer() -> Transformer:
    return CivicTransformer(src_data_store=SourceDataStore(src_name=SourceName.CIVIC))


@pytest.fixture(scope="session")
def unnormalized_conditions(test_data_dir: Path) -> dict[str, Condition]:
    with (
        test_data_dir / "transformers" / "base_normalize_condition_input.json"
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


@pytest.fixture(scope="session")
def statements(test_data_dir: Path) -> dict[str, Statement]:
    with (
        test_data_dir / "transformers" / "base_construct_statements_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: Statement(**v) for k, v in data.items()}


def test_normalize_condition(
    transformer: Transformer, unnormalized_conditions: dict[str, Condition]
):
    result = transformer._normalize_condition(unnormalized_conditions["civic.did:8"])
    assert result is not None
    assert isinstance(result.root, MappableConcept)
    assert result.root.id == "metakb.disease:ncit_C2926"

    conditionset = unnormalized_conditions["civic_cs_plexiform_neurofibroma_nonadult"]

    result = transformer._normalize_condition(conditionset)
    assert result is not None
    assert isinstance(result.root, ConditionSet)
    assert result.root.id == "metakb.cs:J48jP9ZWN7G1FKwnzVOXXq01pDiow2x-"
    assert result.root.membershipOperator == MembershipOperator.AND
    assert result.root.conditions[0].id == "metakb.disease:ncit_C3797"

    assert isinstance(result.root.conditions[1], ConditionSet)
    assert result.root.conditions[1].id == "metakb.cs:VXoGdg4PaQbSXeSh5At6zKhSkxrUgxC9"

    assert result.root.conditions[1].membershipOperator == MembershipOperator.OR
    # eventually these should be normalized out of source IDs too
    # see https://github.com/cancervariants/metakb/issues/726
    assert result.root.conditions[1].conditions[0].id == "HP:0011463"
    assert result.root.conditions[1].conditions[1].id == "HP:0003621"
    assert result.root.conditions[1].conditions[2].id == "HP:0025708"

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
    result = transformer._normalize_therapeutic(
        unnormalized_therapeutics["moa_bosutinib"]
    )
    assert result is not None
    assert isinstance(result.root, MappableConcept)
    assert result.root.id == "metakb.therapy:rxcui_1307619"

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
async def test_build_aggregate_statement(
    transformer: Transformer, statements: dict[str, Statement]
):
    assertions = {}

    statement = statements["civic.eid:1421"]
    await transformer._upsert_assertion_from_evidence(statement, assertions)
    result = assertions["metakb.assertion:YFka_hqmWIjps9L6LZz1VfuJFobRTuFs"]
    assert result is not None
    assert (
        result.proposition.subjectVariant.id
        == "metakb.cv:PSQ.VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"
    )
    assert result.proposition.geneContextQualifier.id == "metakb.gene:hgnc_1097"
    assert (
        result.proposition.objectTherapeutic.root.id
        == "metakb.tg:GMZoYSJ8w0MBfq1cFjivZdxrbrFgtD7N"
    )
    assert result.proposition.conditionQualifier.root.id == "metakb.disease:ncit_C3224"
    result_exts = {ext.name: ext.value for ext in result.extensions}
    assert result_exts["metakb_star_rating"]["primaryCoding"]["code"] == "1_star"
    assert (
        result_exts["metakb_star_rating_reason"]
        == "single submission from a clinical lab or online resource"
    )

    statement = statements["civic.aid:10"]
    await transformer._upsert_assertion_from_evidence(statement, assertions)
    result = assertions["metakb.assertion:YFka_hqmWIjps9L6LZz1VfuJFobRTuFs"]
    assert (
        result.proposition.subjectVariant.id
        == "metakb.cv:PSQ.VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"
    )
    assert result.proposition.geneContextQualifier.id == "metakb.gene:hgnc_1097"
    assert (
        result.proposition.objectTherapeutic.root.id
        == "metakb.tg:GMZoYSJ8w0MBfq1cFjivZdxrbrFgtD7N"
    )
    assert result.proposition.conditionQualifier.root.id == "metakb.disease:ncit_C3224"
    result_exts = {ext.name: ext.value for ext in result.extensions}
    assert result_exts["metakb_star_rating"]["primaryCoding"]["code"] == "4_star"
    assert (
        result_exts["metakb_star_rating_reason"]
        == "knowledge from WHO / NCCN / FDA / other regulatory or professional guidelines"
    )

    # smoothly handle failed normalization
    statement = statements["moa.assertion:1"]
    await transformer._upsert_assertion_from_evidence(statement, assertions)
    assert len(assertions) == 1
