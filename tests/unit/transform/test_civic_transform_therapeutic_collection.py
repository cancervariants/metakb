"""Test CIViC evidence with therapeutic collections"""
import json

import pytest
import pytest_asyncio

from metakb.transform.civic import CIViCTransform  # noqa: I202
from metakb import PROJECT_ROOT


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic_collection"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CIViCTransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def pmid_31566309():
    """Create test fixture for PubMed ID 31566309"""
    return {
        "id": "civic.source:3025",
        "label": "Kopetz et al., 2019, N. Engl. J. Med.",
        "title": "Encorafenib, Binimetinib, and Cetuximab in BRAF V600E-Mutated Colorectal Cancer.",  # noqa: E501
        "xrefs": ["pmid:31566309"],
        "type": "Document"
    }


@pytest.fixture(scope="module")
def pmid_25989278():
    """Create test fixture for PubMed ID 25989278"""
    return {
        "id": "civic.source:548",
        "label": "Rowland et al., 2015, Br. J. Cancer",
        "title": "Meta-analysis of BRAF mutation as a predictive biomarker of benefit from anti-EGFR monoclonal antibody therapy for RAS wild-type metastatic colorectal cancer.",  # noqa: E501
        "xrefs": ["pmc:PMC4580381", "pmid:25989278"],
        "type": "Document"
    }


@pytest.fixture(scope="module")
def civic_eid9851_statement(method1, pmid_31566309):
    """Create CIVIC EID9851 Statement test fixture"""
    return {
        "id": "civic.eid:9851",
        "type": "VariationNeoplasmTherapeuticResponseStatement",
        "description": "The open-label phase 3 BEACON CRC trial included 665 patients with BRAF V600E-mutated metastatic CRC. Patients were randomly assigned in a 1:1:1 ratio to receive encorafenib, binimetinib, and cetuximab (triplet-therapy group); encorafenib and cetuximab (doublet-therapy group); or the investigators’ choice of either cetuximab and irinotecan or cetuximab and FOLFIRI. The median overall survival was 8.4 months (95% CI, 7.5 to 11.0) in the doublet-therapy group and 5.4 months (95% CI, 4.8 to 6.6) in the control group, with a significantly lower risk of death compared to the control group (hazard ratio for death doublet-group vs. control, 0.60; 95% CI, 0.45 to 0.79; P<0.001). The confirmed response rate was 26% (95% CI, 18 to 35) in the triplet-therapy group, 20% in the doublet-therapy group (95% CI 13 to 29) and 2% (95% CI, 0 to 7) in the control group (doublet group vs. control P<0.001). Median PFS was 4.2 months (95% CI, 3.7 to 5.4) in the doublet-therapy group, and 1.5 months (95% CI, 1.5 to 1.7) in the control group (hazard ratio for disease progression doublet-group vs control, 0.40; 95% CI, 0.31 to 0.52, P<0.001).",  # noqa: E501
        "direction": "supports",
        "evidence_level": {
            "id": "vicc:e00001",
            "label": "authoritative evidence",
            "type": "Coding"
        },
        "target_proposition": "proposition:c2PfzLMShNKjM4iuJgjpJLGb8vKJYFNl",
        "variation_origin": "somatic",
        "subject_descriptor": "civic.vid:12",
        "object_descriptor": "civic.tcd:P1PY89shAjemg7jquQ0V9pg1VnYnkPeK",
        "neoplasm_type_descriptor": "civic.did:11",
        "specified_by": method1,
        "contributions": [
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Cam Grisdale",
                    "id": "civic.user:968"
                },
                "date": "2021-11-09T20:40:42.744Z",
                "activity": {
                    "type": "Coding",
                    "label": "submitted"
                }
            },
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Cam Grisdale",
                    "id": "civic.user:968"
                },
                "date": "2021-11-09T20:42:29.151Z",
                "activity": {
                    "type": "Coding",
                    "label": "last_commented_on"
                }
            },
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Kilannin Krysiak",
                    "id": "civic.user:6"
                },
                "date": "2022-02-11T23:51:32.656Z",
                "activity": {
                    "type": "Coding",
                    "label": "accepted"
                }
            }
        ],
        "is_reported_in": [pmid_31566309]
    }


@pytest.fixture(scope="module")
def civic_eid9851_proposition():
    """Create a test fixture for EID9851 proposition"""
    return {
        "id": "proposition:c2PfzLMShNKjM4iuJgjpJLGb8vKJYFNl",
        "type": "VariationNeoplasmTherapeuticResponseProposition",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.h313H4CQh6pogbbSJ3H5pI1cPoh9YMm_",
        "neoplasm_type_qualifier": {"id": "ncit:C4978", "type": "Disease"},
        "object": {
            "type": "CombinationTherapeutics",
            "members": [
                {"id": "rxcui:2049106", "type": "Therapeutic"},
                {"id": "rxcui:318341", "type": "Therapeutic"}
            ]
        }
    }


@pytest.fixture(scope="module")
def civic_eid816_statement(method1, pmid_25989278):
    """Create CIVIC EID816 Statement test fixture"""
    return {
        "id": "civic.eid:816",
        "type": "VariationNeoplasmTherapeuticResponseStatement",
        "description": "This meta-analysis of 7 randomized control trials evaluating overall survival (OS) (8 for progression free survival) could not definitely state that survival benefit of anti-EGFR monoclonal antibodies is limited to patients with wild type BRAF. In other words, the authors believe that there is insufficient data to justify the exclusion of anti-EGFR monoclonal antibody therapy for patients with mutant BRAF. In these studies, mutant BRAF specifically meant the V600E mutation.",  # noqa: E501
        "direction": "opposes",
        "evidence_level": {
            "id": "vicc:e00005",
            "label": "clinical cohort evidence",
            "type": "Coding"
        },
        "target_proposition": "proposition:R6kd1VbbX_M-9Bs9WkrHDmTG-EmunICY",
        "variation_origin": "somatic",
        "subject_descriptor": "civic.vid:12",
        "object_descriptor": "civic.tcd:7IxyhCwID0QYyVCP2xuIyYvwwu-S_HrZ",
        "neoplasm_type_descriptor": "civic.did:11",
        "specified_by": method1,
        "contributions": [
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Damian Rieke",
                    "id": "civic.user:100"
                },
                "date": "2016-01-12T10:25:26.787Z",
                "activity": {
                    "type": "Coding",
                    "label": "submitted"
                }
            },
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Obi Griffith",
                    "id": "civic.user:3"
                },
                "date": "2016-02-18T19:55:57.565Z",
                "activity": {
                    "type": "Coding",
                    "label": "last_modified"
                }
            },
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Kilannin Krysiak",
                    "id": "civic.user:6"
                },
                "date": "2016-02-18T19:56:58.994Z",
                "activity": {
                    "type": "Coding",
                    "label": "last_reviewed"
                }
            },
            {
                "type": "Contribution",
                "contributor": {
                    "type": "Agent",
                    "name": "Kilannin Krysiak",
                    "id": "civic.user:6"
                },
                "date": "2016-01-28T04:23:37.049Z",
                "activity": {
                    "type": "Coding",
                    "label": "accepted"
                }
            },
        ],
        "is_reported_in": [pmid_25989278]
    }


@pytest.fixture(scope="module")
def civic_eid816_proposition():
    """Create a test fixture for EID816 proposition"""
    return {
        "id": "proposition:R6kd1VbbX_M-9Bs9WkrHDmTG-EmunICY",
        "type": "VariationNeoplasmTherapeuticResponseProposition",
        "predicate": "predicts_resistance_to",
        "subject": "ga4gh:VA.h313H4CQh6pogbbSJ3H5pI1cPoh9YMm_",
        "neoplasm_type_qualifier": {"id": "ncit:C4978", "type": "Disease"},
        "object": {
            "type": "SubstituteTherapeutics",
            "members": [
                {"id": "rxcui:318341", "type": "Therapeutic"},
                {"id": "rxcui:263034", "type": "Therapeutic"}
            ]
        }
    }


@pytest.fixture(scope="module")
def civic_vid12(braf_v600e_variation):
    """Create a test fixture for CIViC VID12"""
    return {
        "id": "civic.vid:12",
        "type": "VariationDescriptor",
        "label": "V600E",
        "description": "BRAF V600E has been shown to be recurrent in many cancer types. It is one of the most widely studied variants in cancer. This variant is correlated with poor prognosis in certain cancer types, including colorectal cancer and papillary thyroid cancer. The targeted therapeutic dabrafenib has been shown to be effective in clinical trials with an array of BRAF mutations and cancer types. Dabrafenib has also shown to be effective when combined with the MEK inhibitor trametinib in colorectal cancer and melanoma. However, in patients with TP53, CDKN2A and KRAS mutations, dabrafenib resistance has been reported. Ipilimumab, regorafenib, vemurafenib, and a number of combination therapies have been successful in treating V600E mutations. However, cetuximab and panitumumab have been largely shown to be ineffective without supplementary treatment.",  # noqa: E501
        "variation": braf_v600e_variation,
        "xrefs": [
            "clinvar:376069",
            "clinvar:13961",
            "caid:CA123643",
            "dbsnp:113488022"
        ],
        "alternate_labels": [
            "VAL600GLU",
            "V640E",
            "VAL640GLU"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "7",
                    "start": 140453136,
                    "stop": 140453136,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288602.6",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "1353.5",
                "type": "Extension"
            }
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.p",
                "value": "NP_004324.2:p.Val600Glu",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000288602.6:c.1799T>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.c",
                "value": "NM_004333.4:c.1799T>A",
                "type": "Expression"
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000007.13:g.140453136A>T",
                "type": "Expression"
            }
        ],
        "gene_context": "civic.gid:5"
    }


@pytest.fixture(scope="module")
def civic_gid5():
    """Create test fixture for CIViC GID5"""
    return {
        "id": "civic.gid:5",
        "type": "GeneDescriptor",
        "label": "BRAF",
        "description": "BRAF mutations are found to be recurrent in many cancer types. Of these, the mutation of valine 600 to glutamic acid (V600E) is the most prevalent. V600E has been determined to be an activating mutation, and cells that harbor it, along with other V600 mutations are sensitive to the BRAF inhibitor dabrafenib. It is also common to use MEK inhibition as a substitute for BRAF inhibitors, and the MEK inhibitor trametinib has seen some success in BRAF mutant melanomas. BRAF mutations have also been correlated with poor prognosis in many cancer types, although there is at least one study that questions this conclusion in papillary thyroid cancer.\n\nOncogenic BRAF mutations are divided into three categories that determine their sensitivity to inhibitors.\nClass 1 BRAF mutations (V600) are RAS-independent, signal as monomers and are sensitive to current RAF monomer inhibitors.\nClass 2 BRAF mutations (K601E, K601N, K601T, L597Q, L597V, G469A, G469V, G469R, G464V, G464E, and fusions) are RAS-independent, signaling as constitutive dimers and are resistant to vemurafenib. Such mutants may be sensitive to novel RAF dimer inhibitors or MEK inhibitors.\nClass 3 BRAF mutations (D287H, V459L, G466V, G466E, G466A, S467L, G469E, N581S, N581I, D594N, D594G, D594A, D594H, F595L, G596D, and G596R) with low or absent kinase activity are RAS-dependent and they activate ERK by increasing their binding to activated RAS and wild-type CRAF. Class 3 BRAF mutations coexist with mutations in RAS or NF1 in melanoma may be treated with MEK inhibitors. In epithelial tumors such as CRC or NSCLC may be effectively treated with combinations that include inhibitors of receptor tyrosine kinase.",  # noqa: E501
        "gene": "hgnc:1097",
        "alternate_labels": [
            "BRAF-1",
            "BRAF",
            "B-raf",
            "RAFB1",
            "NS7",
            "BRAF1",
            "B-RAF1"
        ],
        "xrefs": [
            "ncbigene:673"
        ]
    }


@pytest.fixture(scope="module")
def civic_tid483():
    """Create test fixture for CIViC Drug 483"""
    return {
        "id": "civic.tid:483",
        "type": "TherapeuticDescriptor",
        "label": "Encorafenib",
        "therapeutic": "rxcui:2049106",
        "alternate_labels": [
            "Braftovi",
            "LGX 818",
            "LGX-818",
            "LGX818"
        ],
        "xrefs": ["ncit:C98283"],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "type": "DiseaseDescriptor",
                            "label": "Neoplasms",
                            "disease": "ncit:C3262"
                        },
                        {
                            "id": "mesh:D008545",
                            "type": "DiseaseDescriptor",
                            "label": "Melanoma",
                            "disease": "ncit:C3224"
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid16():
    """Create test fixture for CIViC Drug 16"""
    return {
        "id": "civic.tid:16",
        "type": "TherapeuticDescriptor",
        "label": "Cetuximab",
        "therapeutic": "rxcui:318341",
        "alternate_labels": [
            "Cetuximab Biosimilar CDP-1",
            "Cetuximab Biosimilar CMAB009",
            "Cetuximab Biosimilar KL 140",
            "Chimeric Anti-EGFR Monoclonal Antibody",
            "Chimeric MoAb C225",
            "Chimeric Monoclonal Antibody C225",
            "Erbitux",
            "IMC-C225"
        ],
        "xrefs": ["ncit:C1723"],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D002294",
                            "type": "DiseaseDescriptor",
                            "label": "Carcinoma, Squamous Cell",
                            "disease": "ncit:C2929"
                        },
                        {
                            "id": "mesh:D009369",
                            "type": "DiseaseDescriptor",
                            "label": "Neoplasms",
                            "disease": "ncit:C3262"
                        },
                        {
                            "id": "mesh:D015179",
                            "type": "DiseaseDescriptor",
                            "label": "Colorectal Neoplasms",
                            "disease": "ncit:C2956"
                        },
                        {
                            "id": "mesh:D006258",
                            "type": "DiseaseDescriptor",
                            "label": "Head and Neck Neoplasms",
                            "disease": "ncit:C4013"
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid28():
    """Create test fixture for CIViC Drug 28"""
    return {
        "id": "civic.tid:28",
        "type": "TherapeuticDescriptor",
        "label": "Panitumumab",
        "therapeutic": "rxcui:263034",
        "alternate_labels": [
            "ABX-EGF",
            "ABX-EGF Monoclonal Antibody",
            "ABX-EGF, Clone E7.6.3",
            "E7.6.3",
            "Human IgG2K Monoclonal Antibody",
            "MoAb ABX-EGF",
            "MoAb E7.6.3",
            "Monoclonal Antibody ABX-EGF",
            "Monoclonal Antibody E7.6.3",
            "Vectibix"
        ],
        "xrefs": ["ncit:C1857"],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "type": "DiseaseDescriptor",
                            "label": "Neoplasms",
                            "disease": "ncit:C3262"
                        },
                        {
                            "id": "mesh:D015179",
                            "type": "DiseaseDescriptor",
                            "label": "Colorectal Neoplasms",
                            "disease": "ncit:C2956"
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tcd_combination(civic_tid483, civic_tid16):
    """Create test fixture for CIViC Combination Collection"""
    return {
        "id": "civic.tcd:P1PY89shAjemg7jquQ0V9pg1VnYnkPeK",
        "type": "TherapeuticsCollectionDescriptor",
        "therapeutic_collection": {
            "type": "CombinationTherapeutics",
            "members": [
                {"id": "rxcui:2049106", "type": "Therapeutic"},
                {"id": "rxcui:318341", "type": "Therapeutic"}
            ]
        },
        "member_descriptors": [civic_tid483, civic_tid16],
        "extensions": [
            {
                "type": "Extension",
                "name": "civic_drug_interaction_type",
                "value": "COMBINATION"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tcd_substitutes(civic_tid16, civic_tid28):
    """Create test fixture for CIViC Substitutes Collection"""
    return {
        "id": "civic.tcd:7IxyhCwID0QYyVCP2xuIyYvwwu-S_HrZ",
        "type": "TherapeuticsCollectionDescriptor",
        "therapeutic_collection": {
            "type": "SubstituteTherapeutics",
            "members": [
                {"id": "rxcui:318341", "type": "Therapeutic"},
                {"id": "rxcui:263034", "type": "Therapeutic"}
            ]
        },
        "member_descriptors": [civic_tid16, civic_tid28],
        "extensions": [
            {
                "type": "Extension",
                "name": "civic_drug_interaction_type",
                "value": "SUBSTITUTES"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_did11():
    """Create test fixture for CIViC Disease 11"""
    return {
        "id": "civic.did:11",
        "type": "DiseaseDescriptor",
        "label": "Colorectal Cancer",
        "disease": "ncit:C4978",
        "xrefs": ["DOID:9256"]
    }


@pytest.fixture(scope="module")
def statements(civic_eid9851_statement, civic_eid816_statement):
    """Create test fixture for statements"""
    return [civic_eid9851_statement, civic_eid816_statement]


@pytest.fixture(scope="module")
def propositions(civic_eid9851_proposition, civic_eid816_proposition):
    """Create test fixture for propositions"""
    return [civic_eid9851_proposition, civic_eid816_proposition]


@pytest.fixture(scope="module")
def variation_descriptors(civic_vid12):
    """Create test fixture for variation descriptors"""
    return [civic_vid12]


@pytest.fixture(scope="module")
def therapeutic_descriptors(civic_tid483, civic_tid16, civic_tid28):
    """Create a test fixture for therapeutic descriptors"""
    return [civic_tid483, civic_tid16, civic_tid28]


@pytest.fixture(scope="module")
def therapeutic_collection_descriptors(civic_tcd_combination, civic_tcd_substitutes):
    """Create test fixture for therapeutic collection descriptors"""
    return [civic_tcd_combination, civic_tcd_substitutes]


@pytest.fixture(scope="module")
def disease_descriptors(civic_did11):
    """Create test fixture for disease_descriptors"""
    return [civic_did11]


@pytest.fixture(scope="module")
def gene_descriptors(civic_gid5):
    """Create test fixture for gene descriptors"""
    return [civic_gid5]


@pytest.fixture(scope="module")
def documents(pmid_31566309, pmid_25989278):
    """Create test fixture for documents"""
    return [pmid_31566309, pmid_25989278]


def test_civic_cdm(data, statements, propositions, variation_descriptors,
                   gene_descriptors, disease_descriptors, civic_methods, documents,
                   check_statement, check_proposition, check_variation_descriptor,
                   check_descriptor, check_document, check_method,
                   therapeutic_descriptors, therapeutic_collection_descriptors,
                   check_transformed_cdm):
    """Test that civic transform works correctly with therapeutic collections."""
    check_transformed_cdm(
        data, statements, propositions, variation_descriptors, gene_descriptors,
        disease_descriptors, civic_methods, documents, check_statement,
        check_proposition, check_variation_descriptor, check_descriptor, check_document,
        check_method, DATA_DIR / FILENAME,
        therapeutic_descriptors=therapeutic_descriptors,
        therapeutic_collection_descriptors=therapeutic_collection_descriptors
    )
