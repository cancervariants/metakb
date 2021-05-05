"""Test MOA Transformation to common data model"""
import pytest
from metakb.transform.moa import MOATransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a MOA Transform test fixture."""
    moa = MOATransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/moa_harvester.json")
    moa.transform()
    moa._create_json(moa_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform')
    with open(f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def asst69_statements(moa_aid69_statement):
    """Create assertion69 statements test fixture."""
    return [moa_aid69_statement]


@pytest.fixture(scope='module')
def asst69_propositions(moa_aid69_proposition):
    """Create assertion69 propositions test fixture."""
    return [moa_aid69_proposition]


@pytest.fixture(scope='module')
def asst69_variation_descriptors(moa_vid69):
    """Create assertion69 variation_descriptors test fixture."""
    return [moa_vid69]


@pytest.fixture(scope='module')
def asst69_gene_descriptors(moa_abl1):
    """Create assertion69 gene_descriptors test fixture."""
    return [moa_abl1]


@pytest.fixture(scope='module')
def asst69_therapy_descriptors(moa_imatinib):
    """Create assertion69 therapy_descriptors test fixture."""
    return [moa_imatinib]


@pytest.fixture(scope='module')
def asst69_disease_descriptors(moa_chronic_myelogenous_leukemia):
    """Create assertion69 disease_descriptors test fixture."""
    return [moa_chronic_myelogenous_leukemia]


@pytest.fixture(scope='module')
def asst69_methods(method004):
    """Create assertion69 methods test fixture."""
    return[method004]


@pytest.fixture(scope='module')
def asst69_documents(pmid_11423618):
    """Create assertion69 documents test fixture."""
    return[pmid_11423618]


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        assert test == actual


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(test_data[key]) == set(actual_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        for item in actual_data:
            if isinstance(item, list):
                assert set(test_data) == set(actual_data)
            else:
                assert_non_lists(actual_data, test_data)


def test_moa_cdm(data, asst69_statements, asst69_propositions,
                 asst69_variation_descriptors, asst69_gene_descriptors,
                 asst69_therapy_descriptors, asst69_disease_descriptors,
                 asst69_methods, asst69_documents):
    """Test that moa transform works correctly."""
    assertions(asst69_statements, data['statements'])
    assertions(asst69_propositions, data['propositions'])
    assertions(asst69_variation_descriptors, data['variation_descriptors'])
    assertions(asst69_gene_descriptors, data['gene_descriptors'])
    assertions(asst69_therapy_descriptors, data['therapy_descriptors'])
    assertions(asst69_disease_descriptors, data['disease_descriptors'])
    assertions(asst69_methods, data['methods'])
    assertions(asst69_documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json")
