"""Test MOAlmanac source"""
import json

from mock import patch
import pytest

from metakb import PROJECT_ROOT  # noqa: I202
from metakb.harvesters import MOAHarvester


@pytest.fixture(scope="module")
def sources():
    """Create a list of sources."""
    moa = MOAHarvester()

    return moa._harvest_sources()


@pytest.fixture(scope="module")
def source68():
    """Create a fixture for source of evidence #68."""
    return {
        "id": 68,
        "type": "Journal",
        "doi": "10.1186/s40425-016-0148-7",
        "nct": "NCT01673854",
        "pmid": 27532019,
        "url": "https://doi.org/10.1186/s40425-016-0148-7",
        "citation": "Amin A, Lawson DH, Salama AK, et al. Phase II "
                    "study of vemurafenib followed by ipilimumab in patients "
                    "with previously untreated BRAF-mutated metastatic "
                    "melanoma. J Immunother Cancer. 2016;4:44."
    }


@patch.object(MOAHarvester, "_get_all_assertions")
def test_source68(test_get_all_assertions, source68):
    """Test moa harvester works correctly for evidence."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    assertion_resp = MOAHarvester()._get_all_assertions()
    sources = MOAHarvester()._harvest_sources(assertion_resp)

    actual = None
    for s in sources:
        if s["id"] == 68:
            actual = s
            break
    assert actual == source68
