"""Test PMKB deltas."""
import pytest
from metakb import PROJECT_ROOT, version
from metakb.delta import Delta
from datetime import date
import json
import os

MAIN_JSON = PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'main_pmkb.json'
UPDATED_JSON = \
    PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'updated_pmkb.json'


@pytest.fixture(scope='module')
def pmkb():
    """Create PMKB Delta test fixture."""
    return Delta(MAIN_JSON, 'pmkb', _updated_json=UPDATED_JSON)


@pytest.fixture(scope='module')
def main_data():
    """Create main_data test fixture."""
    with open(MAIN_JSON, 'r') as f:
        main_data = json.load(f)
        return main_data


@pytest.fixture(scope='module')
def updated_data():
    """Create updated_data test fixture."""
    with open(UPDATED_JSON, 'r') as f:
        updated_data = json.load(f)
        return updated_data


@pytest.fixture(scope='module')
def diff():
    """Create a test fixture for PMKB deltas."""
    return {
        '_meta': {
            'metakb_version': version,
            'date_harvested': date.today().strftime('%Y%m%d'),
            'pmkb_version': '1.0'
        },
        'interpretations': {
            'DELETE': [],
            'INSERT': [
                {
                    "id": "5",
                    "gene": {
                        "name": "NOTCH2"
                    },
                    "evidence_items": [
                        "Lee SY, et al. Gain-of-function mutations and copy number  increases of Notch2 in diffuse large B-cell lymphoma. Cancer Sci 2009;100(5):920-6",  # noqa: E501
                        "Kiel MJ, et al. Whole-genome sequencing identifies recurrent somatic NOTCH2 mutations in splenic marginal zone lymphoma. J Exp Med 2012;209(9):1553-65"  # noqa: E501
                    ],
                    "pmkb_evidence_tier": "1",
                    "variants": [
                        {
                            "name": "NOTCH2 I2304fs",
                            "id": "332"
                        },
                        {
                            "name": "NOTCH2 exon(s) 34 frameshift",
                            "id": "333"
                        }
                    ],
                    "diseases": [
                        "Diffuse Large B Cell Lymphoma",
                        "Marginal Zone B Cell Lymphoma"
                    ],
                    "therapies": [
                        "therapeutic procedure"
                    ],
                    "description": "NOTCH2 gain of function mutations have been reported in apprximately 25% of splenic marginal zone lymphomas and are thought to be rare in non-splenic marginal zone lymphomas.  These mutations are typically located near the C-terminal PEST domain and lead to protein truncation or, more rarely, are nonsynonymous substitution mutations affected the extracellular heterodimerization domain.  NOTCH2 mutations may be associated with a worse prognosis among cases of splenic marginal zone lymphoma.  In addition, NOTCH2 PEST domain mutations have been reported in approximately 8% of diffuse large B cell lymphomas and in vitro systems have demonstrated these PEST domain mutant NOTCH2 receptors have increased activity compared to wild type NOTCH2.  In addion, copy number gain has been reported in a subset of DLBCL cases with NOTCH2 mutations.",  # noqa: E501
                    "tissue_types": [
                        "Bone Marrow",
                        "Blood"
                    ],
                    "origin": "Somatic"
                }
            ],
            'UPDATE': [
                {
                    "113": {"$delete": ["diseases"]}
                }
            ]
        },
        'variants': {
            'DELETE': [
                {
                    "id": "214",
                    "name": "test_remove"
                }
            ],
            'INSERT': [],
            'UPDATE': [
                {
                    "217": {
                        "partner_gene": "another gene"
                    }
                },
                {
                    "1583": {
                        "new_field": "new_value"
                    },
                }
            ]
        }
    }


@pytest.fixture(scope='module')
def delta():
    """Create empty delta test fixture."""
    return {
        'variants': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        },
        'interpretations': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        }
    }


def test_init():
    """Test that init is correct."""
    pmkb_d = Delta(MAIN_JSON, 'pmkb')
    assert pmkb_d._main_json == MAIN_JSON
    assert pmkb_d._updated_json is None

    pmkb_d = Delta(MAIN_JSON, 'pmkb', _updated_json=UPDATED_JSON)
    assert pmkb_d._main_json == MAIN_JSON
    assert pmkb_d._updated_json == UPDATED_JSON


def test_compute_delta(pmkb, diff):
    """Test that compute_delta method is correct."""
    assert pmkb.compute_delta() == diff

    # Test when _updated_json is not in kwargs
    pmkb_d = Delta(MAIN_JSON, 'pmkb')
    pmkb_d.compute_delta()
    fn = PROJECT_ROOT / 'data' / 'pmkb' / \
        f"pmkb_harvester_{date.today().strftime('%Y%m%d')}.json"
    assert fn.exists()
    os.remove(fn)
    assert not fn.exists()


def test_ins_del_delta(pmkb, diff, main_data, updated_data, delta):
    """Test that _ins_del_delta method is correct."""
    pmkb._ins_del_delta(delta, 'variants', 'DELETE', ['214'],
                        main_data['variants'])
    assert delta['variants']['DELETE'] == diff['variants']['DELETE']

    pmkb._ins_del_delta(delta, 'interpretations', 'INSERT', ['5'],
                        updated_data['interpretations'])
    assert delta['interpretations']['INSERT'] == \
        diff['interpretations']['INSERT']


def test_update_delta(pmkb, diff, delta, updated_data, main_data):
    """Test that _update_delta method is correct."""
    pmkb._update_delta(delta, 'interpretations',
                       updated_data['interpretations'],
                       main_data['interpretations'])
    assert delta['interpretations']['UPDATE'] == \
        diff['interpretations']['UPDATE']


def test_get_ids(pmkb, main_data, updated_data):
    """Test that _get_ids method is correct."""
    assert len(pmkb._get_ids(main_data['interpretations'])) == 1
    assert len(pmkb._get_ids(main_data['variants'])) == 3

    assert len(pmkb._get_ids(updated_data['interpretations'])) == 2
    assert len(pmkb._get_ids(updated_data['variants'])) == 2


def test_create_json(pmkb, diff):
    """Test that _create_json method is correct."""
    test_date = '19980108'
    pmkb._create_json(diff, test_date)
    file_name = PROJECT_ROOT / 'data' / 'pmkb' / f'pmkb_deltas_' \
                                                 f'{test_date}.json'
    assert file_name.exists()
    os.remove(file_name)
    assert not file_name.exists()
