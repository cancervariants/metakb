import json
from pathlib import Path

import civicpy.civic as civicpy
import pytest
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.va_spec.base import ConditionSet, TherapyGroup

from metakb.transformers.civic import CivicTransformer


# this needs to be scoped for each function, for reasons relating to the ALRU cache and pytest event loops
@pytest.fixture
def civic_transformer() -> CivicTransformer:
    return CivicTransformer()


@pytest.fixture(scope="session")
def normalize_variant_input(test_data_dir: Path) -> dict[str, CategoricalVariant]:
    with (
        test_data_dir / "transformers" / "civic_normalize_variant_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: CategoricalVariant(**v) for k, v in data.items()}


@pytest.fixture(scope="session")
def ensure_conditionset_id_input(test_data_dir: Path) -> dict[str, ConditionSet]:
    with (
        test_data_dir / "transformers" / "civic_ensure_conditionset_id_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: ConditionSet(**v) for k, v in data.items()}


@pytest.fixture(scope="session")
def ensure_therapygroup_id_input(test_data_dir: Path) -> dict[str, TherapyGroup]:
    with (
        test_data_dir / "transformers" / "civic_ensure_therapygroup_id_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: TherapyGroup(**v) for k, v in data.items()}


@pytest.mark.asyncio
async def test_normalize_variant(
    civic_transformer: CivicTransformer,
    normalize_variant_input: dict[str, CategoricalVariant],
):
    result = await civic_transformer._normalize_variant(
        normalize_variant_input["civic.mpid:34"]
    )
    assert result is not None
    assert result.id == "metakb.cv:PSQ.VA.sMA9h8fzDi0RvweMlxtD0_Oi8B-JZ1V-"
    # assert result.name == "EGFR T790M"  # TODO pending issue 727
    assert result.constraints
    assert len(result.constraints) == 1
    assert (
        result.constraints[0].root.allele.id
        == "ga4gh:VA.sMA9h8fzDi0RvweMlxtD0_Oi8B-JZ1V-"
    )

    # defining location isn't supported yet
    result = await civic_transformer._normalize_variant(
        normalize_variant_input["civic.mpid:17"]
    )
    assert result is None

    # feature context constraint isn't supported yet
    result = await civic_transformer._normalize_variant(
        normalize_variant_input["civic.mpid:332"]
    )
    assert result is None

    # generally unsupported
    result = await civic_transformer._normalize_variant(
        normalize_variant_input["civic.mpid:85"]
    )
    assert result is None

    # harder feature context constraint
    result = await civic_transformer._normalize_variant(
        normalize_variant_input["civic.mpid:86"]
    )
    assert result is None


def test_civic_claim_to_statement():
    # TODO construct a case for each kind of valid input
    # TODO esp find something that fails each error case
    pass


def test_civic_ensure_therapygroup_id(
    civic_transformer: CivicTransformer,
    ensure_therapygroup_id_input: dict[str, TherapyGroup],
):
    tg = ensure_therapygroup_id_input["neratinib/trastuzumab"]
    assert tg.id is None
    civic_transformer._ensure_therapygroup_id(tg)
    assert tg.id == "civic.tg:0sW9STbxDG18TPKMJ2edv_XGNbkCFyYH"

    tg = ensure_therapygroup_id_input["dabrafenib + trametinib"]
    assert tg.id is None
    civic_transformer._ensure_therapygroup_id(tg)
    assert tg.id == "civic.tg:q2pjgRaI0hSmor_qFawHt7xxXcrGEAfG"


def test_civic_ensure_conditionset_id(
    civic_transformer: CivicTransformer,
    ensure_conditionset_id_input: dict[str, ConditionSet],
):
    phenotype_union = ensure_conditionset_id_input["phenotype_union"]
    assert phenotype_union.id is None
    civic_transformer._ensure_conditionset_id(phenotype_union)
    assert phenotype_union.id == "civic.cs:xw9sBMfjiKmjf6Xda1sUamhi76oLETPO"

    pediatric_b_all = ensure_conditionset_id_input["pediatric b-all"]
    assert pediatric_b_all.id is None
    civic_transformer._ensure_conditionset_id(pediatric_b_all)
    assert pediatric_b_all.id == "civic.cs:3n4In-CHQIAHbmqcHR57K9sKycTLqE2i"


@pytest.mark.asyncio
async def test_transform(test_data_dir: Path, civic_transformer: CivicTransformer):
    # load test cache and manually inject it before running test
    cache_pkl_path = test_data_dir / "transformers" / "civicpy_transformer_cache.pkl"
    civicpy.load_cache(str(cache_pkl_path), on_stale="ignore")
    await civic_transformer.transform()

    assert civic_transformer.processed_data.statements[0].id == "civic.eid:238"
    assert (
        civic_transformer.processed_data.statements[1].id
        == "metakb.assertion:WRdtjMzgdMFsPX2i4MgN-BTFz_C3ITZQ"
    )
