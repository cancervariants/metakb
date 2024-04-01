"""Test CIViC Transformation to common data model for Therapeutic Response."""
import json

import pytest
import pytest_asyncio

from metakb import PROJECT_ROOT
from metakb.transform.civic import CivicTransform

DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio()
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransform(
        data_dir=DATA_DIR, harvester_path=harvester_path, normalizers=normalizers
    )
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with (DATA_DIR / FILENAME).open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def studies(civic_eid2997_study, civic_eid816_study, civic_eid9851_study):
    """Create test fixture for CIViC therapeutic studies."""
    return [civic_eid2997_study, civic_eid816_study, civic_eid9851_study]


def test_civic_cdm(data, studies, check_transformed_cdm):
    """Test that civic transform works correctly."""
    check_transformed_cdm(data, studies, DATA_DIR / FILENAME)
