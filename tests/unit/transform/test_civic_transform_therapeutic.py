"""Test CIViC Transformation to common data model for Therapeutic Response."""
import pytest
import pytest_asyncio
from metakb.transform.civic import CivicTransform
from metakb import PROJECT_ROOT
import json


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def civic_vid12():
    """Create test fixture for CIViC Variant ID 12"""
    return {
        "id": "ga4gh:VA.4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO",
        "type": "Allele",
        "label": "V600E",
        "digest": "4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO",
        "location": {
            "id": "ga4gh:SL.ZA1XNKhCT_7m2UtmnYb8ZYOVS4eplMEK",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                "type": "SequenceReference",
            },
            "start": 599,
            "end": 600
        },
        "state": {
            "sequence": "E",
            "type": "LiteralSequenceExpression"
        },
        "expressions": [
            {
                "syntax": "hgvs.p",
                "value": "NP_004324.2:p.Val600Glu"
            },
            {
                "syntax": "hgvs.c",
                "value": "NM_004333.4:c.1799T>A"
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000288602.6:c.1799T>A",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000007.13:g.140453136A>T",
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_mpid12(civic_vid12):
    """Create test fixture for CIViC Molecular Profile ID 12"""
    return {
        "id": "civic.mpid:12",
        "type": "ProteinSequenceConsequence",
        "description": "BRAF V600E has been shown to be recurrent in many cancer types. It is one of the most widely studied variants in cancer. This variant is correlated with poor prognosis in certain cancer types, including colorectal cancer and papillary thyroid cancer. The targeted therapeutic dabrafenib has been shown to be effective in clinical trials with an array of BRAF mutations and cancer types. Dabrafenib has also shown to be effective when combined with the MEK inhibitor trametinib in colorectal cancer and melanoma. However, in patients with TP53, CDKN2A and KRAS mutations, dabrafenib resistance has been reported. Ipilimumab, regorafenib, vemurafenib, and a number of combination therapies have been successful in treating V600E mutations. However, cetuximab and panitumumab have been largely shown to be ineffective without supplementary treatment.",  # noqa: E501
        "label": "BRAF V600E",
        "definingContext": civic_vid12,
        "members": [
            {
                "id": "ga4gh:VA.LX3ooHBAiZdKY4RfTXcliUmkj48mnD_M",
                "label": "NC_000007.13:g.140453136A>T",
                "digest": "LX3ooHBAiZdKY4RfTXcliUmkj48mnD_M",
                "type": "Allele",
                "location": {
                    "id": "ga4gh:SL.XutGzMvqbzN-vnxmPt2MJf7ehxmB0opi",
                    "type": "SequenceLocation",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.F-LrLMe1SRpfUZHkQmvkVKFEGaoDeHul"
                    },
                    "start": 140753335,
                    "end": 140753336
                },
                "state": {
                    "type": "LiteralSequenceExpression",
                    "sequence": "T"
                }
            }
        ],
        "aliases": [
            "VAL600GLU",
            "V640E",
            "VAL640GLU"
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA123643",
                    "system": "https://reg.clinicalgenome.org/"
                },
                "relation": "relatedMatch"
            },
            {
                "coding": {
                    "code": "13961",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/"
                },
                "relation": "relatedMatch"
            },
            {
                "coding": {
                    "code": "376069",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/"
                },
                "relation": "relatedMatch"
            },
            {
                "coding": {
                    "code": "rs113488022",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/"
                },
                "relation": "relatedMatch"
            },
            {
                "coding": {"code": "12", "system": "https://civicdb.org/variants/"},
                "relation": "exactMatch"
            }
        ],
        "extensions": [
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "7",
                    "start": 140453136,
                    "stop": 140453136,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288602.6",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates"
                },
                "type": "Extension"
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 1353.5,
                "type": "Extension"
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",  # noqa: E501
                        "label": "missense_variant",
                        "version": None
                    }
                ],
                "type": "Extension"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid28():
    """Create test fixture for CIViC therapy ID 28"""
    return {
        "id": "civic.tid:28",
        "type": "TherapeuticAgent",
        "label": "Panitumumab",
        "mappings": [
            {
                "coding": {
                    "code": "C1857",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
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
        "extensions": [
            {
                "type": "Extension",
                "name": "therapy_normalizer_data",
                "value": {
                    "normalized_id": "rxcui:263034",
                    "label": "panitumumab"
                }
            },
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "type": "Disease",
                            "label": "Neoplasms",
                            "mappings": [
                                {
                                    "coding": {"code": "C3262", "system": "ncit"},
                                    "relation": "relatedMatch"
                                }
                            ]
                        },
                        {
                            "id": "mesh:D015179",
                            "type": "Disease",
                            "label": "Colorectal Neoplasms",
                            "mappings": [
                                {
                                    "coding": {"code": "C2956", "system": "ncit"},
                                    "relation": "relatedMatch"
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid16(cetuximab_extensions):
    """Create test fixture for CIViC therapy ID 16"""
    return {
        "id": "civic.tid:16",
        "type": "TherapeuticAgent",
        "label": "Cetuximab",
        "mappings": [
            {
                "coding": {
                    "code": "C1723",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
            "Cetuximab Biosimilar CDP-1",
            "Cetuximab Biosimilar CMAB009",
            "Cetuximab Biosimilar KL 140",
            "Chimeric Anti-EGFR Monoclonal Antibody",
            "Chimeric MoAb C225",
            "Chimeric Monoclonal Antibody C225",
            "Erbitux",
            "IMC-C225"
        ],
        "extensions": cetuximab_extensions
    }


@pytest.fixture(scope="module")
def civic_gid5():
    """Create test fixture for CIViC GID5."""
    return {
        "id": "civic.gid:5",
        "type": "Gene",
        "label": "BRAF",
        "description": "BRAF mutations are found to be recurrent in many cancer types. Of these, the mutation of valine 600 to glutamic acid (V600E) is the most prevalent. V600E has been determined to be an activating mutation, and cells that harbor it, along with other V600 mutations are sensitive to the BRAF inhibitor dabrafenib. It is also common to use MEK inhibition as a substitute for BRAF inhibitors, and the MEK inhibitor trametinib has seen some success in BRAF mutant melanomas. BRAF mutations have also been correlated with poor prognosis in many cancer types, although there is at least one study that questions this conclusion in papillary thyroid cancer.\n\nOncogenic BRAF mutations are divided into three categories that determine their sensitivity to inhibitors.\nClass 1 BRAF mutations (V600) are RAS-independent, signal as monomers and are sensitive to current RAF monomer inhibitors.\nClass 2 BRAF mutations (K601E, K601N, K601T, L597Q, L597V, G469A, G469V, G469R, G464V, G464E, and fusions) are RAS-independent, signaling as constitutive dimers and are resistant to vemurafenib. Such mutants may be sensitive to novel RAF dimer inhibitors or MEK inhibitors.\nClass 3 BRAF mutations (D287H, V459L, G466V, G466E, G466A, S467L, G469E, N581S, N581I, D594N, D594G, D594A, D594H, F595L, G596D, and G596R) with low or absent kinase activity are RAS-dependent and they activate ERK by increasing their binding to activated RAS and wild-type CRAF. Class 3 BRAF mutations coexist with mutations in RAS or NF1 in melanoma may be treated with MEK inhibitors. In epithelial tumors such as CRC or NSCLC may be effectively treated with combinations that include inhibitors of receptor tyrosine kinase.",  # noqa: E501
        "mappings": [
            {
                "coding": {
                    "code": "ncbigene:673",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/"
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
            "B-RAF1",
            "B-raf",
            "BRAF",
            "BRAF-1",
            "BRAF1",
            "NS7",
            "RAFB1"
        ],
    }


@pytest.fixture(scope="module")
def civic_did11():
    """Create test fixture for CIViC Disease ID 11"""
    return {
        "id": "civic.did:11",
        "type": "Disease",
        "label": "Colorectal Cancer",
        "mappings": [
            {
                "coding": {
                    "code": "DOID:9256",
                    "system": "https://www.disease-ontology.org/"
                },
                "relation": "exactMatch"
            }
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "disease_normalizer_data",
                "value": {
                    "normalized_id": "ncit:C4978",
                    "label": "Malignant Colorectal Neoplasm",
                    "mondo_id": "0005575"
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_eid816_study(
    civic_mpid12,
    civic_tsg,
    civic_did11,
    civic_gid5,
    civic_method
):
    """Create CIVIC EID816 study test fixture. Uses TherapeuticSubstituteGroup."""
    return {
        "id": "civic.eid:816",
        "type": "VariantTherapeuticResponseStudy",
        "description": "This meta-analysis of 7 randomized control trials evaluating overall survival (OS) (8 for progression free survival) could not definitely state that survival benefit of anti-EGFR monoclonal antibodies is limited to patients with wild type BRAF. In other words, the authors believe that there is insufficient data to justify the exclusion of anti-EGFR monoclonal antibody therapy for patients with mutant BRAF. In these studies, mutant BRAF specifically meant the V600E mutation.",  # noqa: E501
        "direction": "refutes",
        "strength": {
            "code": "e000005",
            "label": "clinical cohort evidence",
            "system": "https://go.osu.edu/evidence-codes"
        },
        "predicate": "predictsResistanceTo",
        "variant": civic_mpid12,
        "therapeutic": civic_tsg,
        "tumorType": civic_did11,
        "qualifiers": {
            "alleleOrigin": "somatic",
            "geneContext": civic_gid5
        },
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:548",
                "label": "Rowland et al., 2015",
                "title": "Meta-analysis of BRAF mutation as a predictive biomarker of benefit from anti-EGFR monoclonal antibody therapy for RAS wild-type metastatic colorectal cancer.",  # noqa: E501
                "pmid": 25989278,
                "type": "Document"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_eid9851_study(
    civic_mpid12,
    civic_ct,
    civic_did11,
    civic_gid5,
    civic_method,
):
    """Create CIVIC EID9851 study test fixture. Uses CombinationTherapy."""
    return {
        "id": "civic.eid:9851",
        "type": "VariantTherapeuticResponseStudy",
        "description": "The open-label phase 3 BEACON CRC trial included 665 patients with BRAF V600E-mutated metastatic CRC. Patients were randomly assigned in a 1:1:1 ratio to receive encorafenib, binimetinib, and cetuximab (triplet-therapy group); encorafenib and cetuximab (doublet-therapy group); or the investigators\u2019 choice of either cetuximab and irinotecan or cetuximab and FOLFIRI. The median overall survival was 8.4 months (95% CI, 7.5 to 11.0) in the doublet-therapy group and 5.4 months (95% CI, 4.8 to 6.6) in the control group, with a significantly lower risk of death compared to the control group (hazard ratio for death doublet-group vs. control, 0.60; 95% CI, 0.45 to 0.79; P<0.001). The confirmed response rate was 26% (95% CI, 18 to 35) in the triplet-therapy group, 20% in the doublet-therapy group (95% CI 13 to 29) and 2% (95% CI, 0 to 7) in the control group (doublet group vs. control P<0.001). Median PFS was 4.2 months (95% CI, 3.7 to 5.4) in the doublet-therapy group, and 1.5 months (95% CI, 1.5 to 1.7) in the control group (hazard ratio for disease progression doublet-group vs control, 0.40; 95% CI, 0.31 to 0.52, P<0.001).",  # noqa: E501
        "direction": "supports",
        "strength": {
            "code": "e000001",
            "label": "authoritative evidence",
            "system": "https://go.osu.edu/evidence-codes"
        },
        "predicate": "predictsSensitivityTo",
        "variant": civic_mpid12,
        "therapeutic": civic_ct,
        "tumorType": civic_did11,
        "qualifiers": {
            "alleleOrigin": "somatic",
            "geneContext": civic_gid5
        },
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:3025",
                "label": "Kopetz et al., 2019",
                "title": "Encorafenib, Binimetinib, and Cetuximab in BRAF V600E-Mutated Colorectal Cancer.",  # noqa: E501
                "pmid": 31566309,
                "type": "Document"
            }
        ]
    }


@pytest.fixture(scope="module")
def studies(civic_eid2997_study, civic_eid816_study, civic_eid9851_study):
    """Create test fixture for CIViC therapeutic studies."""
    return [civic_eid2997_study, civic_eid816_study, civic_eid9851_study]


def test_civic_cdm(data, studies, check_transformed_cdm):
    """Test that civic transform works correctly."""
    check_transformed_cdm(
        data, studies, DATA_DIR / FILENAME
    )
