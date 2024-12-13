"""Test MOA Transformation to common data model"""

import json

import pytest
import pytest_asyncio
from tests.conftest import TEST_TRANSFORMERS_DIR

from metakb.normalizers import VICC_NORMALIZER_DATA
from metakb.transformers.moa import MoaTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "prognostic"
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
def moa_vid141():
    """Create a test fixture for MOA VID141."""
    return {
        "id": "moa.variant:141",
        "type": "CategoricalVariant",
        "label": "BCOR p.N1425S (Missense)",
        "constraints": [
            {
                "definingContext": {
                    "id": "ga4gh:VA.pDuCLNI3mHF25uUPNSDM8LbP8p4Fsuay",
                    "digest": "pDuCLNI3mHF25uUPNSDM8LbP8p4Fsuay",
                    "type": "Allele",
                    "location": {
                        "id": "ga4gh:SL.XiatLUYcK0JzC_CROMV55bbJ_weygAkP",
                        "digest": "XiatLUYcK0JzC_CROMV55bbJ_weygAkP",
                        "type": "SequenceLocation",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.VHPiWlNXV-23rh_9w2KR2PLqPd7OSKMS",
                        },
                        "start": 1458,
                        "end": 1459,
                        "sequence": "N",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "S"},
                },
                "type": "DefiningContextConstraint",
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.e84USp97bhTBu8IC3wsm7nF8_GXU7Yk2",
                "type": "Allele",
                "label": "X-39921444-T-C",
                "digest": "e84USp97bhTBu8IC3wsm7nF8_GXU7Yk2",
                "location": {
                    "id": "ga4gh:SL.6k6-KBncHr2M-nwSTTOLNYbUN5XsMmpB",
                    "type": "SequenceLocation",
                    "digest": "6k6-KBncHr2M-nwSTTOLNYbUN5XsMmpB",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.w0WZEvgJF0zf_P4yyTzjjv9oW1z61HHP",
                    },
                    "start": 40062190,
                    "end": 40062191,
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "C"},
            }
        ],
        "extensions": [
            {
                "name": "MOA representative coordinate",
                "value": {
                    "chromosome": "X",
                    "start_position": "39921444",
                    "end_position": "39921444",
                    "reference_allele": "T",
                    "alternate_allele": "C",
                    "cdna_change": "c.4376A>G",
                    "protein_change": "p.N1425S",
                    "exon": "10",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "system": "https://moalmanac.org/api/features/",
                    "code": "141",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_myelodysplasia():
    """Create test fixture for MOA disease Myelodysplasia"""
    return {
        "id": "moa.normalize.disease.ncit:C3247",
        "type": "Disease",
        "label": "Myelodysplasia",
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "ncit:C3247",
                    "label": "Myelodysplastic Syndrome",
                    "mondo_id": "0018881",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "label": "Myelodysplasia",
                    "system": "https://oncotree.mskcc.org/",
                    "code": "MDS",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_bcor():
    """Create MOA gene BCOR test fixture"""
    return {
        "id": "moa.normalize.gene:BCOR",
        "type": "Gene",
        "label": "BCOR",
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {"id": "hgnc:20893", "label": "BCOR"},
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_source60():
    """Create MOA source ID 60 test fixture"""
    return {
        "id": "moa.source:60",
        "extensions": [{"name": "source_type", "value": "Journal"}],
        "type": "Document",
        "title": "O'Brien C, Wallin JJ, Sampath D, et al. Predictive biomarkers of sensitivity to the phosphatidylinositol 3' kinase inhibitor GDC-0941 in breast cancer preclinical models. Clin Cancer Res. 2010;16(14):3670-83.",
        "urls": ["https://doi.org/10.1158/1078-0432.CCR-09-2828"],
        "doi": "10.1158/1078-0432.CCR-09-2828",
        "pmid": 20453058,
    }


@pytest.fixture(scope="module")
def moa_aid141_study_stmt(
    moa_vid141, moa_myelodysplasia, moa_bcor, moa_source60, moa_method
):
    """Create MOA AID 141 study statement test fixture."""
    return {
        "id": "moa.assertion:141",
        "type": "VariantPrognosticStudyStatement",
        "description": "More frequent in Chronic Myelomonocytic Leukemia.",
        "strength": {
            "code": "e000007",
            "label": "observational study evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "associatedWithWorseOutcomeFor",
        "subjectVariant": moa_vid141,
        "objectCondition": moa_myelodysplasia,
        "alleleOriginQualifier": "somatic",
        "geneContextQualifier": moa_bcor,
        "specifiedBy": moa_method,
        "reportedIn": [moa_source60],
    }


@pytest.fixture(scope="module")
def moa_vid532():
    """Create a test fixture for MOA VID532."""
    return {
        "id": "moa.variant:532",
        "type": "CategoricalVariant",
        "label": "SF3B1 p.E622D (Missense)",
        "constraints": [
            {
                "definingContext": {
                    "id": "ga4gh:VA.53EXGCEm1KH4W4ygbovgD_fFWskECrAJ",
                    "digest": "53EXGCEm1KH4W4ygbovgD_fFWskECrAJ",
                    "type": "Allele",
                    "location": {
                        "id": "ga4gh:SL.PvDvUEPg69q4PYBxC8jM4cEzQCCkaxHM",
                        "digest": "PvDvUEPg69q4PYBxC8jM4cEzQCCkaxHM",
                        "type": "SequenceLocation",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.ST8-pVpExi5fmcLBZ_vHcVmMtvgggIJm",
                        },
                        "start": 621,
                        "end": 622,
                        "sequence": "E",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "D"},
                },
                "type": "DefiningContextConstraint",
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.Vj8RALpb4HP9RtsDNiaW_N3ODw3aSj5T",
                "type": "Allele",
                "label": "2-198267491-C-G",
                "digest": "Vj8RALpb4HP9RtsDNiaW_N3ODw3aSj5T",
                "location": {
                    "id": "ga4gh:SL.R8r0t9A51FTOJ7Mb8VasF8L6D5Sa_FFU",
                    "type": "SequenceLocation",
                    "digest": "R8r0t9A51FTOJ7Mb8VasF8L6D5Sa_FFU",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.pnAqCRBrTsUoBghSD1yp_jXWSmlbdh4g",
                    },
                    "start": 197402766,
                    "end": 197402767,
                    "sequence": "C",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "G"},
            }
        ],
        "extensions": [
            {
                "name": "MOA representative coordinate",
                "value": {
                    "chromosome": "2",
                    "start_position": "198267491",
                    "end_position": "198267491",
                    "reference_allele": "C",
                    "alternate_allele": "G",
                    "cdna_change": "c.1866G>C",
                    "protein_change": "p.E622D",
                    "exon": "14",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "system": "https://moalmanac.org/api/features/",
                    "code": "532",
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                    "code": "rs763149798",
                },
                "relation": "relatedMatch",
            },
        ],
    }


@pytest.fixture(scope="module")
def moa_sf3b1():
    """Create MOA gene SF3B1 test fixture"""
    return {
        "id": "moa.normalize.gene:SF3B1",
        "type": "Gene",
        "label": "SF3B1",
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {"id": "hgnc:10768", "label": "SF3B1"},
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_source33():
    """Create MOA source ID 33 test fixture"""
    return {
        "id": "moa.source:33",
        "extensions": [{"name": "source_type", "value": "Guideline"}],
        "type": "Document",
        "title": "Referenced with permission from the NCCN Clinical Practice Guidelines in Oncology (NCCN Guidelines\u00ae) for Myelodysplastic Syndromes V.2.2023. \u00a9 National Comprehensive Cancer Network, Inc. 2023. All rights reserved. Accessed November 2, 2023. To view the most recent and complete version of the guideline, go online to NCCN.org.",
        "urls": ["https://www.nccn.org/professionals/physician_gls/pdf/mds_blocks.pdf"],
    }


@pytest.fixture(scope="module")
def moa_aid532_study_stmt(
    moa_vid532, moa_myelodysplasia, moa_sf3b1, moa_source33, moa_method
):
    """Create MOA AID 532 study statement test fixture."""
    return {
        "id": "moa.assertion:532",
        "type": "VariantPrognosticStudyStatement",
        "description": "The National Comprehensive Cancer Network\u00ae (NCCN\u00ae) highlights SF3B1 E622, Y623, R625, N626, H662, T663, K666, K700E, I704, G740, G742, and D781 missense variants as being associated with a favorable prognosis in patients with myelodysplastic syndromes.",
        "strength": {
            "code": "e000003",
            "label": "professional guideline evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "associatedWithBetterOutcomeFor",
        "subjectVariant": moa_vid532,
        "objectCondition": moa_myelodysplasia,
        "alleleOriginQualifier": "somatic",
        "geneContextQualifier": moa_sf3b1,
        "specifiedBy": moa_method,
        "reportedIn": [moa_source33],
    }


@pytest.fixture(scope="module")
def statements(moa_aid141_study_stmt, moa_aid532_study_stmt):
    """Create test fixture for MOA prognostic statements."""
    return [moa_aid141_study_stmt, moa_aid532_study_stmt]


def test_moa_cdm(data, statements, check_transformed_cdm):
    """Test that moa transformation works correctly."""
    check_transformed_cdm(data, statements, DATA_DIR / FILENAME)
