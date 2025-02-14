"""Module for pytest fixtures."""

import logging
from copy import deepcopy
from pathlib import Path

import pytest
from deepdiff import DeepDiff

from metakb.harvesters.base import Harvester
from metakb.normalizers import VICC_NORMALIZER_DATA, ViccNormalizers
from metakb.query import QueryHandler

TEST_DATA_DIR = Path(__file__).resolve().parents[0] / "data"
TEST_HARVESTERS_DIR = TEST_DATA_DIR / "harvesters"
TEST_TRANSFORMERS_DIR = TEST_DATA_DIR / "transformers"


def pytest_addoption(parser):
    """Add custom commands to pytest invocation.

    See https://docs.pytest.org/en/7.1.x/reference/reference.html#parser
    """
    parser.addoption(
        "--verbose-logs",
        action="store_true",
        default=False,
        help="show noisy module logs",
    )


def pytest_configure(config):
    """Configure pytest setup."""
    logging.getLogger(__name__).error(config.getoption("--verbose-logs"))
    if not config.getoption("--verbose-logs"):
        for lib in (
            "botocore",
            "boto3",
            "urllib3.connectionpool",
            "neo4j.pool",
            "neo4j.io",
        ):
            logging.getLogger(lib).setLevel(logging.ERROR)


def check_source_harvest(tmp_path: Path, harvester: Harvester):
    """Test that source harvest method works correctly"""
    harvested_data = harvester.harvest()
    harvested_filepath = tmp_path / f"{harvester.__class__.__name__.lower()}.json"

    try:
        harvester.save_harvested_data_to_file(
            harvested_data, harvested_filepath=harvested_filepath
        )
        assert harvested_filepath.exists()
    finally:
        if harvested_filepath.exists():
            harvested_filepath.unlink()
        assert not harvested_filepath.exists()


@pytest.fixture(scope="session")
def cetuximab_extensions():
    """Create test fixture for cetuximab extensions"""
    return [
        {
            "name": VICC_NORMALIZER_DATA,
            "value": {"id": "rxcui:318341", "label": "cetuximab"},
        },
        {
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "ChEMBL",
                "has_indications": [
                    {
                        "id": "mesh:D009369",
                        "conceptType": "Disease",
                        "label": "Neoplasms",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C3262",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D015179",
                        "conceptType": "Disease",
                        "label": "Colorectal Neoplasms",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C2956",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D006258",
                        "conceptType": "Disease",
                        "label": "Head and Neck Neoplasms",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C4013",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D002294",
                        "conceptType": "Disease",
                        "label": "Carcinoma, Squamous Cell",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C2929",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
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
            "name": VICC_NORMALIZER_DATA,
            "value": {
                "id": "rxcui:2049106",
                "label": "encorafenib",
            },
        },
        {
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "ChEMBL",
                "has_indications": [
                    {
                        "id": "mesh:D008545",
                        "conceptType": "Disease",
                        "label": "Melanoma",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C3224",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D009369",
                        "conceptType": "Disease",
                        "label": "Neoplasms",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C3262",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
                                "relation": "relatedMatch",
                            }
                        ],
                    },
                    {
                        "id": "mesh:D015179",
                        "conceptType": "Disease",
                        "label": "Colorectal Neoplasms",
                        "mappings": [
                            {
                                "coding": {
                                    "code": "ncit:C2956",
                                    "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                },
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
        "type": "CategoricalVariant",
        "description": "EGFR L858R has long been recognized as a functionally significant mutation in cancer, and is one of the most prevalent single mutations in lung cancer. Best described in non-small cell lung cancer (NSCLC), the mutation seems to confer sensitivity to first and second generation TKI's like gefitinib and neratinib. NSCLC patients with this mutation treated with TKI's show increased overall and progression-free survival, as compared to chemotherapy alone. Third generation TKI's are currently in clinical trials that specifically focus on mutant forms of EGFR, a few of which have shown efficacy in treating patients that failed to respond to earlier generation TKI therapies.",
        "label": "EGFR L858R",
        "constraints": [{"allele": civic_vid33, "type": "DefiningAlleleConstraint"}],
        "members": [
            {
                "id": "ga4gh:VA.gV7_dnvF8SQSeUdvgDFhU65zK_csc6VE",
                "type": "Allele",
                "label": "NM_005228.4:c.2573T>G",
                "digest": "gV7_dnvF8SQSeUdvgDFhU65zK_csc6VE",
                "location": {
                    "id": "ga4gh:SL.LREsUiEYvOrRhwXW1rG72kXFPegvkNzI",
                    "type": "SequenceLocation",
                    "digest": "LREsUiEYvOrRhwXW1rG72kXFPegvkNzI",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.d_QsP29RWJi6bac7GOC9cJ9AO7s_HUMN",
                    },
                    "start": 2833,
                    "end": 2834,
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "G"},
                "expressions": [{"syntax": "hgvs.c", "value": "NM_005228.4:c.2573T>G"}],
            },
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
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "G"},
                "expressions": [
                    {"syntax": "hgvs.g", "value": "NC_000007.13:g.55259515T>G"}
                ],
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA126713",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
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
                "coding": {
                    "id": "civic.vid:33",
                    "code": "33",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            {"name": "aliases", "value": ["LEU858ARG"]},
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
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 379.0,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001583",
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "label": "missense_variant",
                    }
                ],
            },
        ],
    }


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
def civic_eid2997_study_stmt(
    civic_mpid33,
    civic_tid146,
    civic_did8,
    civic_gid19,
    civic_method,
    civic_source592,
):
    """Create CIVIC EID2997 Study Statement test fixture. Uses Therapy."""
    return {
        "id": "civic.eid:2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",
        "direction": "supports",
        "strength": {
            "primaryCode": "e000001",
            "label": "authoritative evidence",
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "objectTherapeutic": civic_tid146,
            "conditionQualifier": civic_did8,
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": civic_gid19,
            "subjectVariant": civic_mpid33,
        },
        "specifiedBy": civic_method,
        "reportedIn": [civic_source592],
    }


@pytest.fixture(scope="session")
def civic_gid5():
    """Create test fixture for CIViC GID5."""
    return {
        "id": "civic.gid:5",
        "conceptType": "Gene",
        "label": "BRAF",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:673",
                    "code": "673",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": "description",
                "value": "BRAF mutations are found to be recurrent in many cancer types. Of these, the mutation of valine 600 to glutamic acid (V600E) is the most prevalent. V600E has been determined to be an activating mutation, and cells that harbor it, along with other V600 mutations are sensitive to the BRAF inhibitor dabrafenib. It is also common to use MEK inhibition as a substitute for BRAF inhibitors, and the MEK inhibitor trametinib has seen some success in BRAF mutant melanomas. BRAF mutations have also been correlated with poor prognosis in many cancer types, although there is at least one study that questions this conclusion in papillary thyroid cancer.\n\nOncogenic BRAF mutations are divided into three categories that determine their sensitivity to inhibitors.\nClass 1 BRAF mutations (V600) are RAS-independent, signal as monomers and are sensitive to current RAF monomer inhibitors.\nClass 2 BRAF mutations (K601E, K601N, K601T, L597Q, L597V, G469A, G469V, G469R, G464V, G464E, and fusions) are RAS-independent, signaling as constitutive dimers and are resistant to vemurafenib. Such mutants may be sensitive to novel RAF dimer inhibitors or MEK inhibitors.\nClass 3 BRAF mutations (D287H, V459L, G466V, G466E, G466A, S467L, G469E, N581S, N581I, D594N, D594G, D594A, D594H, F595L, G596D, and G596R) with low or absent kinase activity are RAS-dependent and they activate ERK by increasing their binding to activated RAS and wild-type CRAF. Class 3 BRAF mutations coexist with mutations in RAS or NF1 in melanoma may be treated with MEK inhibitors. In epithelial tumors such as CRC or NSCLC may be effectively treated with combinations that include inhibitors of receptor tyrosine kinase.",
            },
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {"id": "hgnc:1097", "label": "BRAF"},
            },
            {
                "name": "aliases",
                "value": [
                    "B-RAF1",
                    "B-raf",
                    "BRAF",
                    "BRAF-1",
                    "BRAF1",
                    "NS7",
                    "RAFB1",
                ],
            },
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
            "digest": "t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                "type": "SequenceReference",
            },
            "start": 599,
            "end": 600,
            "sequence": "V",
        },
        "state": {"sequence": "E", "type": "LiteralSequenceExpression"},
        "expressions": [
            {"syntax": "hgvs.p", "value": "NP_004324.2:p.Val600Glu"},
        ],
    }


@pytest.fixture(scope="session")
def braf_v600e_genomic():
    """Genomic representation for BRAF V600E"""
    return {
        "id": "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe",
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
            "sequence": "A",
        },
        "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
    }


@pytest.fixture(scope="session")
def civic_mpid12(civic_vid12, braf_v600e_genomic):
    """Create test fixture for CIViC Molecular Profile ID 12"""
    genomic_rep = braf_v600e_genomic.copy()
    genomic_rep["label"] = "NC_000007.13:g.140453136A>T"
    genomic_rep["expressions"] = [
        {"syntax": "hgvs.g", "value": "NC_000007.13:g.140453136A>T"}
    ]

    return {
        "id": "civic.mpid:12",
        "type": "CategoricalVariant",
        "description": "BRAF V600E has been shown to be recurrent in many cancer types. It is one of the most widely studied variants in cancer. This variant is correlated with poor prognosis in certain cancer types, including colorectal cancer and papillary thyroid cancer. The targeted therapeutic dabrafenib has been shown to be effective in clinical trials with an array of BRAF mutations and cancer types. Dabrafenib has also shown to be effective when combined with the MEK inhibitor trametinib in colorectal cancer and melanoma. However, in patients with TP53, CDKN2A and KRAS mutations, dabrafenib resistance has been reported. Ipilimumab, regorafenib, vemurafenib, and a number of combination therapies have been successful in treating V600E mutations. However, cetuximab and panitumumab have been largely shown to be ineffective without supplementary treatment.",
        "label": "BRAF V600E",
        "constraints": [{"allele": civic_vid12, "type": "DefiningAlleleConstraint"}],
        "members": [
            genomic_rep,
            {
                "id": "ga4gh:VA.W6xsV-aFm9yT2Bic5cFAV2j0rll6KK5R",
                "type": "Allele",
                "label": "NM_004333.4:c.1799T>A",
                "digest": "W6xsV-aFm9yT2Bic5cFAV2j0rll6KK5R",
                "expressions": [{"syntax": "hgvs.c", "value": "NM_004333.4:c.1799T>A"}],
                "location": {
                    "id": "ga4gh:SL.8HBKs9fzlT3tKWlM03REjkg_0Om6Y33U",
                    "type": "SequenceLocation",
                    "digest": "8HBKs9fzlT3tKWlM03REjkg_0Om6Y33U",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.aKMPEJgmlZXt_F6gRY5cUG3THH2n-GUa",
                    },
                    "start": 2024,
                    "end": 2025,
                    "sequence": "T",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "A"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA123643",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
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
                "coding": {
                    "id": "civic.vid:12",
                    "code": "12",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            {"name": "aliases", "value": ["VAL600GLU", "V640E", "VAL640GLU"]},
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
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 1378.5,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001583",
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "label": "missense_variant",
                    }
                ],
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
            "digest": "v0_edynH98OIu-0QPVT5anCSOriAFSDQ",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
                "type": "SequenceReference",
            },
            "start": 857,
            "end": 858,
            "sequence": "L",
        },
        "state": {"sequence": "R", "type": "LiteralSequenceExpression"},
        "expressions": [
            {"syntax": "hgvs.p", "value": "NP_005219.2:p.Leu858Arg"},
        ],
    }


@pytest.fixture(scope="session")
def civic_gid19():
    """Create test fixture for CIViC GID19."""
    return {
        "id": "civic.gid:19",
        "conceptType": "Gene",
        "label": "EGFR",
        "mappings": [
            {
                "coding": {
                    "id": "ncbigene:1956",
                    "code": "1956",
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": "description",
                "value": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. Overproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",
            },
            {
                "name": "aliases",
                "value": [
                    "EGFR",
                    "ERBB",
                    "ERBB1",
                    "ERRP",
                    "HER1",
                    "NISBD2",
                    "PIG61",
                    "mENA",
                ],
            },
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {"id": "hgnc:3236", "label": "EGFR"},
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_tid146():
    """Create test fixture for CIViC TID146."""
    return {
        "id": "civic.tid:146",
        "conceptType": "Therapy",
        "label": "Afatinib",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C66940",
                    "code": "C66940",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": "aliases",
                "value": [
                    "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide",
                    "BIBW 2992",
                    "BIBW2992",
                ],
            },
            {
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "FDA",
                    "has_indications": [
                        {
                            "id": "hemonc:642",
                            "conceptType": "Disease",
                            "label": "Non-small cell lung cancer",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C2926",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:25316",
                            "conceptType": "Disease",
                            "label": "Non-small cell lung cancer squamous",
                        },
                    ],
                },
            },
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "rxcui:1430438",
                    "label": "afatinib",
                },
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_did8():
    """Create test fixture for CIViC DID8."""
    return {
        "id": "civic.did:8",
        "conceptType": "Disease",
        "label": "Lung Non-small Cell Carcinoma",
        "mappings": [
            {
                "coding": {
                    "id": "DOID:3908",
                    "code": "DOID:3908",
                    "system": "https://disease-ontology.org/?id=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "ncit:C2926",
                    "label": "Lung Non-Small Cell Carcinoma",
                    "mondo_id": "mondo:0005233",
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
        "conceptType": "Therapy",
        "label": "Panitumumab",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C1857",
                    "code": "C1857",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": "aliases",
                "value": [
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
            },
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "rxcui:263034",
                    "label": "panitumumab",
                },
            },
            {
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "conceptType": "Disease",
                            "label": "Neoplasms",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C3262",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "mesh:D015179",
                            "conceptType": "Disease",
                            "label": "Colorectal Neoplasms",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C2956",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
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
        "conceptType": "Therapy",
        "label": "Cetuximab",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C1723",
                    "code": "C1723",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            *cetuximab_extensions,
            {
                "name": "aliases",
                "value": [
                    "Cetuximab Biosimilar CDP-1",
                    "Cetuximab Biosimilar CMAB009",
                    "Cetuximab Biosimilar KL 140",
                    "Chimeric Anti-EGFR Monoclonal Antibody",
                    "Chimeric MoAb C225",
                    "Chimeric Monoclonal Antibody C225",
                    "Erbitux",
                    "IMC-C225",
                ],
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_tsg(civic_tid16, civic_tid28):
    """Create test fixture for CIViC therapy subsitutes"""
    return {
        "id": "civic.tsgid:7IxyhCwID0QYyVCP2xuIyYvwwu-S_HrZ",
        "therapies": [civic_tid16, civic_tid28],
        "groupType": {"label": "TherapeuticSubstituteGroup"},
        "extensions": [
            {
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
        "conceptType": "Therapy",
        "label": "Encorafenib",
        "mappings": [
            {
                "coding": {
                    "id": "ncit:C98283",
                    "code": "C98283",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            *encorafenib_extensions,
            {"name": "aliases", "value": ["Braftovi", "LGX 818", "LGX-818", "LGX818"]},
        ],
    }


@pytest.fixture(scope="session")
def civic_ct(civic_tid483, civic_tid16):
    """Create test fixture for CIViC combination therapy"""
    return {
        "id": "civic.ctid:P1PY89shAjemg7jquQ0V9pg1VnYnkPeK",
        "therapies": [civic_tid483, civic_tid16],
        "groupType": {"label": "CombinationTherapy"},
        "extensions": [
            {
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
        "conceptType": "Disease",
        "label": "Colorectal Cancer",
        "mappings": [
            {
                "coding": {
                    "id": "DOID:9256",
                    "code": "DOID:9256",
                    "system": "https://disease-ontology.org/?id=",
                },
                "relation": "exactMatch",
            }
        ],
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "ncit:C4978",
                    "label": "Malignant Colorectal Neoplasm",
                    "mondo_id": "mondo:0005575",
                },
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_eid816_study_stmt(
    civic_mpid12, civic_tsg, civic_did11, civic_gid5, civic_method
):
    """Create CIVIC EID816 study statement test fixture. Uses TherapeuticSubstituteGroup."""
    return {
        "id": "civic.eid:816",
        "type": "Statement",
        "description": "This meta-analysis of 7 randomized control trials evaluating overall survival (OS) (8 for progression free survival) could not definitely state that survival benefit of anti-EGFR monoclonal antibodies is limited to patients with wild type BRAF. In other words, the authors believe that there is insufficient data to justify the exclusion of anti-EGFR monoclonal antibody therapy for patients with mutant BRAF. In these studies, mutant BRAF specifically meant the V600E mutation.",
        "direction": "disputes",
        "strength": {
            "primaryCode": "e000005",
            "label": "clinical cohort evidence",
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsResistanceTo",
            "subjectVariant": civic_mpid12,
            "objectTherapeutic": civic_tsg,
            "conditionQualifier": civic_did11,
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": civic_gid5,
        },
        "specifiedBy": civic_method,
        "reportedIn": [
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
def civic_eid9851_study_stmt(
    civic_mpid12,
    civic_ct,
    civic_did11,
    civic_gid5,
    civic_method,
):
    """Create CIVIC EID9851 study statement test fixture. Uses CombinationTherapy."""
    return {
        "id": "civic.eid:9851",
        "type": "Statement",
        "description": "The open-label phase 3 BEACON CRC trial included 665 patients with BRAF V600E-mutated metastatic CRC. Patients were randomly assigned in a 1:1:1 ratio to receive encorafenib, binimetinib, and cetuximab (triplet-therapy group); encorafenib and cetuximab (doublet-therapy group); or the investigators\u2019 choice of either cetuximab and irinotecan or cetuximab and FOLFIRI. The median overall survival was 8.4 months (95% CI, 7.5 to 11.0) in the doublet-therapy group and 5.4 months (95% CI, 4.8 to 6.6) in the control group, with a significantly lower risk of death compared to the control group (hazard ratio for death doublet-group vs. control, 0.60; 95% CI, 0.45 to 0.79; P<0.001). The confirmed response rate was 26% (95% CI, 18 to 35) in the triplet-therapy group, 20% in the doublet-therapy group (95% CI 13 to 29) and 2% (95% CI, 0 to 7) in the control group (doublet group vs. control P<0.001). Median PFS was 4.2 months (95% CI, 3.7 to 5.4) in the doublet-therapy group, and 1.5 months (95% CI, 1.5 to 1.7) in the control group (hazard ratio for disease progression doublet-group vs control, 0.40; 95% CI, 0.31 to 0.52, P<0.001).",
        "direction": "supports",
        "strength": {
            "primaryCode": "e000001",
            "label": "authoritative evidence",
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "subjectVariant": civic_mpid12,
            "objectTherapeutic": civic_ct,
            "conditionQualifier": civic_did11,
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": civic_gid5,
        },
        "specifiedBy": civic_method,
        "reportedIn": [
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
def civic_eid26_study_stmt(
    civic_mpid65, civic_gid29, civic_did3, civic_method, pmid_16384925
):
    """Create a test fixture for CIViC EID26 study statement."""
    return {
        "id": "civic.eid:26",
        "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",
        "direction": "supports",
        "strength": {
            "primaryCode": "e000005",
            "label": "clinical cohort evidence",
        },
        "proposition": {
            "type": "VariantPrognosticProposition",
            "predicate": "associatedWithWorseOutcomeFor",
            "alleleOriginQualifier": {"label": "somatic"},
            "subjectVariant": civic_mpid65,
            "geneContextQualifier": civic_gid29,
            "objectCondition": civic_did3,
        },
        "specifiedBy": civic_method,
        "reportedIn": [pmid_16384925],
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
    """Create test fixture for CIViC Variant ID 65"""
    return {
        "id": "ga4gh:VA.nhiDwIq1klrGm3wtWO4a4BiS0jdW79Wd",
        "type": "Allele",
        "label": "D816V",
        "digest": "nhiDwIq1klrGm3wtWO4a4BiS0jdW79Wd",
        "location": {
            "id": "ga4gh:SL.FDPpCHrDqH_pR10oxpHZ17tyGhZXVnsj",
            "digest": "FDPpCHrDqH_pR10oxpHZ17tyGhZXVnsj",
            "type": "SequenceLocation",
            "sequenceReference": {
                "refgetAccession": "SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB",
                "type": "SequenceReference",
            },
            "start": 815,
            "end": 816,
            "sequence": "D",
        },
        "state": {"sequence": "V", "type": "LiteralSequenceExpression"},
        "expressions": [
            {"syntax": "hgvs.p", "value": "NP_000213.1:p.Asp816Val"},
        ],
    }


@pytest.fixture(scope="session")
def civic_mpid65(civic_vid65):
    """Create a test fixture for CIViC VID65."""
    return {
        "id": "civic.mpid:65",
        "type": "CategoricalVariant",
        "description": "KIT D816V is a mutation observed in acute myeloid leukemia (AML). This variant has been linked to poorer prognosis and worse outcome in AML patients.",
        "label": "KIT D816V",
        "constraints": [{"allele": civic_vid65, "type": "DefiningAlleleConstraint"}],
        "members": [
            {
                "id": "ga4gh:VA.MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "type": "Allele",
                "label": "NM_000222.2:c.2447A>T",
                "digest": "MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "expressions": [{"syntax": "hgvs.c", "value": "NM_000222.2:c.2447A>T"}],
                "location": {
                    "id": "ga4gh:SL.vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "type": "SequenceLocation",
                    "digest": "vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.5UOthuwxqhwdsrbA4bVonC2ps_Njx1gh",
                    },
                    "start": 2504,
                    "end": 2505,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
            {
                "id": "ga4gh:VA.MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "type": "Allele",
                "label": "ENST00000288135.5:c.2447A>T",
                "digest": "MQQ62X5KMlj9gDKjOkE1lIZjAY9k_7g4",
                "expressions": [
                    {"syntax": "hgvs.c", "value": "ENST00000288135.5:c.2447A>T"}
                ],
                "location": {
                    "id": "ga4gh:SL.vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "type": "SequenceLocation",
                    "digest": "vfWDYUfL2sqohE0wtojKCZ6PlLAPPvjl",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.5UOthuwxqhwdsrbA4bVonC2ps_Njx1gh",
                    },
                    "start": 2504,
                    "end": 2505,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
            {
                "id": "ga4gh:VA.UQJIH49-agpdZzdyGiM4NQE_njoQy0m6",
                "type": "Allele",
                "label": "NC_000004.11:g.55599321A>T",
                "digest": "UQJIH49-agpdZzdyGiM4NQE_njoQy0m6",
                "expressions": [
                    {"syntax": "hgvs.g", "value": "NC_000004.11:g.55599321A>T"}
                ],
                "location": {
                    "id": "ga4gh:SL.aAqDEdLIeXIQOX6LaJaaiOuC7lgo_DZk",
                    "type": "SequenceLocation",
                    "digest": "aAqDEdLIeXIQOX6LaJaaiOuC7lgo_DZk",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.HxuclGHh0XCDuF8x6yQrpHUBL7ZntAHc",
                    },
                    "start": 54733154,
                    "end": 54733155,
                    "sequence": "A",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "code": "CA123513",
                    "system": "https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "13852",
                    "system": "https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "code": "rs121913507",
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                },
                "relation": "relatedMatch",
            },
            {
                "coding": {
                    "id": "civic.vid:65",
                    "code": "65",
                    "system": "https://civicdb.org/variants/",
                },
                "relation": "exactMatch",
            },
        ],
        "extensions": [
            {"name": "aliases", "value": ["ASP816VAL"]},
            {
                "name": "CIViC representative coordinate",
                "value": {
                    "chromosome": "4",
                    "start": 55599321,
                    "stop": 55599321,
                    "reference_bases": "A",
                    "variant_bases": "T",
                    "representative_transcript": "ENST00000288135.5",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37",
                    "type": "coordinates",
                },
            },
            {
                "name": "CIViC Molecular Profile Score",
                "value": 67.0,
            },
            {
                "name": "Variant types",
                "value": [
                    {
                        "id": "SO:0001583",
                        "code": "SO:0001583",
                        "system": "http://www.sequenceontology.org/browser/current_svn/term/",
                        "label": "missense_variant",
                    }
                ],
            },
        ],
    }


@pytest.fixture(scope="session")
def civic_did3():
    """Create test fixture for CIViC DID3."""
    return {
        "id": "civic.did:3",
        "conceptType": "Disease",
        "label": "Acute Myeloid Leukemia",
        "extensions": [
            {
                "name": "vicc_normalizer_data",
                "value": {
                    "id": "ncit:C3171",
                    "label": "Acute Myeloid Leukemia",
                    "mondo_id": "mondo:0018874",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "id": "DOID:9119",
                    "system": "https://disease-ontology.org/?id=",
                    "code": "DOID:9119",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="session")
def civic_gid29():
    """Create test fixture for CIViC GID29."""
    return {
        "id": "civic.gid:29",
        "conceptType": "Gene",
        "label": "KIT",
        "extensions": [
            {
                "name": "description",
                "value": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",
            },
            {
                "name": "aliases",
                "value": ["MASTC", "KIT", "SCFR", "PBT", "CD117", "C-Kit"],
            },
            {
                "name": "vicc_normalizer_data",
                "value": {"id": "hgnc:6342", "label": "KIT"},
            },
        ],
        "mappings": [
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/gene/",
                    "id": "ncbigene:3815",
                    "code": "3815",
                },
                "relation": "exactMatch",
            }
        ],
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
        "id": "civic.source:69",
        "label": "Cairoli et al., 2006",
        "title": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study.",
        "pmid": 16384925,
        "type": "Document",
    }


@pytest.fixture(scope="session")
def moa_aid66_study_stmt(
    moa_vid66,
    moa_abl1,
    moa_imatinib,
    moa_chronic_myelogenous_leukemia,
    moa_method,
    moa_source45,
):
    """Create a Variant Therapeutic Response Study Statement test fixture for MOA Assertion 66."""
    return {
        "id": "moa.assertion:66",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",
        "strength": {
            "primaryCode": "e000009",
            "label": "preclinical evidence",
        },
        "direction": "supports",
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsResistanceTo",
            "subjectVariant": moa_vid66,
            "objectTherapeutic": moa_imatinib,
            "conditionQualifier": moa_chronic_myelogenous_leukemia,
            "alleleOriginQualifier": {"label": "somatic"},
            "geneContextQualifier": moa_abl1,
        },
        "specifiedBy": moa_method,
        "reportedIn": [moa_source45],
        "type": "Statement",
    }


@pytest.fixture(scope="session")
def moa_vid66():
    """Create a test fixture for MOA VID66."""
    return {
        "id": "moa.variant:66",
        "type": "CategoricalVariant",
        "label": "ABL1 p.T315I (Missense)",
        "constraints": [
            {
                "allele": {
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
                        "sequence": "T",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "I"},
                },
                "type": "DefiningAlleleConstraint",
            }
        ],
        "members": [
            {
                "id": "ga4gh:VA.HUJOQCml0LngKmUf5IJIYQk9CfKmagbf",
                "label": "9-133748283-C-T",
                "digest": "HUJOQCml0LngKmUf5IJIYQk9CfKmagbf",
                "type": "Allele",
                "location": {
                    "id": "ga4gh:SL.vd9Kb9rCPWBEUZ_wbBxZyulgOAq-jk0P",
                    "digest": "vd9Kb9rCPWBEUZ_wbBxZyulgOAq-jk0P",
                    "type": "SequenceLocation",
                    "sequenceReference": {
                        "type": "SequenceReference",
                        "refgetAccession": "SQ.KEO-4XBcm1cxeo_DIQ8_ofqGUkp4iZhI",
                    },
                    "start": 133748282,
                    "end": 133748283,
                    "sequence": "C",
                },
                "state": {"type": "LiteralSequenceExpression", "sequence": "T"},
            }
        ],
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
            }
        ],
        "mappings": [
            {
                "coding": {
                    "id": "moa.variant:66",
                    "system": "https://moalmanac.org",
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
        "conceptType": "Gene",
        "label": "ABL1",
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {"id": "hgnc:76", "label": "ABL1"},
            }
        ],
    }


@pytest.fixture(scope="session")
def moa_imatinib():
    """Create a test fixture for MOA Imatinib Therapy."""
    return {
        "id": "moa.normalize.therapy.rxcui:282388",
        "conceptType": "Therapy",
        "label": "Imatinib",
        "extensions": [
            {
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "FDA",
                    "has_indications": [
                        {
                            "id": "hemonc:669",
                            "conceptType": "Disease",
                            "label": "Systemic mastocytosis",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C9235",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:582",
                            "conceptType": "Disease",
                            "label": "Chronic myeloid leukemia",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C3174",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:24309",
                            "conceptType": "Disease",
                            "label": "Acute lymphoblastic leukemia",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C3167",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:634",
                            "conceptType": "Disease",
                            "label": "Myelodysplastic syndrome",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C3247",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:602",
                            "conceptType": "Disease",
                            "label": "Gastrointestinal stromal tumor",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C3868",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:33893",
                            "conceptType": "Disease",
                            "label": "Chronic myeloid leukemia pediatric",
                        },
                        {
                            "id": "hemonc:667",
                            "conceptType": "Disease",
                            "label": "Soft tissue sarcoma",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C9306",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                        {
                            "id": "hemonc:616",
                            "conceptType": "Disease",
                            "label": "Hypereosinophilic syndrome",
                            "mappings": [
                                {
                                    "coding": {
                                        "code": "ncit:C27038",
                                        "system": "http://purl.obolibrary.org/obo/ncit.owl",
                                    },
                                    "relation": "relatedMatch",
                                }
                            ],
                        },
                    ],
                },
            },
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "rxcui:282388",
                    "label": "imatinib",
                },
            },
        ],
    }


@pytest.fixture(scope="session")
def moa_chronic_myelogenous_leukemia():
    """Create test fixture for MOA Chronic Myelogenous Leukemia."""
    return {
        "id": "moa.normalize.disease.ncit:C3174",
        "conceptType": "Disease",
        "label": "Chronic Myelogenous Leukemia",
        "extensions": [
            {
                "name": VICC_NORMALIZER_DATA,
                "value": {
                    "id": "ncit:C3174",
                    "label": "Chronic Myeloid Leukemia, BCR-ABL1 Positive",
                    "mondo_id": "mondo:0011996",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "id": "oncotree:CML",
                    "label": "Chronic Myelogenous Leukemia",
                    "system": "https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
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
        "reportedIn": {
            "label": "Danos et al., 2019, Genome Med.",
            "title": "Standard operating procedure for curation and clinical interpretation of variants in cancer",
            "doi": "10.1186/s13073-019-0687-x",
            "pmid": 31779674,
            "type": "Document",
        },
        "subtype": {"primaryCode": "variant curation standard operating procedure"},
        "type": "Method",
    }


@pytest.fixture(scope="session")
def moa_method():
    """Create test fixture for MOA."""
    return {
        "id": "moa.method:2021",
        "label": "MOAlmanac (2021)",
        "reportedIn": {
            "label": "Reardon, B., Moore, N.D., Moore, N.S. et al.",
            "title": "Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
            "doi": "10.1038/s43018-021-00243-3",
            "pmid": 35121878,
            "type": "Document",
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
def moa_source45():
    """Create a test fixture for MOA source 44."""
    return {
        "id": "moa.source:45",
        "extensions": [{"name": "source_type", "value": "Journal"}],
        "type": "Document",
        "title": "Gorre, Mercedes E., et al. Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification. Science 293.5531 (2001): 876-880.",
        "urls": ["https://doi.org/10.1126/science.1062538"],
        "doi": "10.1126/science.1062538",
        "pmid": 11423618,
    }


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
                    assert actual.keys() == expected.keys(), expected["id"]
                    expected_copy = deepcopy(expected)
                    diff = DeepDiff(actual, expected_copy, ignore_order=True)
                    assert diff == {}, expected["id"]
                    continue

            assert found_match, f"Did not find {expected['id']} in response"

    return _check


@pytest.fixture(scope="session")
def check_transformed_cdm(assertion_checks):
    """Test fixture to compare CDM transformations."""

    def check_transformed_cdm(data, statements, transformed_file):
        """Test that transform to CDM works correctly."""
        assertion_checks(data["statements"], statements, is_cdm=True)
        transformed_file.unlink()

    return check_transformed_cdm


@pytest.fixture(scope="module")
def normalizers():
    """Provide normalizers to querying/transformation tests."""
    return ViccNormalizers()


@pytest.fixture(scope="module")
def query_handler(normalizers):
    """Create query handler test fixture"""
    qh = QueryHandler(normalizers=normalizers)
    yield qh
    qh.driver.close()
