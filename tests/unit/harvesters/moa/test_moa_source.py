"""Test MOAlmanac source"""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters.moalmanac import MOAlmanac
from mock import patch
import json


@pytest.fixture(scope='module')
def sources():
    """Create a list of sources."""
    moa = MOAlmanac()

    return moa._harvest_sources()


@pytest.fixture(scope='module')
def source66():
    """Create a fixture for source of evidence #66."""
    return {
        "id": 66,
        "type": "Journal",
        "assertion_id": [
            166,
            167
        ],
        "doi": "10.1186/s40425-016-0148-7",
        "nct": "NCT01673854",
        "pmid": "27532019",
        "url": "https://doi.org/10.1186/s40425-016-0148-7",
        "citation": "Amin A, Lawson DH, Salama AK, et al. Phase II study of "
                    "vemurafenib followed by ipilimumab in patients with "
                    "previously untreated BRAF-mutated metastatic melanoma."
                    " J Immunother Cancer. 2016;4:44."
    }


@patch.object(MOAlmanac, '_get_all_sources')
def test_source66(test_get_all_sources, source66):
    """Test moa harvester works correctly for evidence."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/sources.json") as f:
        data = json.load(f)
    test_get_all_sources.return_value = data

    sources = MOAlmanac()._harvest_sources()

    actual = None
    for s in sources:
        if s['id'] == 66:
            actual = s
            break
    assert actual == source66
