"""Test CIViC deltas."""
import pytest
from metakb import PROJECT_ROOT
from metakb.deltas.civic import CIVICDelta
from datetime import date


@pytest.fixture(scope='module')
def civic():
    """Create CIViC Delta text fixture"""
    main_json = PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'main_civic.json'
    new_json = PROJECT_ROOT / 'tests' / 'data' / 'deltas' / 'new_civic.json'
    return CIVICDelta(main_json, _new_json=new_json).compute_delta()


@pytest.fixture(scope='module')
def diff():
    """Create a test fixture for CIViC deltas."""
    return {
        '_meta': {
            'civicpy_version': '1.1.2',
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


def test_evidence_delta(civic, diff):
    """Test that CIViC deltas are correct."""
    assert civic == diff
