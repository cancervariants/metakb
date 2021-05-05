"""Test CIViC Transformation to common data model for Therapeutic Response."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a CIViC Transform test fixture."""
    c = CIViCTransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/therapeutic/civic_harvester.json")
    c.transform()
    c._create_json(
        civic_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'therapeutic'
    )
    with open(f"{PROJECT_ROOT}/tests/data/transform/"
              f"therapeutic/civic_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def statements(civic_eid2997_statement, civic_aid6_statement):
    """Create test fixture for statements."""
    return [civic_eid2997_statement, civic_aid6_statement]


@pytest.fixture(scope='module')
def propositions(civic_eid2997_proposition):
    """Create test fixture for proposition."""
    return [civic_eid2997_proposition]


@pytest.fixture(scope='module')
def variation_descriptors(civic_vid33):
    """Create test fixture for variants."""
    return [civic_vid33]


@pytest.fixture(scope='module')
def therapy_descriptors(civic_tid146):
    """Create test fixture for therapy descriptors."""
    return [civic_tid146]


@pytest.fixture(scope='module')
def disease_descriptors(civic_did8):
    """Create test fixture for disease descriptors."""
    return [civic_did8]


@pytest.fixture(scope='module')
def gene_descriptors(civic_gid19):
    """Create test fixture for gene descriptors."""
    return [civic_gid19]


@pytest.fixture(scope='module')
def documents(civic_eid2997_document, civic_aid6_document):
    """Create test fixture for documents."""
    return [civic_eid2997_document, civic_aid6_document]


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        assert actual == test


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(actual_data[key]) == set(test_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        for item in actual_data:
            if isinstance(item, list):
                assert set(actual_data) == set(test_data)
            else:
                assert_non_lists(actual_data, test_data)


def test_civic_cdm(data, statements, propositions, variation_descriptors,
                   gene_descriptors, therapy_descriptors, disease_descriptors,
                   civic_methods, documents):
    """Test that civic transform works correctly."""
    assertions(statements, data['statements'])
    assertions(propositions, data['propositions'])
    assertions(variation_descriptors, data['variation_descriptors'])
    assertions(gene_descriptors, data['gene_descriptors'])
    assertions(therapy_descriptors, data['therapy_descriptors'])
    assertions(disease_descriptors, data['disease_descriptors'])
    assertions(civic_methods, data['methods'])
    assertions(documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/therapeutic/"
              f"civic_cdm.json")
