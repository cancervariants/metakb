import json
from unittest.mock import patch

import pytest_asyncio
from civicpy import civic as civicpy

from metakb.transformers.civic import CivicTransformer


@pytest_asyncio.fixture
async def civic_cdm_data(normalizers, tmp_path):
    """Get CIViC CDM data."""

    async def _civic_cdm_data(evidence_items, assertions, file_name):
        with (
            patch.object(
                civicpy,
                "get_all_evidence",
                return_value=evidence_items,
            ),
            patch.object(civicpy, "get_all_assertions", return_value=assertions),
        ):
            t = CivicTransformer(data_dir=tmp_path, normalizers=normalizers)
            await t.transform()
            t.create_json(tmp_path / file_name)
            with (tmp_path / file_name).open() as f:
                return json.load(f)

    return _civic_cdm_data
