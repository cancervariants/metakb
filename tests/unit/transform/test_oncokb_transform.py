"""Test OncoKB Transformation to common data model

Test data uses public OncoKB API: https://demo.oncokb.org/api
"""
import json

import pytest
import pytest_asyncio

from metakb.transform.oncokb import OncoKBTransform
from metakb import PROJECT_ROOT


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform"
FILENAME = "oncokb_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a OncoKB Transform test fixture."""
    harvester_path = DATA_DIR / "oncokb_harvester.json"
    o = OncoKBTransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                        normalizers=normalizers)
    await o.transform()
    o.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def oncokb_statements(oncokb_diagnostic_statement1, oncokb_therapeutic_statement1):
    """Create OncoKB statements test fixture"""
    return [oncokb_diagnostic_statement1, oncokb_therapeutic_statement1]


@pytest.fixture(scope="module")
def oncokb_propositions(oncokb_diagnostic_proposition1,
                        oncokb_therapeutic_proposition1):
    """Create OncoKB propositions test fixture"""
    return [oncokb_diagnostic_proposition1, oncokb_therapeutic_proposition1]


@pytest.fixture(scope="module")
def oncokb_therapy_descriptors(oncokb_trametinib_therapy_descriptor):
    """Create OncoKB therapy descriptors test fixture"""
    return [oncokb_trametinib_therapy_descriptor]


@pytest.fixture(scope="module")
def oncokb_gene_descriptors(oncokb_braf_gene_descriptor):
    """Create OncoKB gene descriptors test fixture"""
    return [oncokb_braf_gene_descriptor]


@pytest.fixture(scope="module")
def oncokb_variation_descriptors(oncokb_braf_v600e_vd):
    """Create OncoKB variation descriptors test fixture"""
    return [oncokb_braf_v600e_vd]


@pytest.fixture(scope="module")
def oncokb_disease_descriptors(oncokb_ecd_disease_descriptor,
                               oncokb_mel_disease_descriptor):
    """Create OncoKB disease descriptors test fixture"""
    return [oncokb_ecd_disease_descriptor, oncokb_mel_disease_descriptor]


@pytest.fixture(scope="module")
def oncokb_methods(oncokb_method):
    """Create OncoKB methods test fixture"""
    return [oncokb_method]


@pytest.fixture(scope="module")
def oncokb_therapeutic1_documents():
    """Create test fixture for OncoKB therapeutic evidence 1 documents"""
    return [
        {
            "id": "pmid:29361468",
            "label": "PubMed 29361468",
            "type": "Document"
        },
        {
            "id": "pmid:25399551",
            "label": "PubMed 25399551",
            "type": "Document"
        },
        {
            "id": "pmid:22663011",
            "label": "PubMed 22663011",
            "type": "Document"
        },
        {
            "id": "pmid:25265492",
            "label": "PubMed 25265492",
            "type": "Document"
        }
    ]


@pytest.fixture(scope="module")
def oncokb_documents(oncokb_diagnostic1_documents, oncokb_therapeutic1_documents):
    """Create OncoKB Documents test fixture"""
    return oncokb_diagnostic1_documents + oncokb_therapeutic1_documents


def test_oncokb_transform(
    data, oncokb_statements, oncokb_propositions, oncokb_variation_descriptors,
    oncokb_gene_descriptors, oncokb_disease_descriptors, oncokb_therapy_descriptors,
    oncokb_methods, oncokb_documents, check_statement, check_proposition,
    check_variation_descriptor, check_descriptor, check_document, check_method,
    check_transformed_cdm
):
    """Test that OncoKB transform works correctly"""
    check_transformed_cdm(
        data, oncokb_statements, oncokb_propositions, oncokb_variation_descriptors,
        oncokb_gene_descriptors, oncokb_disease_descriptors, oncokb_therapy_descriptors,
        oncokb_methods, oncokb_documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document, check_method,
        DATA_DIR / FILENAME
    )
