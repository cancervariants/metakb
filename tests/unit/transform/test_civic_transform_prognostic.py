"""Test CIViC Transformation to common data model for prognostic."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a CIViC Transform test fixture."""
    c = CIViCTransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/prognostic/civic_harvester.json")
    c.transform()
    c._create_json(
        civic_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'prognostic'
    )
    with open(f"{PROJECT_ROOT}/tests/data/transform/"
              f"prognostic/civic_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def statements(civic_eid26_statement, civic_eid1756_statement):
    """Create test fixture for statements."""
    return [civic_eid26_statement, civic_eid1756_statement]


@pytest.fixture(scope='module')
def propositions(civic_eid26_proposition, civic_eid1756_proposition):
    """Create test fixture for proposition."""
    return [civic_eid26_proposition, civic_eid1756_proposition]


@pytest.fixture(scope='module')
def variation_descriptors(civic_vid65, civic_vid258):
    """Create test fixture for variants."""
    return [civic_vid65, civic_vid258]


@pytest.fixture(scope='module')
def disease_descriptors(civic_did3, civic_did556):
    """Create test fixture for disease descriptors."""
    return [civic_did3, civic_did556]


@pytest.fixture(scope='module')
def gene_descriptors(civic_gid29, civic_gid3672):
    """Create test fixture for gene descriptors."""
    return [civic_gid29, civic_gid3672]


@pytest.fixture(scope='module')
def documents(pmid_16384925, pmid_27819322):
    """Create test fixture for documents."""
    return [pmid_16384925, pmid_27819322]


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
                   gene_descriptors, disease_descriptors, civic_methods,
                   documents):
    """Test that civic transform works correctly."""
    assertions(statements, data['statements'])
    assertions(propositions, data['propositions'])
    assertions(variation_descriptors, data['variation_descriptors'])
    assertions(gene_descriptors, data['gene_descriptors'])
    assertions(disease_descriptors, data['disease_descriptors'])
    assertions(civic_methods, data['methods'])
    assertions(documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/prognostic/civic_cdm.json")
