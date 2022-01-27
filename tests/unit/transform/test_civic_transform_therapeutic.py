"""Test CIViC Transformation to common data model for Therapeutic Response."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic"
FILENAME = "civic_cdm.json"


@pytest.fixture(scope="module")
def data():
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CIViCTransform(data_dir=DATA_DIR, harvester_path=harvester_path)
    c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def statements(civic_eid2997_statement, civic_aid6_statement):
    """Create test fixture for statements."""
    return [civic_eid2997_statement, civic_aid6_statement]


@pytest.fixture(scope="module")
def propositions(civic_eid2997_proposition):
    """Create test fixture for proposition."""
    return [civic_eid2997_proposition]


@pytest.fixture(scope="module")
def variation_descriptors(civic_vid33):
    """Create test fixture for variants."""
    return [civic_vid33]


@pytest.fixture(scope="module")
def therapy_descriptors(civic_tid146):
    """Create test fixture for therapy descriptors."""
    return [civic_tid146]


@pytest.fixture(scope="module")
def disease_descriptors(civic_did8):
    """Create test fixture for disease descriptors."""
    return [civic_did8]


@pytest.fixture(scope="module")
def gene_descriptors(civic_gid19):
    """Create test fixture for gene descriptors."""
    return [civic_gid19]


@pytest.fixture(scope="module")
def documents(pmid_23982599, civic_aid6_document):
    """Create test fixture for documents."""
    return [pmid_23982599, civic_aid6_document]


def test_civic_cdm(data, statements, propositions, variation_descriptors,
                   gene_descriptors, disease_descriptors, therapy_descriptors,
                   civic_methods, documents, check_statement,
                   check_proposition, check_variation_descriptor,
                   check_descriptor, check_document, check_method,
                   check_transformed_cdm):
    """Test that civic transform works correctly."""
    check_transformed_cdm(
        data, statements, propositions, variation_descriptors,
        gene_descriptors, disease_descriptors, therapy_descriptors,
        civic_methods, documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document,
        check_method, DATA_DIR / FILENAME
    )
