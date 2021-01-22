"""Test MOAlmanac deltas."""
import pytest
from metakb import PROJECT_ROOT
from metakb.deltas import Delta
from datetime import date
import json
import os

MAIN_JSON = PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'main_moa.json'
UPDATED_JSON = \
    PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'updated_moa.json'


@pytest.fixture(scope='module')
def moa():
    """Create MOAlmanac Delta test fixture."""
    return Delta(MAIN_JSON, 'moa', _updated_json=UPDATED_JSON)


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
    """Create a test fixture for MOAlmanac deltas."""
    return {
        '_meta': {
            'metakb_version': '1.0.1',
            'date_harvested': date.today().strftime('%Y%m%d'),
            'moa_api_version': '0.2'
        },
        'assertions': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': [
                {
                    '3': {
                        'disease': {
                            'oncotree_code': 'ALL',
                            'oncotree_term': 'Acute Lymphoid Leukemia'
                        },
                        'created_on': '01/16/21',
                        '$delete': ['test update delete']
                    }
                }
            ]
        },
        'sources': {
            'DELETE': [],
            'INSERT': [
                {
                    'id': 22,
                    'type': 'Journal',
                    'assertion_id': [30, 288],
                    'doi': '10.1371/journal.pgen.1004135',
                    'nct': None,
                    'pmid': '24550739',
                    'url': 'https://doi.org/10.1371/journal.pgen.1004135',
                    'citation': 'Borad MJ, Champion MD, Egan JB, et al. '
                                'Integrated genomic characterization reveals '
                                'novel, therapeutically relevant drug targets'
                                ' in FGFR and EGFR pathways in sporadic '
                                'intrahepatic cholangiocarcinoma. PLoS Genet.'
                                ' 2014;10(2):e1004135.'
                }
            ],
            'UPDATE': [
                {
                    '2': {
                        'assertion_id': {
                            '$insert': [(1, 3)]
                        }
                    }
                }
            ]
        },
        'variants': {
            'DELETE': [
                {
                    'id': 5,
                    'feature_type': 'test_removal'
                }
            ],
            'INSERT': [],
            'UPDATE': []
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
        'sources': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        },
        'assertions': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        }
    }


def test_init():
    """Test that init is correct."""
    moad = Delta(MAIN_JSON, 'moa')
    assert moad._main_json == MAIN_JSON
    assert moad._updated_json is None

    moad = Delta(MAIN_JSON, 'moa', _updated_json=UPDATED_JSON)
    assert moad._main_json == MAIN_JSON
    assert moad._updated_json == UPDATED_JSON


def test_compute_delta(moa, diff):
    """Test that compute_delta method is correct."""
    assert moa.compute_delta() == diff

    # Test when _updated_json is not in kwargs
    moad = Delta(MAIN_JSON, 'moa')
    moad.compute_delta()
    fn = PROJECT_ROOT / 'data' / 'moa' / \
        f"moa_harvester_{date.today().strftime('%Y%m%d')}.json"
    assert fn.exists()
    os.remove(fn)
    assert not fn.exists()


def test_ins_del_delta(moa, diff, main_data, updated_data, delta):
    """Test that _ins_del_delta method is correct."""
    moa._ins_del_delta(delta, 'variants', 'DELETE', [5], main_data['variants'])
    assert delta['variants']['DELETE'] == diff['variants']['DELETE']

    moa._ins_del_delta(delta, 'sources', 'INSERT', [22],
                       updated_data['sources'])
    assert delta['sources']['INSERT'] == diff['sources']['INSERT']


def test_update_delta(moa, diff, delta, updated_data, main_data):
    """Test that _update_delta method is correct."""
    moa._update_delta(delta, 'assertions', updated_data['assertions'],
                      main_data['assertions'])
    assert delta['assertions']['UPDATE'] == diff['assertions']['UPDATE']

    moa._update_delta(delta, 'sources', updated_data['sources'],
                      main_data['sources'])
    assert delta['sources']['UPDATE'] == diff['sources']['UPDATE']


def test_get_ids(moa, main_data, updated_data):
    """Test that _get_ids method is correct."""
    assert len(moa._get_ids(main_data['assertions'])) == 1
    assert len(moa._get_ids(main_data['variants'])) == 3
    assert len(moa._get_ids(main_data['sources'])) == 1

    assert len(moa._get_ids(updated_data['assertions'])) == 1
    assert len(moa._get_ids(updated_data['variants'])) == 2
    assert len(moa._get_ids(updated_data['sources'])) == 2


def test_create_json(moa, diff):
    """Test that _create_json method is correct."""
    test_date = '19980108'
    moa._create_json(diff, test_date)
    file_name = PROJECT_ROOT / 'data' / 'moa' / f'moa_deltas_' \
                                                f'{test_date}.json'
    assert file_name.exists()
    os.remove(file_name)
    assert not file_name.exists()
