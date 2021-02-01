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
        },
        "gene_profile": {
            "id": "civic:GID5",
            "type": "gene",
            "label": "BRAF",
            "description": "BRAF mutations are found to be recurrent in many cancer types. Of these, the mutation of valine 600 to glutamic acid (V600E) is the most prevalent. V600E has been determined to be an activating mutation, and cells that harbor it, along with other V600 mutations are sensitive to the BRAF inhibitor dabrafenib. It is also common to use MEK inhibition as a substitute for BRAF inhibitors, and the MEK inhibitor trametinib has seen some success in BRAF mutant melanomas. BRAF mutations have also been correlated with poor prognosis in many cancer types, although there is at least one study that questions this conclusion in papillary thyroid cancer.\n\nOncogenic BRAF mutations are divided into three categories that determine their sensitivity to inhibitors.\nClass 1 BRAF mutations (V600) are RAS-independent, signal as monomers and are sensitive to current RAF monomer inhibitors.\nClass 2 BRAF mutations (K601E, K601N, K601T, L597Q, L597V, G469A, G469V, G469R, G464V, G464E, and fusions) are RAS-independent, signaling as constitutive dimers and are resistant to vemurafenib. Such mutants may be sensitive to novel RAF dimer inhibitors or MEK inhibitors.\nClass 3 BRAF mutations (D287H, V459L, G466V, G466E, G466A, S467L, G469E, N581S, N581I, D594N, D594G, D594A, D594H, F595L, G596D, and G596R) with low or absent kinase activity are RAS-dependent and they activate ERK by increasing their binding to activated RAS and wild-type CRAF. Class 3 BRAF mutations coexist with mutations in RAS or NF1 in melanoma may be treated with MEK inhibitors. In epithelial tumors such as CRC or NSCLC may be effectively treated with combinations that include inhibitors of receptor tyrosine kinase.",  # noqa: E501
            "xrefs": [
                {
                    "system": "ncbigene",
                    "id": 673
                }
            ],
            "aliases": [
                "BRAF",
                "B-raf",
                "RAFB1",
                "NS7",
                "BRAF1",
                "B-RAF1"
            ]
        }
    }


def test_transform(eid3017, civic):
    """Test that transform is correct."""
    assert civic['civic:EID3017'] == eid3017
