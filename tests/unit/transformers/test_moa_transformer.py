"""Test MOA Transformation to common data model"""

import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORMERS_DIR

from metakb.normalizers import VICC_NORMALIZER_DATA
from metakb.transformers.moa import MoaTransformer

FILENAME = "moa_cdm.json"


@pytest_asyncio.fixture(scope="module")
async def data(normalizers):
    """Create a MOA Transformer test fixture."""
    harvester_path = TEST_TRANSFORMERS_DIR / "moa_harvester.json"
    moa = MoaTransformer(
        data_dir=TEST_TRANSFORMERS_DIR,
        harvester_path=harvester_path,
        normalizers=normalizers,
    )
    harvested_data = moa.extract_harvested_data()
    await moa.transform(harvested_data)
    moa.create_json(cdm_filepath=TEST_TRANSFORMERS_DIR / FILENAME)
    with (TEST_TRANSFORMERS_DIR / FILENAME).open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def moa_vid145(braf_v600e_genomic):
    """Create a test fixture for MOA VID145."""
    genomic_rep = braf_v600e_genomic.copy()
    genomic_rep["label"] = "7-140453136-A-T"

    return {
        "id": "moa.variant:145",
        "type": "CategoricalVariant",
        "label": "BRAF p.V600E (Missense)",
        "constraints": [
            {
                "definingContext": {
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
                "type": "DefiningContextConstraint",
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
                    "system": "https://moalmanac.org/api/features/",
                    "code": "145",
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
        "type": "TherapeuticAgent",
        "label": "Cetuximab",
        "extensions": cetuximab_extensions,
    }


@pytest.fixture(scope="module")
def moa_encorafenib(encorafenib_extensions):
    """Create test fixture for MOA Encorafenib"""
    return {
        "id": "moa.normalize.therapy.rxcui:2049106",
        "type": "TherapeuticAgent",
        "label": "Encorafenib",
        "extensions": encorafenib_extensions,
    }


@pytest.fixture(scope="module")
def moa_aid155_study(moa_vid145, moa_cetuximab, moa_encorafenib, moa_method):
    """Create MOA AID 155 study test fixture. Uses CombinationTherapy."""
    return {
        "id": "moa.assertion:155",
        "type": "VariantTherapeuticResponseStudyStatement",
        "description": "The U.S. Food and Drug Administration (FDA) granted regular approval to encorafenib in combination with cetuximab for the treatment of adult patients with metastatic colorectal cancer (CRC) with BRAF V600E mutation, as detected by an FDA-approved test, after prior therapy.",
        "strength": {
            "code": "e000002",
            "label": "FDA recognized evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "predictsSensitivityTo",
        "subjectVariant": moa_vid145,
        "objectTherapeutic": {
            "type": "CombinationTherapy",
            "id": "moa.ctid:ZGlEkRBR4st6Y_nijjuR1KUV7EFHIF_S",
            "components": [moa_cetuximab, moa_encorafenib],
            "extensions": [
                {
                    "name": "moa_therapy_type",
                    "value": "Targeted therapy",
                }
            ],
        },
        "conditionQualifier": {
            "id": "moa.normalize.disease.ncit:C5105",
            "type": "Disease",
            "label": "Colorectal Adenocarcinoma",
            "extensions": [
                {
                    "name": VICC_NORMALIZER_DATA,
                    "value": {
                        "id": "ncit:C5105",
                        "label": "Colorectal Adenocarcinoma",
                        "mondo_id": "0005008",
                    },
                }
            ],
            "mappings": [
                {
                    "coding": {
                        "label": "Colorectal Adenocarcinoma",
                        "system": "https://oncotree.mskcc.org/",
                        "code": "COADREAD",
                    },
                    "relation": "exactMatch",
                }
            ],
        },
        "alleleOriginQualifier": "somatic",
        "geneContextQualifier": {
            "id": "moa.normalize.gene:BRAF",
            "type": "Gene",
            "label": "BRAF",
            "extensions": [
                {
                    "name": VICC_NORMALIZER_DATA,
                    "value": {"id": "hgnc:1097", "label": "BRAF"},
                }
            ],
        },
        "specifiedBy": moa_method,
        "reportedIn": [
            {
                "id": "moa.source:63",
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
def studies(moa_aid66_study, moa_aid155_study):
    """Create test fixture for MOA therapeutic studies."""
    return [moa_aid66_study, moa_aid155_study]


def test_moa_cdm(data, studies, check_transformed_cdm):
    """Test that moa transformation works correctly."""
    check_transformed_cdm(data, studies, TEST_TRANSFORMERS_DIR / FILENAME)
