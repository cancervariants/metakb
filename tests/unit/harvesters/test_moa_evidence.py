"""Test MOAlmanac source"""
import pytest
from metakb.harvesters.moalmanac import MOAlmanac


@pytest.fixture(scope='module')
def evidence():
    """Create a list of evidence."""
    moa = MOAlmanac()

    return moa._harvest_evidence()


@pytest.fixture(scope='module')
def source66():
    """Create a fixture for evidence #55."""
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


def test_evidence_66(evidence, source66):
    """Test moa harvester works correctly for evidence."""
    for e in evidence:
        if e['id'] == 66:
            actual = e
            break
    assert actual.keys() == source66.keys()
    keys = source66.keys()
    for key in keys:
        assert actual[key] == source66[key]
