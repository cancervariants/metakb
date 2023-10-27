"""Test MOA Transformation to common data model"""
import pytest
import pytest_asyncio
from metakb.transform.moa import MOATransform
from metakb import PROJECT_ROOT
import json

DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform"
FILENAME = "moa_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a MOA Transform test fixture."""
    harvester_path = DATA_DIR / "moa_harvester.json"
    moa = MOATransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await moa.transform()
    moa.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def asst71_statements(moa_aid71_statement):
    """Create assertion71 statements test fixture."""
    return [moa_aid71_statement]


def test_moa_cdm(data, asst71_statements, check_transformed_cdm):
    """Test that moa transform works correctly."""
    check_transformed_cdm(
        data, asst71_statements, DATA_DIR / FILENAME
    )
