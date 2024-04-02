"""Module for pytest fixtures."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from metakb.normalizers import ViccNormalizers

TEST_DATA_DIR = Path(__file__).resolve().parents[0] / "data"
TEST_HARVESTERS_DIR = TEST_DATA_DIR / "harvesters"
TEST_TRANSFORM_DIR = TEST_DATA_DIR / "transform"


@pytest.fixture(scope="session")
def cetuximab_extensions():
    """Create test fixture for cetuximab extensions"""
    return [
        {
            "type": "Extension",
            "name": "therapy_normalizer_data",
            "value": {"normalized_id": "rxcui:318341", "label": "cetuximab"},
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
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D015179",
                        "type": "Disease",
                        "label": "Colorectal Neoplasms",
                        "mappings": [
                            {
                                "coding": {"code": "C2956", "system": "ncit"},
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D006258",
                        "type": "Disease",
                        "label": "Head and Neck Neoplasms",
                        "mappings": [
                            {
                                "coding": {"code": "C4013", "system": "ncit"},
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D002294",
                        "type": "Disease",
                        "label": "Carcinoma, Squamous Cell",
                        "mappings": [
                            {
                                "coding": {"code": "C2929", "system": "ncit"},
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                ],
            },
        },
    ]


@pytest.fixture(scope="session")
def encorafenib_extensions():
    """Create test fixture for encorafenib extensions"""
    return [
        {
            "type": "Extension",
            "name": "therapy_normalizer_data",
            "value": {"normalized_id": "rxcui:2049106", "label": "encorafenib"},
        },
        {
            "type": "Extension",
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "ChEMBL",
                "has_indications": [
                    {
                        "id": "mesh:D008545",
                        "type": "Disease",
                        "label": "Melanoma",
                        "mappings": [
                            {
                                "coding": {"code": "C3224", "system": "ncit"},
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D009369",
                        "type": "Disease",
                        "label": "Neoplasms",
                        "mappings": [
                            {
                                "coding": {"code": "C3262", "system": "ncit"},
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                ],
            },
        },
    ]


@pytest.fixture(scope="session")
def civic_mpid33(civic_vid33):
    """Create CIViC MPID 33"""
    return {
        "id": "civic.mpid:33",
        "type": "ProteinSequenceConsequence",
        "description": "EGFR L858R has long been recognized as a functionally significant mutation in cancer, and is one of the most prevalent single mutations in lung cancer. Best described in non-small cell lung cancer (NSCLC), the mutation seems to confer sensitivity to first and second generation TKI's like gefitinib and neratinib. NSCLC patients with this mutation treated with TKI's show increased overall and progression-free survival, as compared to chemotherapy alone. Third generation TKI's are currently in clinical trials that specifically focus on mutant forms of EGFR, a few of which have shown efficacy in treating patients that failed to respond to earlier generation TKI therapies.",
        "label": "EGFR L858R",
        "definingContext": civic_vid33,
        "members": [
            {
                "id": "ga4gh:VA.pM_eD8ha-bnAu6wJOoQTtHYIvEShSN51",
                "label": "NC_000007.13:g.55259515T>G",
                "digest": "pM_eD8ha-bnAu6wJOoQTtHYIvEShSN51",
                "type": "Allele",
                "location": {
                    "id": "ga4gh:SL.7g6PIIHJ_QkKe_dRvkuCe8UtZCmPxo5B",
                    "digest": "7g6PIIHJ_QkKe_dRvkuCe8UtZCmPxo5B",
                    "type": "SequenceLocation",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.F-LrLMe1SRpfUZHkQmvkVKFEGaoDeHul",
                    },
                    "start": 55191821,
                    "end": 55191822,
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "G"},
            }
        ],
        "aliases": ["LEU858ARG"],
        "mappings": [
            {
                "coding": {
                    "code": "CA126713",
                    "system": "https://reg.clinicalgenome.org/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "16609",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "376282",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "376280",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs121434568",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {"code": "33", "system": "https://civicdb.org/variants/"},
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "7",
                    "start": 55259515,
                    "stop": 55259515,
                    "reference_bases": "T",
                    "variant_bases": "G",
                    "representative_transcript": "ENST00000275493.2",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
                "type": "Extension",
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 379.0,
                "type": "Extension",
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "label": "missense_variant",
                        "version": None,
                    }
                ],
                "type": "Extension",
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_eid2997_qualifier(civic_gid19):
    """Create qualifier for civic eid 2997"""
    return {"alleleOrigin": "somatic", "geneContext": civic_gid19}


@pytest.fixture(scope="session")
def civic_source592():
    """Create fixture for civic source 592"""
    return {
        "id": "civic.source:1725",
        "label": "Dungo et al., 2013",
        "title": "Afatinib: first global approval.",
        "pmid": 23982599,
        "type": "Document",
    }


@pytest.fixture(scope="session")
def civic_eid2997_study(
    civic_mpid33,
    civic_tid146,
    civic_did8,
    civic_eid2997_qualifier,
    civic_method,
    civic_source592,
):
    """Create CIVIC EID2997 Statement test fixture. Uses TherapeuticAgent."""
    return {
        "id": "civic.eid:2997",
        "type": "VariantTherapeuticResponseStudy",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",
        "direction": "supports",
        "strength": {
            "code": "e000001",
            "label": "authoritative evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "predictsSensitivityTo",
        "variant": civic_mpid33,
        "therapeutic": civic_tid146,
        "tumorType": civic_did8,
        "qualifiers": civic_eid2997_qualifier,
        "specifiedBy": civic_method,
        "isReportedIn": [civic_source592],
    }


@pytest.fixture(scope="session")
def civic_gid5():
    """Create test fixture for CIViC GID5."""
    return {
        "id": "civic.gid:5",
        "type": "Gene",
        "label": "BRAF",
        "description": "BRAF mutations are found to be recurrent in many cancer types. Of these, the mutation of valine 600 to glutamic acid (V600E) is the most prevalent. V600E has been determined to be an activating mutation, and cells that harbor it, along with other V600 mutations are sensitive to the BRAF inhibitor dabrafenib. It is also common to use MEK inhibition as a substitute for BRAF inhibitors, and the MEK inhibitor trametinib has seen some success in BRAF mutant melanomas. BRAF mutations have also been correlated with poor prognosis in many cancer types, although there is at least one study that questions this conclusion in papillary thyroid cancer.\n\nOncogenic BRAF mutations are divided into three categories that determine their sensitivity to inhibitors.\nClass 1 BRAF mutations (V600) are RAS-independent, signal as monomers and are sensitive to current RAF monomer inhibitors.\nClass 2 BRAF mutations (K601E, K601N, K601T, L597Q, L597V, G469A, G469V, G469R, G464V, G464E, and fusions) are RAS-independent, signaling as constitutive dimers and are resistant to vemurafenib. Such mutants may be sensitive to novel RAF dimer inhibitors or MEK inhibitors.\nClass 3 BRAF mutations (D287H, V459L, G466V, G466E, G466A, S467L, G469E, N581S, N581I, D594N, D594G, D594A, D594H, F595L, G596D, and G596R) with low or absent kinase activity are RAS-dependent and they activate ERK by increasing their binding to activated RAS and wild-type CRAF. Class 3 BRAF mutations coexist with mutations in RAS or NF1 in melanoma may be treated with MEK inhibitors. In epithelial tumors such as CRC or NSCLC may be effectively treated with combinations that include inhibitors of receptor tyrosine kinase.",
        "mappings": [
            {
                "coding": {
                    "code": "ncbigene:673",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            }
        ],
        "aliases": ["B-RAF1", "B-raf", "BRAF", "BRAF-1", "BRAF1", "NS7", "RAFB1"],
        "extensions": [
            {"type": "Extension", "name": "gene_normalizer_id", "value": "hgnc:1097"}
        ],
    }


@pytest.fixture(scope="session")
def civic_vid12():
    """Create test fixture for CIViC Variant ID 12"""
    return {
        "id": "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
        "type": "Allele",
        "label": "V600E",
        "digest": "j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
        "location": {
            "id": "ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                "type": "SequenceReference",
            },
            "start": 599,
            "end": 600,
        },
        "state": {"sequence": "E", "type": "LiteralSequenceExpression"},
        "expressions": [
            {"syntax": "hgvs.p", "value": "NP_004324.2:p.Val600Glu"},
            {"syntax": "hgvs.c", "value": "NM_004333.4:c.1799T>A"},
            {
                "syntax": "hgvs.c",
                "value": "ENST00000288602.6:c.1799T>A",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000007.13:g.140453136A>T",
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_mpid12(civic_vid12):
    """Create test fixture for CIViC Molecular Profile ID 12"""
    return {
        "id": "civic.mpid:12",
        "type": "ProteinSequenceConsequence",
        "description": "BRAF V600E has been shown to be recurrent in many cancer types. It is one of the most widely studied variants in cancer. This variant is correlated with poor prognosis in certain cancer types, including colorectal cancer and papillary thyroid cancer. The targeted therapeutic dabrafenib has been shown to be effective in clinical trials with an array of BRAF mutations and cancer types. Dabrafenib has also shown to be effective when combined with the MEK inhibitor trametinib in colorectal cancer and melanoma. However, in patients with TP53, CDKN2A and KRAS mutations, dabrafenib resistance has been reported. Ipilimumab, regorafenib, vemurafenib, and a number of combination therapies have been successful in treating V600E mutations. However, cetuximab and panitumumab have been largely shown to be ineffective without supplementary treatment.",
        "label": "BRAF V600E",
        "definingContext": civic_vid12,
        "members": [
            {
                "id": "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe",
                "label": "NC_000007.13:g.140453136A>T",
                "digest": "Otc5ovrw906Ack087o1fhegB4jDRqCAe",
                "type": "Allele",
                "location": {
                    "id": "ga4gh:SL.nhul5x5P_fKjGEpY9PEkMIekJfZaKom2",
                    "digest": "nhul5x5P_fKjGEpY9PEkMIekJfZaKom2",
                    "type": "SequenceLocation",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.F-LrLMe1SRpfUZHkQmvkVKFEGaoDeHul",
                    },
                    "start": 140753335,
                    "end": 140753336,
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            }
        ],
        "aliases": ["VAL600GLU", "V640E", "VAL640GLU"],
        "mappings": [
            {
                "coding": {
                    "code": "CA123643",
                    "system": "https://reg.clinicalgenome.org/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "13961",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "376069",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs113488022",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {"code": "12", "system": "https://civicdb.org/variants/"},
                "relation": "exactMatch",
            },
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
                    "type": "coordinates",
                },
                "type": "Extension",
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 1363.5,
                "type": "Extension",
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "label": "missense_variant",
                        "version": None,
                    }
                ],
                "type": "Extension",
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_vid33():
    """Create a test fixture for CIViC VID33."""
    return {
        "id": "ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ",
        "type": "Allele",
        "label": "L858R",
        "digest": "S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ",
        "location": {
            "id": "ga4gh:SL.v0_edynH98OIu-0QPVT5anCSOriAFSDQ",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
                "type": "SequenceReference",
            },
            "start": 857,
            "end": 858,
        },
        "state": {"sequence": "R", "type": "LiteralSequenceExpression"},
        "expressions": [
            {"syntax": "hgvs.p", "value": "NP_005219.2:p.Leu858Arg"},
            {"syntax": "hgvs.c", "value": "ENST00000275493.2:c.2573T>G"},
            {
                "syntax": "hgvs.c",
                "value": "NM_005228.4:c.2573T>G",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000007.13:g.55259515T>G",
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_gid19():
    """Create test fixture for CIViC GID19."""
    return {
        "id": "civic.gid:19",
        "type": "Gene",
        "label": "EGFR",
        "description": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. Overproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",
        "mappings": [
            {
                "coding": {
                    "code": "ncbigene:1956",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            }
        ],
        "aliases": ["EGFR", "ERBB", "ERBB1", "ERRP", "HER1", "NISBD2", "PIG61", "mENA"],
    }


@pytest.fixture(scope="session")
def civic_tid146():
    """Create test fixture for CIViC TID146."""
    return {
        "id": "civic.tid:146",
        "type": "TherapeuticAgent",
        "label": "Afatinib",
        "mappings": [
            {
                "coding": {
                    "code": "C66940",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "aliases": [
            "BIBW2992",
            "BIBW 2992",
            "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide",
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "FDA",
                    "has_indications": [
                        {
                            "id": "hemonc:642",
                            "type": "Disease",
                            "label": "Non-small cell lung cancer",
                            "mappings": [
                                {
                                    "coding": {"code": "C2926", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:25316",
                            "type": "Disease",
                            "label": "Non-small cell lung cancer squamous",
                        },
                    ],
                },
            },
            {
                "type": "Extension",
                "name": "therapy_normalizer_data",
                "value": {"normalized_id": "rxcui:1430438", "label": "afatinib"},
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_did8():
    """Create test fixture for CIViC DID8."""
    return {
        "id": "civic.did:8",
        "type": "Disease",
        "label": "Lung Non-small Cell Carcinoma",
        "mappings": [
            {
                "coding": {
                    "code": "DOID:3908",
                    "system": "https://www.disease-ontology.org/",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "disease_normalizer_data",
                "value": {
                    "normalized_id": "ncit:C2926",
                    "label": "Lung Non-Small Cell Carcinoma",
                    "mondo_id": "0005233",
                },
            }
        ],
    }


@pytest.fixture(scope="session")
def pmid_23982599():
    """Create test fixture for CIViC EID2997 document."""
    return {
        "id": "pmid:23982599",
        "type": "Document",
        "label": "Dungo et al., 2013",
        "description": "Afatinib: first global approval.",
    }


@pytest.fixture(scope="session")
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
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
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
            "Vectibix",
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "therapy_normalizer_data",
                "value": {"normalized_id": "rxcui:263034", "label": "panitumumab"},
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
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "mesh:D015179",
                            "type": "Disease",
                            "label": "Colorectal Neoplasms",
                            "mappings": [
                                {
                                    "coding": {"code": "C2956", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                    ],
                },
            },
        ],
    }


@pytest.fixture(scope="session")
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
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
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
            "IMC-C225",
        ],
        "extensions": cetuximab_extensions,
    }


@pytest.fixture(scope="session")
def civic_tsg(civic_tid16, civic_tid28):
    """Create test fixture for CIViC TherapeuticSubstituteGroup"""
    return {
        "type": "TherapeuticSubstituteGroup",
        "id": "civic.tsgid:7IxyhCwID0QYyVCP2xuIyYvwwu-S_HrZ",
        "substitutes": [civic_tid16, civic_tid28],
        "extensions": [
            {
                "type": "Extension",
                "name": "civic_therapy_interaction_type",
                "value": "SUBSTITUTES",
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_tid483(encorafenib_extensions):
    """Create test fixture for CIViC Therapy ID 483"""
    return {
        "id": "civic.tid:483",
        "type": "TherapeuticAgent",
        "label": "Encorafenib",
        "mappings": [
            {
                "coding": {
                    "code": "C98283",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "aliases": ["Braftovi", "LGX 818", "LGX-818", "LGX818"],
        "extensions": encorafenib_extensions,
    }


@pytest.fixture(scope="session")
def civic_ct(civic_tid483, civic_tid16):
    """Create test fixture for CIViC CombinationTherapy"""
    return {
        "type": "CombinationTherapy",
        "id": "civic.ctid:P1PY89shAjemg7jquQ0V9pg1VnYnkPeK",
        "components": [civic_tid483, civic_tid16],
        "extensions": [
            {
                "type": "Extension",
                "name": "civic_therapy_interaction_type",
                "value": "COMBINATION",
            }
        ],
    }


@pytest.fixture(scope="session")
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
                    "system": "https://www.disease-ontology.org/",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "disease_normalizer_data",
                "value": {
                    "normalized_id": "ncit:C4978",
                    "label": "Malignant Colorectal Neoplasm",
                    "mondo_id": "0005575",
                },
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_eid816_study(civic_mpid12, civic_tsg, civic_did11, civic_gid5, civic_method):
    """Create CIVIC EID816 study test fixture. Uses TherapeuticSubstituteGroup."""
    return {
        "id": "civic.eid:816",
        "type": "VariantTherapeuticResponseStudy",
        "description": "This meta-analysis of 7 randomized control trials evaluating overall survival (OS) (8 for progression free survival) could not definitely state that survival benefit of anti-EGFR monoclonal antibodies is limited to patients with wild type BRAF. In other words, the authors believe that there is insufficient data to justify the exclusion of anti-EGFR monoclonal antibody therapy for patients with mutant BRAF. In these studies, mutant BRAF specifically meant the V600E mutation.",
        "direction": "refutes",
        "strength": {
            "code": "e000005",
            "label": "clinical cohort evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "predictsResistanceTo",
        "variant": civic_mpid12,
        "therapeutic": civic_tsg,
        "tumorType": civic_did11,
        "qualifiers": {"alleleOrigin": "somatic", "geneContext": civic_gid5},
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:548",
                "label": "Rowland et al., 2015",
                "title": "Meta-analysis of BRAF mutation as a predictive biomarker of benefit from anti-EGFR monoclonal antibody therapy for RAS wild-type metastatic colorectal cancer.",
                "pmid": 25989278,
                "type": "Document",
            }
        ],
    }


@pytest.fixture(scope="session")
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
        "description": "The open-label phase 3 BEACON CRC trial included 665 patients with BRAF V600E-mutated metastatic CRC. Patients were randomly assigned in a 1:1:1 ratio to receive encorafenib, binimetinib, and cetuximab (triplet-therapy group); encorafenib and cetuximab (doublet-therapy group); or the investigators\u2019 choice of either cetuximab and irinotecan or cetuximab and FOLFIRI. The median overall survival was 8.4 months (95% CI, 7.5 to 11.0) in the doublet-therapy group and 5.4 months (95% CI, 4.8 to 6.6) in the control group, with a significantly lower risk of death compared to the control group (hazard ratio for death doublet-group vs. control, 0.60; 95% CI, 0.45 to 0.79; P<0.001). The confirmed response rate was 26% (95% CI, 18 to 35) in the triplet-therapy group, 20% in the doublet-therapy group (95% CI 13 to 29) and 2% (95% CI, 0 to 7) in the control group (doublet group vs. control P<0.001). Median PFS was 4.2 months (95% CI, 3.7 to 5.4) in the doublet-therapy group, and 1.5 months (95% CI, 1.5 to 1.7) in the control group (hazard ratio for disease progression doublet-group vs control, 0.40; 95% CI, 0.31 to 0.52, P<0.001).",
        "direction": "supports",
        "strength": {
            "code": "e000001",
            "label": "authoritative evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "predictsSensitivityTo",
        "variant": civic_mpid12,
        "therapeutic": civic_ct,
        "tumorType": civic_did11,
        "qualifiers": {"alleleOrigin": "somatic", "geneContext": civic_gid5},
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:3025",
                "label": "Kopetz et al., 2019",
                "title": "Encorafenib, Binimetinib, and Cetuximab in BRAF V600E-Mutated Colorectal Cancer.",
                "pmid": 31566309,
                "type": "Document",
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_eid1409_statement():
    """Create test fixture for CIViC Evidence 1406."""
    return {
        "id": "civic.eid:1409",
        "description": "Phase 3 randomized clinical trial comparing vemurafenib with dacarbazine in 675 patients with previously untreated, metastatic melanoma with the BRAF V600E mutation. At 6 months, overall survival was 84% (95% confidence interval [CI], 78 to 89) in the vemurafenib group and 64% (95% CI, 56 to 73) in the dacarbazine group. A relative reduction of 63% in the risk of death and of 74% in the risk of either death or disease progression was observed with vemurafenib as compared with dacarbazine (P<0.001 for both comparisons).",
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:wsW_PurZodw_qHg1Iw8iAR1CUQte1CLA",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:12",
        "therapy_descriptor": "civic.tid:4",
        "disease_descriptor": "civic.did:206",
        "method": "method:1",
        "supported_by": ["pmid:21639808"],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_aid6_statement():
    """Create CIViC AID 6 test fixture."""
    return {
        "id": "civic.aid:6",
        "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved, and is recommended (category 1) by NCCN guidelines along with erlotinib, gefitinib and osimertinib as first line systemic therapy in NSCLC with sensitizing EGFR mutation.",
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:1A",
        "proposition": "proposition:Zfp_VG0uvxwteCcJYO6_AJv1KDmJlFjs",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:33",
        "therapy_descriptor": "civic.tid:146",
        "disease_descriptor": "civic.did:8",
        "method": "method:2",
        "supported_by": [
            "document:9WsQBGXOmTFRXBUanTaIec8Gvgg8bsMA",
            "civic.eid:2997",
            "civic.eid:2629",
            "civic.eid:982",
            "civic.eid:968",
            "civic.eid:883",
            "civic.eid:879",
        ],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_aid6_document():
    """Create test fixture for civic aid6 document."""
    return {
        "id": "document:9WsQBGXOmTFRXBUanTaIec8Gvgg8bsMA",
        "document_id": "https://www.nccn.org/professionals/"
        "physician_gls/default.aspx",
        "label": "NCCN Guidelines: Non-Small Cell Lung Cancer version 3.2018",
        "type": "Document",
    }


@pytest.fixture(scope="session")
def civic_eid2_statement():
    """Create a test fixture for CIViC EID2 statement."""
    return {
        "id": "civic.eid:2",
        "type": "Statement",
        "description": "GIST tumors harboring PDGFRA D842V mutation are more likely to be benign than malignant.",
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:KVuJMXiPm-oK4vvijE9Cakvucayay3jE",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:99",
        "disease_descriptor": "civic.did:2",
        "method": "method:1",
        "supported_by": ["pmid:15146165"],
    }


@pytest.fixture(scope="session")
def civic_eid2_proposition():
    """Create a test fixture for CIViC EID2 proposition."""
    return {
        "id": "proposition:KVuJMXiPm-oK4vvijE9Cakvucayay3jE",
        "type": "diagnostic_proposition",
        "predicate": "is_diagnostic_exclusion_criterion_for",
        "subject": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
        "object_qualifier": "ncit:C3868",
    }


@pytest.fixture(scope="session")
def civic_vid99():
    """Create a test fixture for CIViC VID99."""
    return {
        "id": "civic.vid:99",
        "type": "VariationDescriptor",
        "label": "D842V",
        "description": "PDGFRA D842 mutations are characterized broadly as imatinib resistance mutations. This is most well characterized in gastrointestinal stromal tumors, but other cell lines containing these mutations have been shown to be resistant as well. Exogenous expression of the A842V mutation resulted in constitutive tyrosine phosphorylation of PDGFRA in the absence of ligand in 293T cells and cytokine-independent proliferation of the IL-3-dependent Ba/F3 cell line, both evidence that this is an activating mutation. In imatinib resistant cell lines, a number of other therapeutics have demonstrated efficacy. These include; crenolanib, sirolimus, and midostaurin (PKC412).",
        "variation_id": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
        "variation": {
            "_id": "ga4gh:VA.bjWVYvXPaPbIRAfZvE0Uw_P-i36PGkAz",
            "location": {
                "_id": "ga4gh:VSL.CvhzuX1-CV0in3YTnaq9xZGAPxmrkrFC",
                "interval": {
                    "start": {"value": 841, "type": "Number"},
                    "end": {"value": 842, "type": "Number"},
                    "type": "SequenceInterval",
                },
                "sequence_id": "ga4gh:SQ.XpQn9sZLGv_GU3uiWO7YHq9-_alGjrVX",
                "type": "SequenceLocation",
            },
            "state": {"sequence": "V", "type": "LiteralSequenceExpression"},
            "type": "Allele",
        },
        "xrefs": ["clinvar:13543", "caid:CA123194", "dbsnp:121908585"],
        "alternate_labels": ["ASP842VAL"],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55152093,
                    "stop": 55152093,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000257290.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                },
                "type": "Extension",
            },
            {
                "name": "civic_actionability_score",
                "value": "100.5",
                "type": "Extension",
            },
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic.variant_group:1",
                        "label": "Imatinib Resistance",
                        "description": "While imatinib has shown to be incredibly successful in treating philadelphia chromosome positive CML, patients that have shown primary or secondary resistance to the drug have been observed to harbor T315I and E255K ABL kinase domain mutations. These mutations, among others, have been observed both in primary refractory disease and acquired resistance. In gastrointestinal stromal tumors (GIST), PDGFRA 842 mutations have also been shown to confer resistance to imatinib. ",
                        "type": "variant_group",
                    }
                ],
                "type": "Extension",
            },
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_006206.4:c.2525A>T",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_006197.1:p.Asp842Val",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000257290.5:c.2525A>T",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000004.11:g.55152093A>T",
                "type": "Expression",
            },
        ],
        "gene_context": "civic.gid:38",
    }


@pytest.fixture(scope="session")
def civic_did2():
    """Create a test fixture for CIViC DID2."""
    return {
        "id": "civic.did:2",
        "type": "DiseaseDescriptor",
        "label": "Gastrointestinal Stromal Tumor",
        "disease_id": "ncit:C3868",
        "xrefs": ["DOID:9253"],
    }


@pytest.fixture(scope="session")
def civic_gid38():
    """Create a test fixture for CIViC GID38."""
    return {
        "id": "civic.gid:38",
        "type": "GeneDescriptor",
        "label": "PDGFRA",
        "description": "Commonly mutated in GI tract tumors, PDGFR family genes (mutually exclusive to KIT mutations) are a hallmark of gastrointestinal stromal tumors. Gene fusions involving the PDGFRA kinase domain are highly correlated with eosinophilia, and the WHO classifies myeloid and lymphoid neoplasms with these characteristics as a distinct disorder. Mutations in the 842 region of PDGFRA have been often found to confer resistance to the tyrosine kinase inhibitor, imatinib.",
        "gene_id": "hgnc:8803",
        "alternate_labels": ["PDGFRA", "PDGFR2", "PDGFR-2", "CD140A"],
        "xrefs": ["ncbigene:5156"],
    }


@pytest.fixture(scope="session")
def civic_eid74_statement():
    """Create a test fixture for CIViC EID74 statement."""
    return {
        "id": "civic.eid:74",
        "description": "In patients with medullary carcinoma, the presence of RET M918T mutation is associated with increased probability of lymph node metastases.",
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:Vyzbpg-s6mw27yJfYBFxGyQeuEJacP4l",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:113",
        "disease_descriptor": "civic.did:15",
        "method": "method:1",
        "supported_by": ["pmid:18073307"],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_eid74_proposition():
    """Create a test fixture for CIViC EID74 proposition."""
    return {
        "id": "proposition:Vyzbpg-s6mw27yJfYBFxGyQeuEJacP4l",
        "type": "diagnostic_proposition",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
        "object_qualifier": "ncit:C3879",
    }


@pytest.fixture(scope="session")
def civic_vid113():
    """Create a test fixture for CIViC VID113."""
    return {
        "id": "civic.vid:113",
        "type": "VariationDescriptor",
        "label": "M918T",
        "description": "RET M819T is the most common somatically acquired mutation in medullary thyroid cancer (MTC). While there currently are no RET-specific inhibiting agents, promiscuous kinase inhibitors have seen some success in treating RET overactivity. Data suggests however, that the M918T mutation may lead to drug resistance, especially against the VEGFR-inhibitor motesanib. It has also been suggested that RET M819T leads to more aggressive MTC with a poorer prognosis.",
        "variation_id": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
        "variation": {
            "_id": "ga4gh:VA.GweduWrfxV58YnSvUBfHPGOA-KCH_iIl",
            "location": {
                "_id": "ga4gh:VSL.zkwClPQjjO0FqXWN46QRuiGgodhPjxqT",
                "interval": {
                    "end": {"value": 918, "type": "Number"},
                    "start": {"value": 917, "type": "Number"},
                    "type": "SequenceInterval",
                },
                "sequence_id": "ga4gh:SQ.jMu9-ItXSycQsm4hyABeW_UfSNRXRVnl",
                "type": "SequenceLocation",
            },
            "state": {"sequence": "T", "type": "LiteralSequenceExpression"},
            "type": "Allele",
        },
        "xrefs": ["clinvar:13919", "caid:CA009082", "dbsnp:74799832"],
        "alternate_labels": ["MET918THR"],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "10",
                    "start": 43617416,
                    "stop": 43617416,
                    "reference_bases": "T",
                    "variant_bases": "C",
                    "representative_transcript": "ENST00000355710.3",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                },
                "type": "Extension",
            },
            {"name": "civic_actionability_score", "value": "86", "type": "Extension"},
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic.variant_group:6",
                        "label": "Motesanib Resistance",
                        "description": "RET activation is a common oncogenic marker of medullary thyroid carcinoma. Treatment of these patients with the targeted therapeutic motesanib has shown to be effective. However, the missense mutations C634W and M918T have shown to confer motesanib resistance in cell lines. ",
                        "type": "variant_group",
                    }
                ],
                "type": "Extension",
            },
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_020975.4:c.2753T>C",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_065681.1:p.Met918Thr",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000355710.3:c.2753T>C",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000010.10:g.43617416T>C",
                "type": "Expression",
            },
        ],
        "gene_context": "civic.gid:42",
    }


@pytest.fixture(scope="session")
def civic_did15():
    """Create test fixture for CIViC DID15."""
    return {
        "id": "civic.did:15",
        "type": "DiseaseDescriptor",
        "label": "Thyroid Gland Medullary Carcinoma",
        "disease_id": "ncit:C3879",
        "xrefs": ["DOID:3973"],
    }


@pytest.fixture(scope="session")
def civic_gid42():
    """Create test fixture for CIViC GID42."""
    return {
        "id": "civic.gid:42",
        "type": "GeneDescriptor",
        "label": "RET",
        "description": "RET mutations and the RET fusion RET-PTC lead to activation of this tyrosine kinase receptor and are associated with thyroid cancers. RET point mutations are the most common mutations identified in medullary thyroid cancer (MTC) with germline and somatic mutations in RET associated with hereditary and sporadic forms, respectively. The most common somatic form mutation is M918T (exon 16) and a variety of other mutations effecting exons 10, 11 and 15 have been described. The prognostic significance of these mutations have been hotly debated in the field, however, data suggests that some RET mutation may confer drug resistence. No RET-specific agents are currently clinically available but several promiscuous kinase inhibitors that target RET, among others, have been approved for MTC treatment.",
        "gene_id": "hgnc:9967",
        "alternate_labels": [
            "RET",
            "RET-ELE1",
            "PTC",
            "MTC1",
            "MEN2B",
            "MEN2A",
            "HSCR1",
            "CDHR16",
            "CDHF12",
        ],
        "xrefs": ["ncbigene:5979"],
    }


@pytest.fixture(scope="session")
def civic_aid9_statement():
    """Create a test fixture for CIViC AID9 statement."""
    return {
        "id": "civic.aid:9",
        "description": "ACVR1 G328V mutations occur within the kinase domain, leading to activation of downstream signaling. Exclusively seen in high-grade pediatric gliomas, supporting diagnosis of diffuse intrinsic pontine glioma.",
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:2C",
        "proposition": "proposition:Pjri4dU2VaEKcdKtVkoAUJ8bHFXnW2My",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:1686",
        "disease_descriptor": "civic.did:2950",
        "method": "method:2",
        "supported_by": ["civic.eid:4846", "civic.eid:6955"],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_aid9_proposition():
    """Create a test fixture for CIViC AID9 proposition."""
    return {
        "id": "proposition:Pjri4dU2VaEKcdKtVkoAUJ8bHFXnW2My",
        "predicate": "is_diagnostic_inclusion_criterion_for",
        "subject": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
        "object_qualifier": "DOID:0080684",
        "type": "diagnostic_proposition",
    }


@pytest.fixture(scope="session")
def civic_vid1686():
    """Create a test fixture for CIViC VID1686."""
    return {
        "id": "civic.vid:1686",
        "type": "VariationDescriptor",
        "label": "G328V",
        "variation_id": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
        "variation": {
            "_id": "ga4gh:VA.yuvNtv-SpNOzcGsKsNnnK0n026rbfp6T",
            "location": {
                "_id": "ga4gh:VSL.w84KcAESJfbxvPCwCvYpQajlkdPrfS12",
                "interval": {
                    "end": {"value": 328, "type": "Number"},
                    "start": {"value": 327, "type": "Number"},
                    "type": "SequenceInterval",
                },
                "sequence_id": "ga4gh:SQ.6CnHhDq_bDCsuIBf0AzxtKq_lXYM7f0m",
                "type": "SequenceLocation",
            },
            "state": {"sequence": "V", "type": "LiteralSequenceExpression"},
            "type": "Allele",
        },
        "xrefs": ["clinvar:376363", "caid:CA16602802", "dbsnp:387906589"],
        "alternate_labels": ["GLY328VAL"],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "2",
                    "start": 158622516,
                    "stop": 158622516,
                    "reference_bases": "C",
                    "variant_bases": "A",
                    "representative_transcript": "ENST00000434821.1",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                },
                "type": "Extension",
            },
            {"name": "civic_actionability_score", "value": "30", "type": "Extension"},
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic.variant_group:23",
                        "label": "ACVR1 kinase domain mutation",
                        "type": "variant_group",
                    }
                ],
                "type": "Extension",
            },
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {"syntax": "hgvs.c", "value": "NM_001105.4:c.983G>T", "type": "Expression"},
            {
                "syntax": "hgvs.p",
                "value": "NP_001096.1:p.Gly328Val",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000002.11:g.158622516C>A",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000434821.1:c.983G>T",
                "type": "Expression",
            },
        ],
        "gene_context": "civic.gid:154",
    }


@pytest.fixture(scope="session")
def civic_did2950():
    """Create a test fixture for CIViC DID2950."""
    return {
        "id": "civic.did:2950",
        "type": "DiseaseDescriptor",
        "label": "Diffuse Midline Glioma, H3 K27M-mutant",
        "disease_id": "DOID:0080684",
        "xrefs": ["DOID:0080684"],
    }


@pytest.fixture(scope="session")
def civic_gid154():
    """Create a test fixture for CIViC GID154."""
    return {
        "id": "civic.gid:154",
        "type": "GeneDescriptor",
        "label": "ACVR1",
        "gene_id": "hgnc:171",
        "alternate_labels": [
            "ACVR1",
            "TSRI",
            "SKR1",
            "FOP",
            "ALK2",
            "ACVRLK2",
            "ACVR1A",
            "ACTRI",
        ],
        "xrefs": ["ncbigene:90"],
    }


@pytest.fixture(scope="session")
def civic_eid26_statement():
    """Create a test fixture for CIViC EID26 statement."""
    return {
        "id": "civic.eid:26",
        "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:_HXqJtIo6MSmwagQUSOot4wdKE7O4DyN",
        "variation_origin": "somatic",
        "variation_descriptor": "civic.vid:65",
        "disease_descriptor": "civic.did:3",
        "method": "method:1",
        "supported_by": ["pmid:16384925"],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_eid26_proposition():
    """Create a test fixture for CIViC EID26 proposition."""
    return {
        "id": "proposition:_HXqJtIo6MSmwagQUSOot4wdKE7O4DyN",
        "predicate": "is_prognostic_of_worse_outcome_for",
        "subject": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
        "object_qualifier": "ncit:C3171",
        "type": "prognostic_proposition",
    }


@pytest.fixture(scope="session")
def civic_vid65():
    """Create a test fixture for CIViC VID65."""
    return {
        "id": "civic.vid:65",
        "type": "VariationDescriptor",
        "label": "D816V",
        "description": "KIT D816V is a mutation observed in acute myeloid leukemia (AML). This variant has been linked to poorer prognosis and worse outcome in AML patients.",
        "variation_id": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
        "variation": {
            "_id": "ga4gh:VA.QSLb0bR-CRIFfKIENdHhcuUZwW3IS1aP",
            "location": {
                "_id": "ga4gh:VSL.67qWY-IcFDjFx5DttZ1-5ZMm3v_SC7jI",
                "interval": {
                    "end": {"value": 820, "type": "Number"},
                    "start": {"value": 819, "type": "Number"},
                    "type": "SequenceInterval",
                },
                "sequence_id": "ga4gh:SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB",
                "type": "SequenceLocation",
            },
            "state": {"sequence": "V", "type": "LiteralSequenceExpression"},
            "type": "Allele",
        },
        "xrefs": ["clinvar:13852", "caid:CA123513", "dbsnp:121913507"],
        "alternate_labels": ["ASP816VAL"],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55599321,
                    "stop": 55599321,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288135.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                },
                "type": "Extension",
            },
            {"name": "civic_actionability_score", "value": "67", "type": "Extension"},
            {
                "name": "variant_group",
                "value": [
                    {
                        "id": "civic.variant_group:2",
                        "label": "KIT Exon 17",
                        "type": "variant_group",
                    }
                ],
                "type": "Extension",
            },
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {
                "syntax": "hgvs.c",
                "value": "NM_000222.2:c.2447A>T",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.p",
                "value": "NP_000213.1:p.Asp816Val",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000288135.5:c.2447A>T",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000004.11:g.55599321A>T",
                "type": "Expression",
            },
        ],
        "gene_context": "civic.gid:29",
    }


@pytest.fixture(scope="session")
def civic_did3():
    """Create test fixture for CIViC DID3."""
    return {
        "id": "civic.did:3",
        "type": "DiseaseDescriptor",
        "label": "Acute Myeloid Leukemia",
        "disease_id": "ncit:C3171",
        "xrefs": ["DOID:9119"],
    }


@pytest.fixture(scope="session")
def civic_gid29():
    """Create test fixture for CIViC GID29."""
    return {
        "id": "civic.gid:29",
        "type": "GeneDescriptor",
        "label": "KIT",
        "description": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",
        "gene_id": "hgnc:6342",
        "alternate_labels": ["MASTC", "KIT", "SCFR", "PBT", "CD117", "C-Kit"],
        "xrefs": ["ncbigene:3815"],
    }


@pytest.fixture(scope="session")
def civic_eid1756_statement():
    """Create test fixture for CIViC EID1756 statement."""
    return {
        "id": "civic.eid:1756",
        "description": "Study of 1817 PCa cases and 2026 cancer free controls to clarify the association of (MTHFR)c.677C>T (and c.1298A>C ) of pancreatic cancer risk in a population of Han Chinese in Shanghai. Results indicated a lower risk for the heterozygous CT genotype and homozygous TT genotype carriers of (MTHFR)c.677C>T which had a significantly lower risk of developing pancreatic cancer compared with the wild-type CC genotype.",
        "direction": "supports",
        "evidence_level": "civic.evidence_level:B",
        "proposition": "proposition:cDLAt3AJPrHQPQ--JpKU4MkU528_kE-a",
        "variation_origin": "germline",
        "variation_descriptor": "civic.vid:258",
        "disease_descriptor": "civic.did:556",
        "method": "method:1",
        "supported_by": ["pmid:27819322"],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def civic_eid1756_proposition():
    """Create a test fixture for CIViC EID1756 proposition."""
    return {
        "id": "proposition:cDLAt3AJPrHQPQ--JpKU4MkU528_kE-a",
        "predicate": "is_prognostic_of_better_outcome_for",
        "subject": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
        "object_qualifier": "ncit:C9005",
        "type": "prognostic_proposition",
    }


@pytest.fixture(scope="session")
def civic_vid258():
    """Create a test fixture for CIViC VID258."""
    return {
        "id": "civic.vid:258",
        "type": "VariationDescriptor",
        "label": "A222V",
        "variation_id": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
        "variation": {
            "_id": "ga4gh:VA.Nq7ozfH2X6m1PGr_n38E-F0NZ7I9UASP",
            "location": {
                "_id": "ga4gh:VSL._zGTVJ2unM-BjeDKxGl0IKZtKWQdfOxw",
                "interval": {
                    "end": {"value": 222, "type": "Number"},
                    "start": {"value": 221, "type": "Number"},
                    "type": "SequenceInterval",
                },
                "sequence_id": "ga4gh:SQ.4RSETawLfMkNpQBPepa7Uf9ItHAEJUde",
                "type": "SequenceLocation",
            },
            "state": {"sequence": "V", "type": "LiteralSequenceExpression"},
            "type": "Allele",
        },
        "xrefs": ["clinvar:3520", "caid:CA170990", "dbsnp:1801133"],
        "alternate_labels": ["C677T", "ALA222VAL"],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "1",
                    "start": 11856378,
                    "stop": 11856378,
                    "reference_bases": "G",
                    "variant_bases": "A",
                    "representative_transcript": "ENST00000376592.1",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                },
                "type": "Extension",
            },
            {"name": "civic_actionability_score", "value": "55", "type": "Extension"},
        ],
        "structural_type": "SO:0001583",
        "expressions": [
            {"syntax": "hgvs.c", "value": "NM_005957.4:c.665C>T", "type": "Expression"},
            {
                "syntax": "hgvs.p",
                "value": "NP_005948.3:p.Ala222Val",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.c",
                "value": "ENST00000376592.1:c.665G>A",
                "type": "Expression",
            },
            {
                "syntax": "hgvs.g",
                "value": "NC_000001.10:g.11856378G>A",
                "type": "Expression",
            },
        ],
        "gene_context": "civic.gid:3672",
    }


@pytest.fixture(scope="session")
def civic_did556():
    """Create a test fixture for CIViC DID556."""
    return {
        "id": "civic.did:556",
        "type": "DiseaseDescriptor",
        "label": "Pancreatic Cancer",
        "disease_id": "ncit:C9005",
        "xrefs": ["DOID:1793"],
    }


@pytest.fixture(scope="session")
def civic_gid3672():
    """Create test fixture for CIViC GID3672."""
    return {
        "id": "civic.gid:3672",
        "type": "GeneDescriptor",
        "label": "MTHFR",
        "gene_id": "hgnc:7436",
        "alternate_labels": ["MTHFR"],
        "xrefs": ["ncbigene:4524"],
    }


@pytest.fixture(scope="session")
def pmid_15146165():
    """Create a test fixture for PMID 15146165."""
    return {
        "id": "pmid:15146165",
        "label": "Lasota et al., 2004, Lab. Invest.",
        "type": "Document",
        "description": "A great majority of GISTs with PDGFRA mutations represent gastric tumors of low or no malignant potential.",
    }


@pytest.fixture(scope="session")
def pmid_18073307():
    """Create a test fixture for PMID 18073307."""
    return {
        "type": "Document",
        "id": "pmid:18073307",
        "label": "Elisei et al., 2008, J. Clin. Endocrinol. Metab.",
        "description": "Prognostic significance of somatic RET oncogene mutations in sporadic medullary thyroid cancer: a 10-year follow-up study.",
    }


@pytest.fixture(scope="session")
def pmid_16384925():
    """Create a test fixture for PMID 16384925."""
    return {
        "id": "pmid:16384925",
        "label": "Cairoli et al., 2006, Blood",
        "description": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study.",
        "type": "Document",
    }


@pytest.fixture(scope="session")
def pmid_27819322():
    """Create a test fixture for PMID 27819322."""
    return {
        "type": "Document",
        "id": "pmid:27819322",
        "label": "Wu et al., 2016, Sci Rep",
        "description": "MTHFR c.677C>T Inhibits Cell Proliferation and Decreases Prostate Cancer Susceptibility in the Han Chinese Population in Shanghai.",
        "xrefs": ["pmc:PMC5098242"],
    }


@pytest.fixture(scope="session")
def moa_aid66_study(
    moa_vid66,
    moa_abl1,
    moa_imatinib,
    moa_chronic_myelogenous_leukemia,
    moa_method,
    moa_source44,
):
    """Create a Variant Therapeutic Response Study test fixture for MOA Assertion 66."""
    return {
        "id": "moa.assertion:66",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",
        "direction": "none",
        "strength": {
            "code": "e000009",
            "label": "preclinical evidence",
            "system": "https://go.osu.edu/evidence-codes",
        },
        "predicate": "predictsResistanceTo",
        "variant": moa_vid66,
        "therapeutic": moa_imatinib,
        "tumorType": moa_chronic_myelogenous_leukemia,
        "qualifiers": {"alleleOrigin": "somatic", "geneContext": moa_abl1},
        "specifiedBy": moa_method,
        "isReportedIn": [moa_source44],
        "type": "VariantTherapeuticResponseStudy",
    }


@pytest.fixture(scope="session")
def moa_vid66():
    """Create a test fixture for MOA VID66."""
    return {
        "id": "moa.variant:66",
        "type": "ProteinSequenceConsequence",
        "label": "ABL1 p.T315I (Missense)",
        "definingContext": {
            "id": "ga4gh:VA.D6NzpWXKqBnbcZZrXNSXj4tMUwROKbsQ",
            "digest": "D6NzpWXKqBnbcZZrXNSXj4tMUwROKbsQ",
            "type": "Allele",
            "location": {
                "id": "ga4gh:SL.jGElwyBPYNWI-BkFFHKfgLJynt9zuNPs",
                "digest": "jGElwyBPYNWI-BkFFHKfgLJynt9zuNPs",
                "type": "SequenceLocation",
                "sequenceReference": {
                    "type": "SequenceReference",
                    "refgetAccession": "SQ.dmFigTG-0fY6I54swb7PoDuxCeT6O3Wg",
                },
                "start": 314,
                "end": 315,
            },
            "state": {"type": "LiteralSequenceExpression", "sequence": "I"},
        },
        "extensions": [
            {
                "name": "MOA representative coordinate",
                "value": {
                    "chromosome": "9",
                    "start_position": "133748283",
                    "end_position": "133748283",
                    "reference_allele": "C",
                    "alternate_allele": "T",
                    "cdna_change": "c.944C>T",
                    "protein_change": "p.T315I",
                    "exon": "5",
                },
                "type": "Extension",
            }
        ],
        "mappings": [
            {
                "coding": {
                    "system": "https://moalmanac.org/api/features/",
                    "code": "66",
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                    "code": "rs121913459",
                },
                "relation": "relatedMatch",
            },
        ],
    }


@pytest.fixture(scope="session")
def moa_abl1():
    """Create a test fixture for MOA ABL1 Gene."""
    return {
        "id": "moa.normalize.gene:ABL1",
        "type": "Gene",
        "label": "ABL1",
        "extensions": [
            {"type": "Extension", "name": "gene_normalizer_id", "value": "hgnc:76"}
        ],
    }


@pytest.fixture(scope="session")
def moa_imatinib():
    """Create a test fixture for MOA Imatinib Therapy."""
    return {
        "id": "moa.normalize.therapy.rxcui:282388",
        "type": "TherapeuticAgent",
        "label": "Imatinib",
        "extensions": [
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "FDA",
                    "has_indications": [
                        {
                            "id": "hemonc:669",
                            "type": "Disease",
                            "label": "Systemic mastocytosis",
                            "mappings": [
                                {
                                    "coding": {"code": "C9235", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:582",
                            "type": "Disease",
                            "label": "Chronic myelogenous leukemia",
                            "mappings": [
                                {
                                    "coding": {"code": "C3174", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:24309",
                            "type": "Disease",
                            "label": "Acute lymphoblastic leukemia",
                            "mappings": [
                                {
                                    "coding": {"code": "C3167", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:634",
                            "type": "Disease",
                            "label": "Myelodysplastic syndrome",
                            "mappings": [
                                {
                                    "coding": {"code": "C3247", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:602",
                            "type": "Disease",
                            "label": "Gastrointestinal stromal tumor",
                            "mappings": [
                                {
                                    "coding": {"code": "C3868", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:33893",
                            "type": "Disease",
                            "label": "Chronic myelogenous leukemia pediatric",
                        },
                        {
                            "id": "hemonc:667",
                            "type": "Disease",
                            "label": "Soft tissue sarcoma",
                            "mappings": [
                                {
                                    "coding": {"code": "C9306", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:616",
                            "type": "Disease",
                            "label": "Hypereosinophilic syndrome",
                            "mappings": [
                                {
                                    "coding": {"code": "C27038", "system": "ncit"},
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                    ],
                },
            },
            {
                "type": "Extension",
                "name": "therapy_normalizer_data",
                "value": {"normalized_id": "rxcui:282388", "label": "imatinib"},
            },
        ],
    }


@pytest.fixture(scope="session")
def moa_chronic_myelogenous_leukemia():
    """Create test fixture for MOA Chronic Myelogenous Leukemia."""
    return {
        "id": "moa.normalize.disease.ncit:C3174",
        "type": "Disease",
        "label": "Chronic Myelogenous Leukemia",
        "extensions": [
            {
                "type": "Extension",
                "name": "disease_normalizer_data",
                "value": {
                    "normalized_id": "ncit:C3174",
                    "label": "Chronic Myelogenous Leukemia, BCR-ABL1 Positive",
                    "mondo_id": "0011996",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "label": "Chronic Myelogenous Leukemia",
                    "system": "https://oncotree.mskcc.org/",
                    "code": "CML",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_method():
    """Create test fixture for method:1."""
    return {
        "id": "civic.method:2019",
        "label": "CIViC Curation SOP (2019)",
        "isReportedIn": {
            "label": "Danos et al., 2019, Genome Med.",
            "title": "Standard operating procedure for curation and clinical interpretation of variants in cancer",
            "doi": "10.1186/s13073-019-0687-x",
            "pmid": 31779674,
        },
        "type": "Method",
    }


@pytest.fixture(scope="session")
def moa_method():
    """Create test fixture for MOA."""
    return {
        "id": "moa.method:2021",
        "label": "MOAlmanac (2021)",
        "isReportedIn": {
            "label": "Reardon, B., Moore, N.D., Moore, N.S. et al.",
            "title": "Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
            "doi": "10.1038/s43018-021-00243-3",
            "pmid": 35121878,
        },
        "type": "Method",
    }


@pytest.fixture(scope="session")
def method3():
    """Create test fixture for method:3."""
    return {
        "id": "method:3",
        "label": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology",
        "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
        "version": {"year": 2015, "month": 5},
        "type": "Method",
        "authors": "Richards S, Aziz N, Bale S, et al.",
    }


@pytest.fixture(scope="session")
def method4():
    """Create a test fixture for MOA method:4."""
    return {
        "id": "method:4",
        "label": "Clinical interpretation of integrative molecular profiles to guide precision cancer medicine",
        "url": "https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1",
        "type": "Method",
        "version": {"year": 2020, "month": 9, "day": 22},
        "authors": "Reardon, B., Moore, N.D., Moore, N. et al.",
    }


@pytest.fixture(scope="session")
def civic_methods(civic_method, moa_method, method3):
    """Create test fixture for methods."""
    return [civic_method, moa_method, method3]


@pytest.fixture(scope="session")
def moa_source44():
    """Create a test fixture for MOA source 44."""
    return {
        "id": "moa.source:44",
        "extensions": [
            {"type": "Extension", "name": "source_type", "value": "Journal"}
        ],
        "type": "Document",
        "title": "Gorre, Mercedes E., et al. Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification. Science 293.5531 (2001): 876-880.",
        "url": "https://doi.org/10.1126/science.1062538",
        "doi": "10.1126/science.1062538",
        "pmid": 11423618,
    }


def _dict_check(expected_d: dict, actual_d: dict, is_cdm: bool = False) -> None:
    """Make dictionary assertion checks. Check that actual matches expected data.

    :param expected_d: Expected dictionary
    :param actual_d: Actual dictionary
    :param is_cdm: Whether checks are for transformers (CDM) or query handler.
        CDM have extra fields that are not exposed to the query handler
    """
    for k, v in expected_d.items():
        if isinstance(v, dict):
            _dict_check(v, actual_d[k], is_cdm=is_cdm)
        elif isinstance(v, list):
            actual_l = [json.dumps(v, sort_keys=True) for v in actual_d[k]]
            if is_cdm:
                expected_l = [json.dumps(v, sort_keys=True) for v in expected_d[k]]
            else:
                expected_l = []
                for v in expected_d[k]:
                    if isinstance(v, dict):
                        if v.get("name") in {
                            "therapy_normalizer_data",
                            "disease_normalizer_data",
                        }:
                            updated_ext = v.copy()
                            normalizer_data_type = v["name"].split("_normalizer_data")[
                                0
                            ]
                            updated_ext[
                                "name"
                            ] = f"{normalizer_data_type}_normalizer_id"
                            updated_ext["value"] = v["value"]["normalized_id"]
                            expected_l.append(json.dumps(updated_ext, sort_keys=True))
                            continue
                        new_extensions = []
                        extensions = v.get("extensions") or []
                        for ext in extensions:
                            if ext.get("name") in {
                                "therapy_normalizer_data",
                                "disease_normalizer_data",
                            }:
                                normalizer_data_type = ext["name"].split(
                                    "_normalizer_data"
                                )[0]
                                new_extensions.append(
                                    {
                                        "name": f"{normalizer_data_type}_normalizer_id",
                                        "type": "Extension",
                                        "value": ext["value"]["normalized_id"],
                                    }
                                )
                            else:
                                new_extensions.append(ext)
                        if extensions:
                            v["extensions"] = new_extensions
                    expected_l.append(json.dumps(v, sort_keys=True))
            assert set(actual_l) == set(expected_l), k
        else:
            assert actual_d[k] == expected_d[k], k


@pytest.fixture(scope="session")
def assertion_checks():
    """Check that actual data matches expected data

    :param actual_data: List of actual data
    :param test_data: List of expected data
    :param is_cdm: Whether checks are for transformers (CDM) or query handler.
        CDM have extra fields that are not exposed to the query handler
    """

    def _check(actual_data: list, test_data: list, is_cdm: bool = False) -> None:
        assert len(actual_data) == len(test_data)
        for expected in test_data:
            found_match = False
            for actual in actual_data:
                if actual["id"] == expected["id"]:
                    found_match = True
                    assert actual.keys() == expected.keys()
                    expected_copy = deepcopy(expected)
                    _dict_check(expected_copy, actual, is_cdm=is_cdm)
                    continue

            assert found_match, f"Did not find {expected['id']} in response"

    return _check


@pytest.fixture(scope="session")
def check_transformed_cdm(assertion_checks):
    """Test fixture to compare CDM transformations."""

    def check_transformed_cdm(data, studies, transformed_file):
        """Test that transform to CDM works correctly."""
        assertion_checks(data["studies"], studies, is_cdm=True)
        transformed_file.unlink()

    return check_transformed_cdm


@pytest.fixture(scope="module")
def normalizers():
    """Provide normalizers to querying/transformation tests."""
    return ViccNormalizers()
