"""Test CIViC Transformation to common data model for prognostic."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json

DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "prognostic"
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
def statements(civic_eid26_statement, civic_eid1756_statement):
    """Create test fixture for statements."""
    return [civic_eid26_statement, civic_eid1756_statement]


@pytest.fixture(scope="module")
def propositions(civic_eid26_proposition, civic_eid1756_proposition):
    """Create test fixture for proposition."""
    return [civic_eid26_proposition, civic_eid1756_proposition]


@pytest.fixture(scope="module")
def variation_descriptors(civic_vid65, civic_vid258):
    """Create test fixture for variants."""
    return [civic_vid65, civic_vid258]


@pytest.fixture(scope="module")
def disease_descriptors(civic_did3, civic_did556):
    """Create test fixture for disease descriptors."""
    return [civic_did3, civic_did556]


@pytest.fixture(scope="module")
def gene_descriptors(civic_gid29, civic_gid3672):
    """Create test fixture for gene descriptors."""
    return [civic_gid29, civic_gid3672]


@pytest.fixture(scope="module")
def documents(pmid_16384925, pmid_27819322):
    """Create test fixture for documents."""
    return [pmid_16384925, pmid_27819322]


def test_civic_cdm(data, statements, propositions, variation_descriptors,
                   gene_descriptors, disease_descriptors,
                   civic_methods, documents, check_statement,
                   check_proposition, check_variation_descriptor,
                   check_descriptor, check_document, check_method,
                   check_transformed_cdm):
    """Test that civic transform works correctly."""
    check_transformed_cdm(
        data, statements, propositions, variation_descriptors,
        gene_descriptors, disease_descriptors, None,
        civic_methods, documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document,
        check_method, DATA_DIR / FILENAME
    )
