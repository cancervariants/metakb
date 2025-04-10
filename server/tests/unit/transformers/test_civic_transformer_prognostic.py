"""Test CIViC Transformation to common data model for prognostic."""

import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORMERS_DIR

from metakb.transformers.civic import CivicTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "prognostic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
async def data(normalizers):
    """Create a CIViC Transformer test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransformer(
        data_dir=DATA_DIR, harvester_path=harvester_path, normalizers=normalizers
    )
    harvested_data = c.extract_harvested_data()
    await c.transform(harvested_data)
    c.create_json(DATA_DIR / FILENAME)
    with (DATA_DIR / FILENAME).open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def statements(civic_eid26_study_stmt):
    """Create test fixture for CIViC Prognostic statements."""
    return [civic_eid26_study_stmt]


def test_civic_cdm(data, statements, check_transformed_cdm):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(data, statements, DATA_DIR / FILENAME)
