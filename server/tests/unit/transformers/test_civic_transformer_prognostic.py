"""Test CIViC Transformation to common data model for prognostic."""

import pytest
import pytest_asyncio
from civicpy import civic as civicpy

FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture
async def data(civic_cdm_data):
    """Create a CIViC Transformer test fixture."""
    eids = [26]
    evidence_items = [civicpy.get_evidence_by_id(eid) for eid in eids]
    return await civic_cdm_data(evidence_items, [], FILENAME)


@pytest.fixture(scope="module")
def statements(civic_eid26_study_stmt):
    """Create test fixture for CIViC Prognostic statements."""
    return [civic_eid26_study_stmt]


def test_civic_cdm(data, statements, check_transformed_cdm, tmp_path):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(data, statements, tmp_path / FILENAME)
