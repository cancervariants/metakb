"""Test CIViC Transformation to common data model for Therapeutic Response."""

import pytest
import pytest_asyncio
from tests.conftest import (
    TEST_TRANSFORMERS_DIR,
    get_transformed_data,
    get_vicc_normalizer_failure_ext,
)

from metakb.transformers.civic import CivicTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "therapeutic"
NORMALIZABLE_FILENAME = "civic_cdm.json"
NOT_NORMALIZABLE_FILE_NAME = "civic_cdm_normalization_failure.json"


@pytest_asyncio.fixture(scope="module")
async def normalizable_data(normalizers):
    """Create a CIViC Transformer test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    return await get_transformed_data(
        CivicTransformer, DATA_DIR, harvester_path, normalizers, NORMALIZABLE_FILENAME
    )


@pytest_asyncio.fixture(scope="module")
async def not_normalizable_data(normalizers):
    """Create a CIViC Transformer test fixture for data that cannot be normalized."""
    # NOTE: This file was manually generated to create a fake evidence item
    #       However, it does include some actual civic records that fail to normalize
    #       Gene record was modified to fail
    harvester_path = DATA_DIR / "civic_harvester_not_normalizable.json"
    return await get_transformed_data(
        CivicTransformer,
        DATA_DIR,
        harvester_path,
        normalizers,
        NOT_NORMALIZABLE_FILE_NAME,
    )


@pytest.fixture(scope="module")
def statements(
    civic_eid2997_study_stmt,
    civic_eid816_study_stmt,
    civic_eid9851_study_stmt,
    civic_aid6_statement,
):
    """Create test fixture for CIViC therapeutic statements."""
    return [
        civic_eid2997_study_stmt,
        civic_eid816_study_stmt,
        civic_eid9851_study_stmt,
        civic_aid6_statement,
    ]


@pytest.fixture(scope="module")
def civic_tid579():
    """Create test fixture for CIViC therapy ID 579"""
    return {
        "id": "civic.tid:579",
        "conceptType": "Therapy",
        "name": "FOLFOX Regimen",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C11197",
                    "code": "C11197",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "aliases",
                "value": [
                    "CF/5-FU/L-OHP",
                    "FOLFOX",
                    "Fluorouracil/Leucovorin Calcium/Oxaliplatin",
                ],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_did3433():
    """Create test fixture for CIViC DID3433."""
    return {
        "id": "civic.did:3433",
        "conceptType": "Disease",
        "name": "B-lymphoblastic Leukemia/lymphoma With PAX5 P80R",
        "extensions": [
            get_vicc_normalizer_failure_ext(),
        ],
    }


@pytest.fixture(scope="session")
def civic_gid6_modified():
    """Create test fixture for CIViC GID6, which has been modified to fail normalization."""
    return {
        "id": "civic.gid:6",
        "conceptType": "Gene",
        "name": "BRCA1. This should fail normalization.",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:0",
                    "code": "0",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "description",
                "value": "This is a fake gene that fails normalization.",
            },
            {
                "name": "aliases",
                "value": ["Fake alias 1", "Fake alias 2"],
            },
        ],
    }


@pytest.fixture(scope="module")
def civic_mpid473():
    """Create CIViC MPID 473"""
    return {
        "id": "civic.mpid:473",
        "type": "CategoricalVariant",
        "name": "BRCA1 P968FS",
        "mappings": [
            {
                "coding": {
                    "code": "CA001889",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "91602",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs398122670",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:477",
                    "code": "477",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "aliases": [
            "3021INSTC",
            "PRO968LEUFS",
        ],
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "17",
                    "start": 41244645,
                    "stop": 41244646,
                    "variant_bases": "GA",
                    "representative_transcript": "ENST00000471181.2",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 20.0,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001910",
                        "code": "SO:0001910",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "name": "frameshift_truncation",
                    }
                ],
            },
            {
                "name": "expressions",
                "value": [
                    {"syntax": "hgvs.c", "value": "NM_007294.3:c.2902_2903insTC"},
                    {"syntax": "hgvs.p", "value": "NP_009225.1:p.Pro968Leufs"},
                    {
                        "syntax": "hgvs.g",
                        "value": "NC_000017.10:g.41244645_41244646insGA",
                    },
                    {"syntax": "hgvs.c", "value": "ENST00000471181.2:c.2902_2903insTC"},
                ],
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_source123456789():
    """Create fixture for a fake civic source 123456789"""
    return {
        "id": "civic.source:123456789",
        "name": "John Doe et al., 2022",
        "title": "My fake civic source",
        "pmid": 123456789,
        "type": "Document",
    }


@pytest.fixture(scope="module")
def civic_not_normalizable_stmt(
    civic_tid579,
    civic_did3433,
    civic_gid6_modified,
    civic_mpid473,
    civic_method,
    civic_source123456789,
):
    """Create test fixture for fake civic statement that fails to normalize gene,
    variant, disease, and therapy.
    """
    return {
        "id": "civic.eid:123456789",
        "type": "Statement",
        "description": "This is a fake evidence item.",
        "direction": "supports",
        "strength": {
            "name": "Validated association",
            "primaryCoding": {
                "system": "https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                "code": "A",
            },
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000001",
                        "name": "authoritative evidence",
                    },
                    "relation": "exactMatch",
                }
            ],
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "objectTherapeutic": civic_tid579,
            "conditionQualifier": civic_did3433,
            "alleleOriginQualifier": {"name": "somatic"},
            "geneContextQualifier": civic_gid6_modified,
            "subjectVariant": civic_mpid473,
        },
        "specifiedBy": civic_method,
        "reportedIn": [civic_source123456789],
    }


def test_civic_cdm(normalizable_data, statements, check_transformed_cdm):
    """Test that civic transformation works correctly."""
    check_transformed_cdm(
        normalizable_data, statements, DATA_DIR / NORMALIZABLE_FILENAME
    )


def test_civic_cdm_not_normalizable(
    not_normalizable_data, civic_not_normalizable_stmt, check_transformed_cdm
):
    """Test that civic transformation works correctly for CIViC records that cannot
    normalize (gene, disease, variant, and therapy)
    """
    check_transformed_cdm(
        not_normalizable_data,
        [civic_not_normalizable_stmt],
        DATA_DIR / NOT_NORMALIZABLE_FILE_NAME,
    )
