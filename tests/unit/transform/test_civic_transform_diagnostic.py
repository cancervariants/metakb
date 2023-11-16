"""Test CIViC Transformation to common data model for prognostic."""
import pytest
import pytest_asyncio
from metakb.transform.civic import CivicTransform
from metakb import PROJECT_ROOT
import json

DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "diagnostic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def statements(civic_eid2_statement, civic_eid74_statement,
               civic_aid9_statement):
    """Create test fixture for statements."""
    return [civic_eid2_statement, civic_eid74_statement, civic_aid9_statement]


@pytest.fixture(scope="module")
def propositions(civic_eid2_proposition, civic_eid74_proposition,
                 civic_aid9_proposition):
    """Create test fixture for proposition."""
    return [
        civic_eid2_proposition, civic_eid74_proposition, civic_aid9_proposition
    ]


@pytest.fixture(scope="module")
def variation_descriptors(civic_vid99, civic_vid113, civic_vid1686):
    """Create test fixture for variants."""
    return [civic_vid99, civic_vid113, civic_vid1686]


@pytest.fixture(scope="module")
def disease_descriptors(civic_did2, civic_did15, civic_did2950):
    """Create test fixture for disease descriptors."""
    return [civic_did2, civic_did15, civic_did2950]


@pytest.fixture(scope="module")
def gene_descriptors(civic_gid38, civic_gid42, civic_gid154):
    """Create test fixture for gene descriptors."""
    return [civic_gid38, civic_gid42, civic_gid154]


@pytest.fixture(scope="module")
def documents(pmid_15146165, pmid_18073307):
    """Create test fixture for documents."""
    return [pmid_15146165, pmid_18073307]


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
