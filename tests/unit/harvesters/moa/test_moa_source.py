"""Test MOAlmanac source"""

import json
from unittest.mock import patch

import pytest
from tests.conftest import TEST_HARVESTERS_DIR

from metakb.harvesters.moa import MoaHarvester
from metakb.schemas.app import SourceName


@pytest.fixture(scope="module")
def sources():
    """Create a list of sources."""
    moa = MoaHarvester()

    return moa._harvest_sources()


@pytest.fixture(scope="module")
def source69():
    """Create a fixture for source ID 69."""
    return {
        "id": 69,
        "type": "Journal",
        "doi": "10.1186/s40425-016-0148-7",
        "nct": "NCT01673854",
        "pmid": 27532019,
        "url": "https://doi.org/10.1186/s40425-016-0148-7",
        "citation": "Amin A, Lawson DH, Salama AK, et al. Phase II study of vemurafenib followed by ipilimumab in patients with previously untreated BRAF-mutated metastatic melanoma. J Immunother Cancer. 2016;4:44.",
    }


@patch.object(MoaHarvester, "_get_all_assertions")
def test_source69(test_get_all_assertions, source69):
    """Test moa harvester works correctly for evidence."""
    with (TEST_HARVESTERS_DIR / SourceName.MOA.value / "assertions.json").open() as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    assertion_resp = MoaHarvester()._get_all_assertions()
    sources = MoaHarvester()._harvest_sources(assertion_resp)

    actual = None
    for s in sources:
        if s["id"] == source69["id"]:
            actual = s
            break
    assert actual == source69
