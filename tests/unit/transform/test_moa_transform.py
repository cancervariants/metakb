"""Test MOA Transformation to common data model"""
import pytest
from metakb.transform.moa import MOATransform
from metakb import PROJECT_ROOT
import json


TRANSFORMED_FILE = f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json"


@pytest.fixture(scope='module')
def data():
    """Create a MOA Transform test fixture."""
    moa = MOATransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/moa_harvester.json")
    moa.transform()
    moa._create_json(moa_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform')
    with open(TRANSFORMED_FILE, 'r') as f:
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


def test_moa_cdm(data, asst69_statements, asst69_propositions,
                 asst69_variation_descriptors, asst69_gene_descriptors,
                 asst69_disease_descriptors, asst69_therapy_descriptors,
                 asst69_methods, asst69_documents, check_statement,
                 check_proposition, check_variation_descriptor,
                 check_descriptor, check_document, check_method,
                 check_transformed_cdm):
    """Test that moa transform works correctly."""
    check_transformed_cdm(
        data, asst69_statements, asst69_propositions,
        asst69_variation_descriptors, asst69_gene_descriptors,
        asst69_disease_descriptors, asst69_therapy_descriptors, asst69_methods,
        asst69_documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document,
        check_method, TRANSFORMED_FILE
    )
