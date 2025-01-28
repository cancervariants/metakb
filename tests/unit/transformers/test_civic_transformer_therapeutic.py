"""Test CIViC Transformation to common data model for Therapeutic Response."""

import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORMERS_DIR

from metakb.transformers.civic import CivicTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "therapeutic"
FILENAME = "civic_cdm.json"
NON_NORMALIZABLE_FILE_NAME = "civic_cdm2.json"


@pytest_asyncio.fixture(scope="module")
async def normalizable_data(normalizers):
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


@pytest_asyncio.fixture(scope="module")
async def not_normalizable_data(normalizers):
    """Create a CIViC Transformer test fixture for data that cannot be normalized."""
    # NOTE: This file was manually generated to create a fake evidence item
    #       However, it does include some actual civic records that fail to normalize
    #       Gene record was modified to fail
    harvester_path = DATA_DIR / "civic_harvester_not_normalizable.json"
    c = CivicTransformer(
        data_dir=DATA_DIR, harvester_path=harvester_path, normalizers=normalizers
    )
    harvested_data = c.extract_harvested_data()
    await c.transform(harvested_data)
    c.create_json(DATA_DIR / NON_NORMALIZABLE_FILE_NAME)
    with (DATA_DIR / NON_NORMALIZABLE_FILE_NAME).open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def statements(
    civic_eid2997_study_stmt,
    civic_eid816_study_stmt,
    civic_eid9851_study_stmt,
    civic_aid6_statement,
):
    """Create test fixture for CIViC therapeutic statements."""
    return [
        civic_eid2997_study_stmt,
        civic_eid816_study_stmt,
        civic_eid9851_study_stmt,
        civic_aid6_statement,
    ]


def test_civic_cdm(normalizable_data, statements, check_transformed_cdm):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(normalizable_data, statements, DATA_DIR / FILENAME)


def test_civic_cdm_not_normalizable(
    not_normalizable_data, statements, check_transformed_cdm
):
    check_transformed_cdm(
        not_normalizable_data, statements, DATA_DIR / NON_NORMALIZABLE_FILE_NAME
    )
