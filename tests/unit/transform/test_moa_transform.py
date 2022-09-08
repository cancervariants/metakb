"""Test MOA Transformation to common data model"""
import pytest
import pytest_asyncio
from metakb.transform.moa import MOATransform
from metakb import PROJECT_ROOT
import json

DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform"
FILENAME = "moa_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a MOA Transform test fixture."""
    harvester_path = DATA_DIR / "therapeutic" / "moa_harvester.json"
    moa = MOATransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await moa.transform()
    moa.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def asst71_statements(moa_aid71_statement):
    """Create assertion71 statements test fixture."""
    return [moa_aid71_statement]


@pytest.fixture(scope="module")
def asst71_propositions(moa_aid71_proposition):
    """Create assertion71 propositions test fixture."""
    return [moa_aid71_proposition]


@pytest.fixture(scope="module")
def asst71_variation_descriptors(moa_vid71):
    """Create assertion71 variation_descriptors test fixture."""
    return [moa_vid71]


@pytest.fixture(scope="module")
def asst71_gene_descriptors(moa_abl1):
    """Create assertion71 gene_descriptors test fixture."""
    return [moa_abl1]


@pytest.fixture(scope="module")
def asst71_therapy_descriptors(moa_imatinib):
    """Create assertion71 therapy_descriptors test fixture."""
    return [moa_imatinib]


@pytest.fixture(scope="module")
def asst71_disease_descriptors(moa_chronic_myelogenous_leukemia):
    """Create assertion71 disease_descriptors test fixture."""
    return [moa_chronic_myelogenous_leukemia]


@pytest.fixture(scope="module")
def asst71_methods(method4):
    """Create assertion71 methods test fixture."""
    return [method4]


@pytest.fixture(scope="module")
def asst71_documents(pmid_11423618):
    """Create assertion71 documents test fixture."""
    return [pmid_11423618]


def test_moa_cdm(data, asst71_statements, asst71_propositions,
                 asst71_variation_descriptors, asst71_gene_descriptors,
                 asst71_disease_descriptors, asst71_methods, asst71_documents,
                 check_statement, check_proposition, check_variation_descriptor,
                 check_descriptor, check_document, check_method,
                 asst71_therapy_descriptors, check_transformed_cdm):
    """Test that moa transform works correctly."""
    check_transformed_cdm(
        data, asst71_statements, asst71_propositions, asst71_variation_descriptors,
        asst71_gene_descriptors, asst71_disease_descriptors, asst71_methods,
        asst71_documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document,
        check_method, DATA_DIR / FILENAME,
        therapeutic_descriptors=asst71_therapy_descriptors
    )
