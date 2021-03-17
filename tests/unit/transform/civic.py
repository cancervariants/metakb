"""Test CIViC Transformation to common data model"""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT


@pytest.fixture(scope='module')
def civic():
    """Create a CIViC Transform test fixture."""
    return CIViCTransform(
        file_path=f"{PROJECT_ROOT}/tests/data/"
                  f"transform/civic_eid3017.json").transform()


@pytest.fixture(scope='module')
def eid3017():
    """Create a test fixture for CIViC evidence item 3017."""
    return {
        "id": "civic:EID3017",
        "type": "evidence",
        "disease_context": {
            "id": "civic:DiseaseID8",
            "label": "Lung Non-small Cell Carcinoma",
            "xrefs": [
                {
                    "system": "DiseaseOntology",
                    "id": "3908"
                }
            ]
        },
        "variant_origin": "Somatic",
        "clinical_significance": "Sensitivity/Response",
        "evidence_level": "A",
        "therapy_profile": {
            "label": "Trametinib and Dabrafenib Combination Therapy",
            "drugs": [
                {
                    "id": "ncit:19",
                    "label": "Trametinib",
                    "xrefs": [
                        {
                            "system": "ncit",
                            "id": "C77908"
                        }
                    ],
                    "aliases": [
                        "N-(3-{3-cyclopropyl-5-[(2-fluoro-4-iodophenyl)amino]-"
                        "6,8-dimethyl-2,4,7-trioxo-3,4,6,7-tetrahydropyrido"
                        "[4,3-d]pyrimidin-1(2H)-yl}phenyl)acetamide",
                        "Mekinist",
                        "MEK Inhibitor GSK1120212",
                        "JTP-74057",
                        "GSK1120212"
                    ]
                },
                {
                    "id": "ncit:22",
                    "label": "Dabrafenib",
                    "xrefs": [
                        {
                            "system": "ncit",
                            "id": "C82386"
                        }
                    ],
                    "aliases": [
                        "GSK2118436",
                        "GSK-2118436A",
                        "GSK-2118436",
                        "BRAF Inhibitor GSK2118436",
                        "Benzenesulfonamide, N-(3-(5-(2-amino-4-pyrimidinyl)"
                        "-2-(1,1-dimethylethyl)-4-thiazolyl)-2-fluorophenyl)-"
                        "2,6-difluoro-"
                    ]
                }
            ],
            "drug_interaction_type": "Combination"
        },
        "variation_profile": {
            "id": "civic:VID12",
            "type": "variant",
            "label": "BRAF V600E",
            "gene": "civic:GID5",
            "hgvs_descriptions": [
                "ENST00000288602.6:c.1799T>A",
                "NC_000007.13:g.140453136A>T",
                "NP_004324.2:p.Val600Glu",
                "NM_004333.4:c.1799T>A"
            ],
            "xrefs": [
                {
                    "system": "ClinVar",
                    "id": "376069",
                    "type": "variation"
                },
                {
                    "system": "ClinVar",
                    "id": "13961",
                    "type": "variation"
                },
                {
                    "system": "ClinGenAlleleRegistry",
                    "id": "CA123643"
                },
                {
                    "system": "dbSNP",
                    "id": "113488022",
                    "type": "rs"
                }
            ],
            "aliases": [
                "VAL600GLU"
            ]
        }
    }


def test_transform(eid3017, civic):
    """Test that transform is correct."""
    assert civic['civic:EID3017'] == eid3017
