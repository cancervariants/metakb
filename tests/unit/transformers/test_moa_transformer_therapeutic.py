"""Test MOA Transformation to common data model"""

import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORMERS_DIR

from metakb.normalizers import VICC_NORMALIZER_DATA
from metakb.transformers.moa import MoaTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "therapeutic"
FILENAME = "moa_cdm.json"


@pytest_asyncio.fixture(scope="module")
async def data(normalizers):
    """Create a MOA Transformer test fixture."""
    harvester_path = DATA_DIR / "moa_harvester.json"
    moa = MoaTransformer(
        data_dir=DATA_DIR,
        harvester_path=harvester_path,
        normalizers=normalizers,
    )
    harvested_data = moa.extract_harvested_data()
    await moa.transform(harvested_data)
    moa.create_json(cdm_filepath=DATA_DIR / FILENAME)
    with (DATA_DIR / FILENAME).open() as f:
        return json.load(f)


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
def moa_cetuximab(cetuximab_extensions):
    """Create a test fixture for MOA Cetuximab"""
    return {
        "id": "moa.normalize.therapy.rxcui:318341",
        "conceptType": "Therapy",
        "label": "Cetuximab",
        "extensions": cetuximab_extensions,
    }


@pytest.fixture(scope="module")
def moa_encorafenib(encorafenib_extensions):
    """Create test fixture for MOA Encorafenib"""
    return {
        "id": "moa.normalize.therapy.rxcui:2049106",
        "conceptType": "Therapy",
        "label": "Encorafenib",
        "extensions": encorafenib_extensions,
    }


@pytest.fixture(scope="module")
def moa_aid154_study_stmt(moa_vid144, moa_cetuximab, moa_encorafenib, moa_method):
    """Create MOA AID 154 study statement test fixture. Uses CombinationTherapy."""
    return {
        "id": "moa.assertion:154",
        "type": "Statement",
        "direction": "supports",
        "description": "The U.S. Food and Drug Administration (FDA) granted regular approval to encorafenib in combination with cetuximab for the treatment of adult patients with metastatic colorectal cancer (CRC) with BRAF V600E mutation, as detected by an FDA-approved test, after prior therapy.",
        "strength": {
            "conceptType": "Evidence Strength",
            "primaryCode": "e000002",
            "label": "FDA recognized evidence",
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000002",
                    },
                    "relation": "exactMatch",
                },
                {
                    "coding": {
                        "system": "MOA",
                        "code": "moa.evidence_level:fda_approved",
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
                "extensions": [
                    {
                        "name": VICC_NORMALIZER_DATA,
                        "value": {
                            "id": "ncit:C5105",
                            "label": "Colorectal Adenocarcinoma",
                            "mondo_id": "mondo:0005008",
                        },
                    }
                ],
                "mappings": [
                    {
                        "coding": {
                            "label": "Colorectal Adenocarcinoma",
                            "system": "https://oncotree.mskcc.org",
                            "code": "COADREAD",
                        },
                        "relation": "exactMatch",
                    }
                ],
            },
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": {
                "id": "moa.normalize.gene:BRAF",
                "conceptType": "Gene",
                "label": "BRAF",
                "extensions": [
                    {
                        "name": VICC_NORMALIZER_DATA,
                        "value": {"id": "hgnc:1097", "label": "BRAF"},
                    }
                ],
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


@pytest.fixture(scope="module")
def statements(moa_aid66_study_stmt, moa_aid154_study_stmt):
    """Create test fixture for MOA therapeutic statements."""
    return [moa_aid66_study_stmt, moa_aid154_study_stmt]


def test_moa_cdm(data, statements, check_transformed_cdm):
    """Test that moa transformation works correctly."""
    check_transformed_cdm(data, statements, DATA_DIR / FILENAME)
