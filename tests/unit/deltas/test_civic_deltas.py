"""Test CIViC deltas."""
import pytest
from metakb import PROJECT_ROOT
from metakb.deltas import Delta
from datetime import date
import json
import os

MAIN_JSON = PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'main_civic.json'
UPDATED_JSON = \
    PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'updated_civic.json'


@pytest.fixture(scope='module')
def civic():
    """Create CIViC Delta test fixture."""
    return Delta(MAIN_JSON, 'civic', _updated_json=UPDATED_JSON)


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
    """Create a test fixture for CIViC deltas."""
    return {
        '_meta': {
            'civicpy_version': '1.1.2',
            'metakb_version': '1.0.1',
            'date_harvested': date.today().strftime('%Y%m%d')
        },
        'genes': {
            'DELETE': [
                {
                    "id": 3,
                    "name": "test_remove"
                }
            ],
            'INSERT': [],
            'UPDATE': [
                {
                    '2778': {
                        'aliases': {
                            '$insert': [
                                (1, 'MIF2')
                            ]
                        }

                    }
                }
            ]
        },
        'variants': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': [
                {
                    '27': {
                        '$delete': ['entrez_name']
                    }
                }
            ]
        },
        'assertions': {
            'DELETE': [],
            'INSERT': [
                {
                    "id": 1,
                    "description": "description"
                }
            ],
            'UPDATE': []
        },
        'evidence': {
            'INSERT': [],
            'DELETE': [],
            'UPDATE': [
                {
                    "358": {"variant_origin": "Somatic"}
                }
            ]
        }
    }


@pytest.fixture(scope='module')
def delta():
    """Create empty delta test fixture."""
    return {
        'genes': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        },
        'variants': {
            'DELETE': [],
            'INSERT': [],
            'UPDATE': []
        },
        'evidence': {
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
    cd = Delta(MAIN_JSON, 'civic')
    assert cd._main_json == MAIN_JSON
    assert cd._updated_json is None

    cd = Delta(MAIN_JSON, 'civic', _updated_json=UPDATED_JSON)
    assert cd._main_json == MAIN_JSON
    assert cd._updated_json == UPDATED_JSON


def test_compute_delta(civic, diff):
    """Test that compute_delta method is correct."""
    assert civic.compute_delta() == diff

    # Test when _updated_json is not in kwargs
    cd = Delta(MAIN_JSON, 'civic')
    cd.compute_delta()
    fn = PROJECT_ROOT / 'data' / 'civic' / \
        f"civic_harvester_{date.today().strftime('%Y%m%d')}.json"
    assert fn.exists()
    os.remove(fn)
    assert not fn.exists()


def test_ins_del_delta(civic, diff, main_data, updated_data, delta):
    """Test that _ins_del_delta method is correct."""
    civic._ins_del_delta(delta, 'genes', 'DELETE', [3], main_data['genes'])
    assert delta['genes']['DELETE'] == diff['genes']['DELETE']

    civic._ins_del_delta(delta, 'assertions', 'INSERT', [1],
                         updated_data['assertions'])
    assert delta['assertions']['INSERT'] == diff['assertions']['INSERT']


def test_update_delta(civic, diff, delta, updated_data, main_data):
    """Test that _update_delta method is correct."""
    civic._update_delta(delta, 'genes', updated_data['genes'],
                        main_data['genes'])
    assert delta['genes']['UPDATE'] == diff['genes']['UPDATE']

    civic._update_delta(delta, 'variants', updated_data['variants'],
                        main_data['variants'])
    assert delta['variants']['UPDATE'] == diff['variants']['UPDATE']

    civic._update_delta(delta, 'evidence', updated_data['evidence'],
                        main_data['evidence'])
    assert delta['evidence']['UPDATE'] == diff['evidence']['UPDATE']


def test_get_ids(civic, main_data, updated_data):
    """Test that _get_ids method is correct."""
    assert len(civic._get_ids(main_data['assertions'])) == 0
    assert len(civic._get_ids(main_data['variants'])) == 1
    assert len(civic._get_ids(main_data['genes'])) == 2
    assert len(civic._get_ids(main_data['evidence'])) == 1

    assert len(civic._get_ids(updated_data['assertions'])) == 1
    assert len(civic._get_ids(updated_data['variants'])) == 1
    assert len(civic._get_ids(updated_data['genes'])) == 1
    assert len(civic._get_ids(updated_data['evidence'])) == 1


def test_create_json(civic, diff):
    """Test that _create_json method is correct."""
    test_date = '19980108'
    civic._create_json(diff, test_date)
    file_name = PROJECT_ROOT / 'data' / 'civic' / f'civic_deltas_' \
                                                  f'{test_date}.json'
    assert file_name.exists()
    os.remove(file_name)
    assert not file_name.exists()
