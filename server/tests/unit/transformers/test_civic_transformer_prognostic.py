"""Test CIViC Transformation to common data model for prognostic."""

import json
from unittest.mock import patch

import pytest
import pytest_asyncio
from civicpy import civic as civicpy

from metakb.transformers.civic import CivicTransformer

FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture
async def data(normalizers, tmp_path):
    """Create a CIViC Transformer test fixture."""
    eids = [26]

    evidence_items = [civicpy.get_evidence_by_id(eid) for eid in eids]

    with (
        patch.object(
            civicpy,
            "get_all_evidence",
            return_value=evidence_items,
        ),
        patch.object(civicpy, "get_all_assertions", return_value=[]),
    ):
        t = CivicTransformer(data_dir=tmp_path, normalizers=normalizers)
        await t.transform()
        t.create_json(tmp_path / FILENAME)
        with (tmp_path / FILENAME).open() as f:
            return json.load(f)


@pytest.fixture(scope="module")
def statements(civic_eid26_study_stmt):
    """Create test fixture for CIViC Prognostic statements."""
    return [civic_eid26_study_stmt]


def test_civic_cdm(data, statements, check_transformed_cdm, tmp_path):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(data, statements, tmp_path / FILENAME)
