"""Test CIViC Transformation to common data model for prognostic."""
import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORM_DIR

from metakb.transform.civic import CivicTransform

DATA_DIR = TEST_TRANSFORM_DIR / "prognostic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio()
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransform(
        data_dir=DATA_DIR, harvester_path=harvester_path, normalizers=normalizers
    )
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with (DATA_DIR / FILENAME).open() as f:
        return json.load(f)


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


@pytest.mark.skip(reason="Will be resolved in issue-242")
def test_civic_cdm(
    data,
    statements,
    propositions,
    variation_descriptors,
    gene_descriptors,
    disease_descriptors,
    civic_methods,
    documents,
    check_statement,
    check_proposition,
    check_variation_descriptor,
    check_descriptor,
    check_document,
    check_method,
    check_transformed_cdm,
):
    """Test that civic transform works correctly."""
    check_transformed_cdm(
        data,
        statements,
        propositions,
        variation_descriptors,
        gene_descriptors,
        disease_descriptors,
        None,
        civic_methods,
        documents,
        check_statement,
        check_proposition,
        check_variation_descriptor,
        check_descriptor,
        check_document,
        check_method,
        DATA_DIR / FILENAME,
    )
