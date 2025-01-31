"""Test MOA Transformation to common data model"""

import pytest
import pytest_asyncio
from tests.conftest import (
    TEST_TRANSFORMERS_DIR,
    get_transformed_data,
    get_vicc_normalizer_failure_ext,
    get_vicc_normalizer_priority_ext,
)

from metakb.transformers.moa import MoaTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "therapeutic"
NORMALIZABLE_FILENAME = "moa_cdm.json"
NOT_NORMALIZABLE_FILE_NAME = "moa_cdm_normalization_failure.json"


@pytest_asyncio.fixture(scope="module")
async def normalizable_data(normalizers):
    """Create a MOA Transformer test fixture."""
    harvester_path = DATA_DIR / "moa_harvester.json"
    return await get_transformed_data(
        MoaTransformer, DATA_DIR, harvester_path, normalizers, NORMALIZABLE_FILENAME
    )


@pytest_asyncio.fixture(scope="module")
async def not_normalizable_data(normalizers):
    """Create a MOA Transformer test fixture for data that cannot be normalized."""
    # NOTE: This file was manually generated to create a fake evidence item
    #       However, it does include some actual moa records that fail to normalize.
    #       Gene record was modified to fail
    harvester_path = DATA_DIR / "moa_harvester_not_normalizable.json"
    return await get_transformed_data(
        MoaTransformer,
        DATA_DIR,
        harvester_path,
        normalizers,
        NOT_NORMALIZABLE_FILE_NAME,
    )


@pytest.fixture(scope="module")
def moa_vid144(braf_v600e_genomic):
    """Create a test fixture for MOA VID144."""
    genomic_rep = braf_v600e_genomic.copy()
    genomic_rep["label"] = "7-140453136-A-T"

    return {
        "id": "moa.variant:144",
        "type": "CategoricalVariant",
        "label": "BRAF p.V600E (Missense)",
        "constraints": [
            {
                "allele": {
                    "id": "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
                    "digest": "j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
                    "type": "Allele",
                    "location": {
                        "id": "ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                        "digest": "t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                        "type": "SequenceLocation",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                        },
                        "start": 599,
                        "end": 600,
                        "sequence": "V",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "E"},
                },
                "type": "DefiningAlleleConstraint",
            }
        ],
        "members": [genomic_rep],
        "extensions": [
            {
                "name": "MOA representative coordinate",
                "value": {
                    "chromosome": "7",
                    "start_position": "140453136",
                    "end_position": "140453136",
                    "reference_allele": "A",
                    "alternate_allele": "T",
                    "cdna_change": "c.1799T>A",
                    "protein_change": "p.V600E",
                    "exon": "15",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "id": "moa.variant:144",
                    "system": "https://moalmanac.org",
                    "code": "144",
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                    "code": "rs113488022",
                },
                "relation": "relatedMatch",
            },
        ],
    }


@pytest.fixture(scope="module")
def moa_cetuximab(cetuximab_extensions, cetuximab_normalizer_mappings):
    """Create a test fixture for MOA Cetuximab"""
    return {
        "id": "moa.normalize.therapy.rxcui:318341",
        "conceptType": "Therapy",
        "label": "Cetuximab",
        "extensions": cetuximab_extensions,
        "mappings": cetuximab_normalizer_mappings,
    }


@pytest.fixture(scope="module")
def moa_encorafenib(encorafenib_extensions, encorafenib_normalizer_mappings):
    """Create test fixture for MOA Encorafenib"""
    return {
        "id": "moa.normalize.therapy.rxcui:2049106",
        "conceptType": "Therapy",
        "label": "Encorafenib",
        "extensions": encorafenib_extensions,
        "mappings": encorafenib_normalizer_mappings,
    }


@pytest.fixture(scope="module")
def moa_aid154_study_stmt(
    moa_vid144,
    moa_cetuximab,
    moa_encorafenib,
    moa_method,
    braf_normalizer_mappings,
):
    """Create MOA AID 154 study statement test fixture. Uses CombinationTherapy."""
    return {
        "id": "moa.assertion:154",
        "type": "Statement",
        "direction": "supports",
        "description": "The U.S. Food and Drug Administration (FDA) granted regular approval to encorafenib in combination with cetuximab for the treatment of adult patients with metastatic colorectal cancer (CRC) with BRAF V600E mutation, as detected by an FDA-approved test, after prior therapy.",
        "strength": {
            "primaryCode": "e000002",
            "label": "FDA recognized evidence",
            "mappings": [
                {
                    "coding": {
                        "id": "vicc:e000002",
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000002",
                        "label": "FDA recognized evidence",
                    },
                    "relation": "exactMatch",
                },
                {
                    "coding": {
                        "id": "moa.assertion_level:fda_approved",
                        "system": "https://moalmanac.org/about",
                        "code": "FDA-Approved",
                    },
                    "relation": "exactMatch",
                },
            ],
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "subjectVariant": moa_vid144,
            "objectTherapeutic": {
                "groupType": {"label": "CombinationTherapy"},
                "id": "moa.ctid:ZGlEkRBR4st6Y_nijjuR1KUV7EFHIF_S",
                "therapies": [moa_cetuximab, moa_encorafenib],
                "extensions": [
                    {
                        "name": "moa_therapy_type",
                        "value": "Targeted therapy",
                    }
                ],
            },
            "conditionQualifier": {
                "id": "moa.normalize.disease.ncit:C5105",
                "conceptType": "Disease",
                "label": "Colorectal Adenocarcinoma",
                "mappings": [
                    {
                        "coding": {
                            "label": "Colorectal Adenocarcinoma",
                            "system": "https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                            "code": "COADREAD",
                            "id": "oncotree:COADREAD",
                        },
                        "relation": "exactMatch",
                    },
                    {
                        "coding": {
                            "label": "Colorectal Adenocarcinoma",
                            "code": "ncit:C5105",
                            "system": "http://purl.obolibrary.org/obo/ncit.owl",
                        },
                        "relation": "exactMatch",
                        "extensions": get_vicc_normalizer_priority_ext(
                            is_priority=True
                        ),
                    },
                    {
                        "coding": {
                            "code": "mondo:0005008",
                            "system": "http://purl.obolibrary.org/obo/mondo.owl",
                        },
                        "relation": "relatedMatch",
                        "extensions": get_vicc_normalizer_priority_ext(
                            is_priority=False
                        ),
                    },
                ],
            },
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": {
                "id": "moa.normalize.gene.hgnc:1097",
                "conceptType": "Gene",
                "label": "BRAF",
                "mappings": braf_normalizer_mappings,
            },
        },
        "specifiedBy": moa_method,
        "reportedIn": [
            {
                "id": "moa.source:64",
                "extensions": [{"name": "source_type", "value": "FDA"}],
                "type": "Document",
                "title": "Array BioPharma Inc. Braftovi (encorafenib) [package insert]. U.S. Food and Drug Administration website. www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf. Revised April 2020. Accessed October 15, 2020.",
                "urls": [
                    "https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf"
                ],
            }
        ],
    }


@pytest.fixture(scope="session")
def moa_vid21_modified():
    """Create a test fixture for MOA VID21 which has been modified to fail"""
    return {
        "id": "moa.variant:21",
        "type": "CategoricalVariant",
        "label": "FakeGene Translocation",
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {"name": "MOA locus", "value": "t(6;14)"},
        ],
        "mappings": [
            {
                "coding": {
                    "id": "moa.variant:21",
                    "system": "https://moalmanac.org",
                    "code": "21",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="session")
def moa_mito_cp():
    """Create a test fixture for MOA Imatinib Therapy."""
    return {
        "id": "moa.therapy:Mito-CP",
        "conceptType": "Therapy",
        "label": "Mito-CP",
        "extensions": [get_vicc_normalizer_failure_ext()],
    }


@pytest.fixture(scope="session")
def moa_t_cell_acute_lymphoid_leukemia():
    """Create test fixture for MOA T-Cell Acute Lymphoid Leukemia."""
    return {
        "id": "moa.disease:T-Cell_Acute_Lymphoid_Leukemia",
        "conceptType": "Disease",
        "label": "T-Cell Acute Lymphoid Leukemia",
        "extensions": [get_vicc_normalizer_failure_ext()],
        "mappings": [
            {
                "coding": {
                    "id": "oncotree:TALL",
                    "label": "T-Cell Acute Lymphoid Leukemia",
                    "system": "https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                    "code": "TALL",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_fake_gene():
    """Create a test fixture for a fake gene in MOA."""
    return {
        "id": "moa.gene:FakeGene",
        "conceptType": "Gene",
        "label": "FakeGene",
        "extensions": [get_vicc_normalizer_failure_ext()],
    }


@pytest.fixture(scope="module")
def moa_not_normalizable_stmt(
    moa_vid21_modified,
    moa_fake_gene,
    moa_mito_cp,
    moa_t_cell_acute_lymphoid_leukemia,
    moa_method,
    moa_source45,
):
    """Create test fixture for fake moa statement that fails to normalize gene,
    variant, disease, and therapy.
    """
    return {
        "id": "moa.assertion:123456789",
        "description": "This is a fake assertion item.",
        "strength": {
            "primaryCode": "e000009",
            "label": "preclinical evidence",
            "mappings": [
                {
                    "coding": {
                        "id": "vicc:e000009",
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000009",
                        "label": "preclinical evidence",
                    },
                    "relation": "exactMatch",
                },
                {
                    "coding": {
                        "id": "civic.evidence_level:D",
                        "system": "https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                        "code": "D",
                    },
                    "relation": "exactMatch",
                },
                {
                    "coding": {
                        "id": "moa.assertion_level:preclinical_evidence",
                        "system": "https://moalmanac.org/about",
                        "code": "Preclinical evidence",
                    },
                    "relation": "exactMatch",
                },
            ],
        },
        "direction": "supports",
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "subjectVariant": moa_vid21_modified,
            "objectTherapeutic": moa_mito_cp,
            "conditionQualifier": moa_t_cell_acute_lymphoid_leukemia,
            # "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": moa_fake_gene,
        },
        "specifiedBy": moa_method,
        "reportedIn": [moa_source45],
        "type": "Statement",
    }


@pytest.fixture(scope="module")
def statements(moa_aid66_study_stmt, moa_aid154_study_stmt):
    """Create test fixture for MOA therapeutic statements."""
    return [moa_aid66_study_stmt, moa_aid154_study_stmt]


def test_moa_cdm(normalizable_data, statements, check_transformed_cdm):
    """Test that moa transformation works correctly."""
    check_transformed_cdm(
        normalizable_data, statements, DATA_DIR / NORMALIZABLE_FILENAME
    )


def test_moa_cdm_not_normalizable(
    not_normalizable_data, moa_not_normalizable_stmt, check_transformed_cdm
):
    """Test that moa transformation works correctly for MOA records that cannot
    normalize (gene, disease, variant, and therapy)
    """
    check_transformed_cdm(
        not_normalizable_data,
        [moa_not_normalizable_stmt],
        DATA_DIR / NOT_NORMALIZABLE_FILE_NAME,
    )
