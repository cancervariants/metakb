"""Test CIViC source"""
import pytest
from metakb.harvesters.civic import CIViC


@pytest.fixture(scope='module')
def evidence():
    """Create a list of evidence."""
    c = CIViC()
    return c.harvest_evidence()


@pytest.fixture(scope='module')
def genes():
    """Create a list of genes."""
    c = CIViC()
    return c.harvest_genes()


@pytest.fixture(scope='module')
def variants():
    """Create a list of variants."""
    c = CIViC()
    return c.harvest_variants()


@pytest.fixture(scope='module')
def assertions():
    """Create a listof assertions."""
    c = CIViC()
    return c.harvest_assertions()


@pytest.fixture(scope='module')
def lnscc():
    """Create a fixture for EID3017 evidence."""
    return {
        "id": 3017,
        "name": "EID3017",
        "description": "Patients with BRAF V600E-mutant NSCLC (n=57) were "
                       "enrolled into a phase 2, multicentre, non-randomised, "
                       "open-label study, administering dabrafenib plus "
                       "trametinib. The overall response rate was 36/57 "
                       "(63.2%, [95% CI 49.3-75.6]) and the median "
                       "progression-free survival was 9.7 months "
                       "(95% CI 6.9-19.6). At data cutoff "
                       "(11.6 months of follow-up), 18/36  (50%) confirmed "
                       "responses were ongoing and 23/57 (40%) of patients "
                       "had died.",
        "disease": {
            "id": 8,
            "name": "Lung Non-small Cell Carcinoma",
            "display_name": "Lung Non-small Cell Carcinoma",
            "doid": "3908",
            "url": "http://www.disease-ontology.org/?id=DOID:3908"
        },
        "drugs": [
            {
                "id": 19,
                "name": "Trametinib",
                "ncit_id": "C77908",
                "aliases": [
                    "N-(3-{3-cyclopropyl-5-[(2-fluoro-4-iodophenyl)amino]-6"
                    ",8-dimethyl-2,4,7-trioxo-3,4,6,7-tetrahydropyrido[4,3-d]"
                    "pyrimidin-1(2H)-yl}phenyl)acetamide",
                    "Mekinist", "MEK Inhibitor GSK1120212", "JTP-74057",
                    "GSK1120212"]
            }, {
                "id": 22,
                "name": "Dabrafenib",
                "ncit_id": "C82386",
                "aliases": ["GSK2118436", "GSK-2118436A", "GSK-2118436",
                            "BRAF Inhibitor GSK2118436",
                            "Benzenesulfonamide, N-(3-(5-(2-amino-4-pyrimidin"
                            "yl)-2-(1,1-dimethylethyl)-4-thiazolyl)-2-fluor"
                            "ophenyl)-2,6-difluoro-"]
            }
        ],
        "rating": 4,
        "evidence_level": "A",
        "evidence_type": "Predictive",
        "clinical_significance": "Sensitivity/Response",
        "evidence_direction": "Supports",
        "variant_origin": "Somatic",
        "drug_interaction_type": "Combination",
        "status": "accepted",
        # "open_change_count": 0,
        "type": "evidence",
        "source": {
            "id": 1296,
            "name": "Dabrafenib plus trametinib in patients with previously "
                    "treated BRAF(V600E)-mutant metastatic non-small cell "
                    "lung cancer: an open-label, multicentre phase 2 trial.",
            "citation": "Planchard et al., 2016, Lancet Oncol.",
            "citation_id": "27283860",
            "source_type": "PubMed",
            "asco_abstract_id": None,
            "source_url": "http://www.ncbi.nlm.nih.gov/pubmed/27283860",
            "open_access": True,
            "pmc_id": "PMC4993103",
            "publication_date": {
                "year": 2016,
                "month": 7
            },
            "journal": "Lancet Oncol.",
            "full_journal_title": "The Lancet. Oncology",
            "status": "partially curated",
            "is_review": False,
            "clinical_trials": [{
                "nct_id": "NCT01336634",
                "name": "Study of Selective BRAF Kinase Inhibitor Dabrafenib "
                        "Monotherapy Twice Daily and in Combination With "
                        "Dabrafenib Twice Daily and Trametinib Once Daily in "
                        "Combination Therapy in Subjects With BRAF V600E "
                        "Mutation Positive Metastatic (Stage IV) Non-small "
                        "Cell Lung Cancer.",
                "description": "Dabrafenib is a potent and selective inhibitor"
                               " of BRAF kinase activity. This is a Phase II,"
                               " non-randomized, open-label study to assess "
                               "the efficacy, safety, and tolerability of "
                               "dabrafenib administered as a single agent and "
                               "in combination with trametinib in stage IV "
                               "disease to subjects with BRAF mutant advanced"
                               " non-small cell lung cancer. Subjects will "
                               "receive dabrafenib 150 mg twice daily (BID) "
                               "in monotherapy treatment and dabrafenib 150 "
                               "mg bid and trametinib 2 mg once daily in "
                               "combination therapy and continue on treatment"
                               " until disease progression, death, or "
                               "unacceptable adverse event.",
                "clinical_trial_url":
                    "https://clinicaltrials.gov/show/NCT01336634"
            }]
        },
        "variant_id": 12,
        "phenotypes": [],
        "assertions": [],
        # "errors": {},
        # "fields_with_pending_changes": {},
        "gene_id": 5
    }


@pytest.fixture(scope='module')
def alk():
    """Create a fixture for ALK gene."""
    return {
        'id': 1,
        'name': "ALK",
        'entrez_id': 238,
        'description': "ALK amplifications, fusions and mutations have been "
                       "shown to be driving events in non-small cell lung "
                       "cancer. While crizontinib has demonstrated efficacy "
                       "in treating the amplification, mutations in ALK have "
                       "been shown to confer resistance to current tyrosine"
                       " kinase inhibitors. Second-generation TKI's have "
                       "seen varied success in treating these resistant "
                       "cases, and the HSP90 inhibitor 17-AAG has been "
                       "shown to be cytostatic in ALK-altered cell lines.",
        'variants': [
            {
                'name': "CAD-ALK",
                'id': 2769,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK (E6;A19) G1269A and AMPLIFICATION",
                'id': 3204,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK G1202del",
                'id': 2813,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK L1152R",
                'id': 307,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK L1198F",
                'id': 2816,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "L1198F",
                'id': 1275,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 1,
                    'submitted_count': 1
                }
            },
            {
                'name': "HIP1-ALK I1171N",
                'id': 588,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 2
                }
            },
            {
                'name': "L1196Q",
                'id': 1553,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "RANBP2-ALK",
                'id': 514,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK L1196M and L1198F",
                'id': 2810,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "F1174C",
                'id': 1492,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "R214H",
                'id': 1683,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK C1156Y",
                'id': 6,
                'evidence_items': {
                    'accepted_count': 4,
                    'rejected_count': 2,
                    'submitted_count': 7
                }
            },
            {
                'name': "EML4-ALK G1202R and L1196M",
                'id': 2809,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 2
                }
            },
            {
                'name': "T1151M",
                'id': 1493,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK  V1180L",
                'id': 528,
                'evidence_items': {
                    'accepted_count': 5,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "R1192P",
                'id': 1661,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 1,
                    'submitted_count': 2
                }
            },
            {
                'name': "DEL4-11",
                'id': 550,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML6-ALK E1;A20 and FBXO11-ALK E1;A20",
                'id': 2750,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "MUTATION",
                'id': 512,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK",
                'id': 5,
                'evidence_items': {
                    'accepted_count': 7,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK S1206Y",
                'id': 172,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 2
                }
            },
            {
                'name': "EML4-ALK and AMPLIFICATION",
                'id': 170,
                'evidence_items': {
                    'accepted_count': 3,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EXPRESSION",
                'id': 2914,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "CLTC-ALK",
                'id': 520,
                'evidence_items': {
                    'accepted_count': 3,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "G1128A",
                'id': 2798,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 1,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK E2;A20",
                'id': 501,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK E6;A20",
                'id': 503,
                'evidence_items': {
                    'accepted_count': 7,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "R1275Q",
                'id': 9,
                'evidence_items': {
                    'accepted_count': 6,
                    'rejected_count': 0,
                    'submitted_count': 3
                }
            },
            {
                'name': "F1245V",
                'id': 1295,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "ALTERNATIVE TRANSCRIPT (ATI)",
                'id': 839,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 2
                }
            },
            {
                'name': "EML4-ALK I1171S",
                'id': 589,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "F1174V",
                'id': 1505,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "F1174L",
                'id': 8,
                'evidence_items': {
                    'accepted_count': 9,
                    'rejected_count': 0,
                    'submitted_count': 3
                }
            },
            {
                'name': "STRN-ALK",
                'id': 2218,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "ALK FUSION G1269A",
                'id': 552,
                'evidence_items': {
                    'accepted_count': 4,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "ALK FUSION G1202R",
                'id': 171,
                'evidence_items': {
                    'accepted_count': 6,
                    'rejected_count': 0,
                    'submitted_count': 3
                }
            },
            {
                'name': "ALK FUSION I1171",
                'id': 527,
                'evidence_items': {
                    'accepted_count': 7,
                    'rejected_count': 0,
                    'submitted_count': 3
                }
            },
            {
                'name': "EML4-ALK G1269A",
                'id': 308,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 6
                }
            },
            {
                'name': "EML4-ALK L1196M",
                'id': 7,
                'evidence_items': {
                    'accepted_count': 4,
                    'rejected_count': 0,
                    'submitted_count': 11
                }
            },
            {
                'name': "F1245C",
                'id': 549,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "L1198P",
                'id': 1556,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "L1152P",
                'id': 1554,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK G1202R and L1198F",
                'id': 2811,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK E20;A20",
                'id': 500,
                'evidence_items': {
                    'accepted_count': 4,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "ALK FUSIONS",
                'id': 499,
                'evidence_items': {
                    'accepted_count': 31,
                    'rejected_count': 2,
                    'submitted_count': 10
                }
            },
            {
                'name': "ALK FUSION F1245C",
                'id': 551,
                'evidence_items': {
                    'accepted_count': 3,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "ALK FUSION L1196M",
                'id': 2819,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK C1156Y-L1198F",
                'id': 352,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "NPM-ALK",
                'id': 513,
                'evidence_items': {
                    'accepted_count': 3,
                    'rejected_count': 1,
                    'submitted_count': 0
                }
            },
            {
                'name': "OVEREXPRESSION",
                'id': 2635,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK T1151INST",
                'id': 173,
                'evidence_items': {
                    'accepted_count': 4,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            }
        ],
        'aliases': [
            "ALK",
            "NBLST3",
            "CD246"
        ],
        'type': "gene"
    }


@pytest.fixture(scope='module')
def dux4():
    """Create DUX4 gene record."""
    return {
        'id': 34321,
        'name': "DUX4",
        'entrez_id': 100288687,
        'description': "",
        'variants': [
            {
                'name': "DUX4 FUSIONS",
                'id': 524,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
            },
            {
                'name': "DUX4-IGH",
                'id': 2589,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 1
                }
            }
        ],
        'aliases': [
            "DUX4",
            "DUX4L"
        ],
        'type': "gene"
    }


@pytest.fixture(scope='module')
def pdgfra():
    """Create a fixture for PDGFRA variant."""
    return {
        'id': 100,
        'entrez_name': "PDGFRA",
        'entrez_id': 5156,
        'name': "D842Y",
        'description': "PDGFRA D842 mutations are characterized broadly as "
                       "imatinib resistance mutations. This is most well "
                       "characterized in gastrointestinal stromal tumors, but "
                       "other cell lines containing these mutations have been "
                       "shown to be resistant as well. In imatinib resistant "
                       "cell lines, a number of other therapeutics have "
                       "demonstrated efficacy. These include; crenolanib, "
                       "sirolimus, and midostaurin (PKC412).",
        'gene_id': 38,
        'type': "variant",
        'variant_types': [
            {
                'id': 47,
                'name': "missense_variant",
                'display_name': "Missense Variant",
                'so_id': "SO:0001583",
                'description': "A sequence variant, that changes one or more"
                               " bases, resulting in a different amino acid "
                               "sequence but where the length is preserved.",
                'url':
                    "http://www.sequenceontology.org/browser/"
                    "current_svn/term/SO:0001583"
            }
        ],
        'civic_actionability_score': 4,
        'coordinates': {
            'chromosome': "4",
            'start': 55152092,
            'stop': 55152092,
            'reference_bases': "G",
            'variant_bases': "T",
            'representative_transcript': "ENST00000257290.5",
            'chromosome2': None,
            'start2': None,
            'stop2': None,
            'representative_transcript2': None,
            'ensembl_version': 75,
            'reference_build': "GRCh37"
        },
        'evidence_items': [
            {
                'id': 45,
                'name': "EID45",
                'description': "In CHO cells with PDGFRA D842Y mutation "
                               "that have shown imatinib resistance, "
                               "crenolanib was significantly more potent "
                               "at inhibiting kinase activity than imatinib.",
                'disease': {
                    'id': 2,
                    'name': "Gastrointestinal Stromal Tumor",
                    'display_name': "Gastrointestinal Stromal Tumor",
                    'doid': "9253",
                    'url': "http://www.disease-ontology.org/?id=DOID:9253"
                },
                'drugs': [
                    {
                        'id': 21,
                        'name': "Crenolanib",
                        'ncit_id': "C64639",
                        'aliases': [
                            "PDGFR Inhibitor CP-868596",
                            "CP-868596",
                            "CP-868,596",
                            "[1-[2-[5-(3-Methyloxetan-3-ylmethoxy)benzimidazol"
                            "-1-yl]quinolin-8-yl]piperidin-4-yl]amine",
                            "4-Piperidinamine, 1-[2-[5-[(3-methyl-3-oxetanyl)"
                            "methoxy]-1Hbenzimidazol-1-yl]-8-quinolinyl]-"
                        ]
                    }
                ],
                'rating': 4,
                'evidence_level': "D",
                'evidence_type': "Predictive",
                'clinical_significance': "Sensitivity/Response",
                'evidence_direction': "Supports",
                'variant_origin': "Somatic",
                'drug_interaction_type': None,
                'status': "accepted",
                # 'open_change_count': 0,
                'type': "evidence",
                'source': {
                    'id': 80,
                    'name': "Crenolanib inhibits the drug-resistant PDGFRA "
                            "D842V mutation associated with imatinib-resistant"
                            " gastrointestinal stromal tumors.",
                    'citation': "Heinrich et al., 2012, Clin. Cancer Res.",
                    'citation_id': "22745105",
                    'source_type': "PubMed",
                    'asco_abstract_id': None,
                    'source_url':
                        "http://www.ncbi.nlm.nih.gov/pubmed/22745105",
                    'open_access': None,
                    'pmc_id': None,
                    'publication_date': {
                        'year': 2012,
                        'month': 8,
                        'day': 15
                    },
                    'journal': "Clin. Cancer Res.",
                    'full_journal_title':
                        "Clinical cancer research : an official"
                        " journal of the American Association"
                        " for Cancer Research",
                    'status': "fully curated",
                    'is_review': False,
                    'clinical_trials': []
                },
                'variant_id': 100,
                'phenotypes': []
            }
        ],
        'variant_groups': [
            {
                'id': 1,
                'name': "Imatinib Resistance",
                'description': "While imatinib has shown to be incredibly "
                               "successful in treating philadelphia chromosome"
                               " positive CML, patients that have shown "
                               "primary or secondary resistance to the drug "
                               "have been observed to harbor T315I and E255K "
                               "ABL kinase domain mutations. These mutations,"
                               " among others, have been observed both in "
                               "primary refractory disease and acquired "
                               "resistance. In gastrointestinal stromal "
                               "tumors (GIST), PDGFRA 842 mutations have "
                               "also been shown to confer resistance to"
                               " imatinib. ",
                'variants': [
                    {
                        'id': 2,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL T315I",
                        'description': "While the efficacy of imatinib has "
                                       "revolutionized chronic myelogenous "
                                       "leukemia (CML) treatment, it is still"
                                       " not a cure-all. Both initial "
                                       "resistance and acquired resistance "
                                       "as a result of selection have been "
                                       "seen in a small subset of CML "
                                       "patients. The ABL kinase domain "
                                       "mutation T315I (aka T334I) has been "
                                       "shown to be one such mutation that"
                                       " confers resistance to imatinib. "
                                       "Second generation TKI's (dasatinib"
                                       " and ponatinib) specific to BCR-ABL"
                                       " have shown efficacy in treating "
                                       "resistant cases.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different amino"
                                               " acid sequence but where "
                                               "the length is preserved.",
                                'url':
                                    "http://www.sequenceontology.org/browser/"
                                    "current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the"
                                               " deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 146,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133748283,
                            'stop': 133748283,
                            'reference_bases': "C",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 3,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL E255K",
                        'description': "While the efficacy of imatinib has "
                                       "revolutionized chronic myelogenous"
                                       " leukemia (CML) treatment, it is "
                                       "still not a cure-all. Both initial"
                                       " resistance and acquired resistance"
                                       " as a result of selection have been"
                                       " seen in a small subset of CML "
                                       "patients. The ABL kinase domain "
                                       "mutation E255K has been shown to be"
                                       " one such mutation that confers "
                                       "resistance to imatinib. Second "
                                       "generation TKI's (dasatinib and "
                                       "nilotinib) specific to BCR-ABL have"
                                       " shown efficacy in treating "
                                       "resistant cases.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the "
                                               "deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 73,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133738363,
                            'stop': 133738363,
                            'reference_bases': "G",
                            'variant_bases': "A",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 98,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842I",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib "
                                       "resistance mutations. This is most"
                                       " well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to be"
                                       " resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152092,
                            'stop': 55152093,
                            'reference_bases': "GA",
                            'variant_bases': "AT",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 99,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842V",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is most"
                                       " well characterized in "
                                       "gastrointestinal stromal tumors, but"
                                       " other cell lines containing these "
                                       "mutations have been shown to be "
                                       "resistant as well. Exogenous "
                                       "expression of the A842V mutation"
                                       " resulted in constitutive tyrosine"
                                       " phosphorylation of PDGFRA in the "
                                       "absence of ligand in 293T cells and "
                                       "cytokine-independent proliferation "
                                       "of the IL-3-dependent Ba/F3 cell "
                                       "line, both evidence that this is an "
                                       "activating mutation. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases,"
                                               " resulting in a different "
                                               "amino acid sequence but "
                                               "where the length is "
                                               "preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 100.5,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152093,
                            'stop': 55152093,
                            'reference_bases': "A",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 100,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842Y",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is "
                                       "most well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing these"
                                       " mutations have been shown to be "
                                       "resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but"
                                               " where the length is "
                                               "preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152092,
                            'stop': 55152092,
                            'reference_bases': "G",
                            'variant_bases': "T",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 101,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "I843DEL",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib"
                                       " resistance mutations. This is "
                                       "most well characterized in "
                                       "gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to "
                                       "be resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated "
                                       "efficacy. These include; crenolanib,"
                                       " sirolimus, and midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 107,
                                'name': "inframe_deletion",
                                'display_name': "Inframe Deletion",
                                'so_id': "SO:0001822",
                                'description': "An inframe non synonymous "
                                               "variant that deletes bases "
                                               "from the coding sequence.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001822"
                            }
                        ],
                        'civic_actionability_score': 5,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152095,
                            'stop': 55152097,
                            'reference_bases': "ATC",
                            'variant_bases': None,
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 102,
                        'entrez_name': "PDGFRA",
                        'entrez_id': 5156,
                        'name': "D842_I843delinsVM",
                        'description': "PDGFRA D842 mutations are "
                                       "characterized broadly as imatinib "
                                       "resistance mutations. The "
                                       "DI842-843VM variant is the result of"
                                       " a double point mutation. This is"
                                       " most well characterized in"
                                       " gastrointestinal stromal tumors, "
                                       "but other cell lines containing "
                                       "these mutations have been shown to"
                                       " be resistant as well. In imatinib "
                                       "resistant cell lines, a number of "
                                       "other therapeutics have demonstrated"
                                       " efficacy. These include; "
                                       "crenolanib, sirolimus, and "
                                       "midostaurin (PKC412).",
                        'gene_id': 38,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases, "
                                               "resulting in a different "
                                               "amino acid sequence but "
                                               "where the length is preserved"
                                               ".",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            }
                        ],
                        'civic_actionability_score': 4,
                        'coordinates': {
                            'chromosome': "4",
                            'start': 55152093,
                            'stop': 55152097,
                            'reference_bases': "ACATC",
                            'variant_bases': "TCATG",
                            'representative_transcript': "ENST00000257290.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    },
                    {
                        'id': 241,
                        'entrez_name': "ABL1",
                        'entrez_id': 25,
                        'name': "BCR-ABL F317L",
                        'description': "BCR-ABL F317L, like the similar "
                                       "BCR-ABL T315I mutation, is becoming "
                                       "a common clinical marker for"
                                       " resistance to front-line therapies"
                                       " in CML. It has been shown to confer"
                                       " resistance to dasatinib, but "
                                       "responds well to ponatinib and other "
                                       "second generation inhibitors.",
                        'gene_id': 4,
                        'type': "variant",
                        'variant_types': [
                            {
                                'id': 47,
                                'name': "missense_variant",
                                'display_name': "Missense Variant",
                                'so_id': "SO:0001583",
                                'description': "A sequence variant, that "
                                               "changes one or more bases,"
                                               " resulting in a different "
                                               "amino acid sequence but where"
                                               " the length is preserved.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001583"
                            },
                            {
                                'id': 120,
                                'name': "transcript_fusion",
                                'display_name': "Transcript Fusion",
                                'so_id': "SO:0001886",
                                'description': "A feature fusion where the"
                                               " deletion brings together "
                                               "transcript regions.",
                                'url': "http://www.sequenceontology.org/"
                                       "browser/current_svn/term/SO:0001886"
                            }
                        ],
                        'civic_actionability_score': 109.5,
                        'coordinates': {
                            'chromosome': "9",
                            'start': 133748288,
                            'stop': 133748288,
                            'reference_bases': "T",
                            'variant_bases': "C",
                            'representative_transcript': "ENST00000318560.5",
                            'chromosome2': None,
                            'start2': None,
                            'stop2': None,
                            'representative_transcript2': None,
                            'ensembl_version': 75,
                            'reference_build': "GRCh37"
                        }
                    }
                ],
                'type': "variant_group"
            }
        ],
        'assertions': [],
        'variant_aliases': [
            "ASP842TYR",
            "RS121913265"
        ],
        'hgvs_expressions': [
            "ENST00000257290.5:c.2524G>T",
            "NC_000004.11:g.55152092G>T",
            "NM_006206.5:c.2524G>T",
            "NP_006197.1:p.Asp842Tyr"
        ],
        'clinvar_entries': [
            "376250"
        ],
        'allele_registry_id': 'CA16602703'
    }


@pytest.fixture(scope='module')
def aid40():
    """Create a fixture for AID40 assertion."""
    return {
        'id': 40,
        'type': "assertion",
        'name': "AID40",
        'summary': "FLT3 tyrosine kinase domain mutations at residue I836 "
                   "in relapsed / refractory acute myeloid leukemia (AML)"
                   " are sensitive to Gilteritinib, a Type I FLT3 inhibitor.",
        'description': "Mutations in the FMS-like tyrosine kinase 3 (FLT3)"
                       " gene are the most common mutations in acute myeloid"
                       " leukemia (AML). 5 to 10% of AML is associated with"
                       " activating point mutations in the FLT3 tyrosine "
                       "kinase domain (TKD), including at the residue I836."
                       " FLT3 TKD mutations, such as I836 are a commonly "
                       "reported mechanism of clinical resistance to type II "
                       "FLT3 inhibitors (sorafenib, quizartinib and ponatinib)"
                       ", which bind only the inactive kinase conformation."
                       " However, Gilteritinib (an oral inhibitor of FLT3 "
                       "and AXL) demonstrated significant single-agent "
                       "activity in R/R (Relapsed or Refractory) AML with "
                       "FLT3 ITD, D835, I836 mutations, achieving an overall "
                       "response rate of 40%. A randomized phase 3 study of"
                       " Gilteritinib (ADMIRAL trial, NCT02421939) compared"
                       " with salvage chemotherapy in AML demonstrated a "
                       "significant overall survival benefit in the "
                       "gilteritinib arm (9.3 months) compared with "
                       "chemotherapy (5.6 months). Event-free survival in "
                       "the gilteritinib arm was also superior (Perl AE, et "
                       "al., 2019). Based on findings from this study, the "
                       "US Food and Drug Administration (FDA) approved "
                       "Gilteritinib as the first FLT3 inhibitor indicated "
                       "for use as monotherapy R/R AML with FLT3 ITD "
                       "mutations or TKD D835 or I836 mutations.",
        'gene': {
            'name': "FLT3",
            'id': 24
        },
        'variant': {
            'name': "I836",
            'id': 3232
        },
        'disease': {
            'id': 3,
            'name': "Acute Myeloid Leukemia",
            'display_name': "Acute Myeloid Leukemia",
            'doid': "9119",
            'url': "http://www.disease-ontology.org/?id=DOID:9119"
        },
        'drugs': [
            {
                'id': 641,
                'name': "Gilteritinib",
                'ncit_id': "C116722",
                'aliases': [
                    "Xospata",
                    "ASP2215",
                    "ASP-2215",
                    "6-Ethyl-3-((3-methoxy-4-(4-(4-methylpiperazin-1-yl)"
                    "piperidin-1-yl)phenyl)amino)-5-((tetrahydro-2H-pyran-4-yl"
                    ")amino)pyrazine-2-carboxamide"
                ]
            }
        ],
        'evidence_type': "Predictive",
        'evidence_direction': "Supports",
        'clinical_significance': "Sensitivity/Response",
        # 'evidence_item_count': 2,
        'fda_regulatory_approval': True,
        'status': "submitted",
        # 'open_change_count': 0,
        # 'pending_evidence_count': 0,
        'nccn_guideline': "Acute Myeloid Leukemia",
        'nccn_guideline_version': "v1.2020",
        'amp_level': "Tier I - Level A",
        'evidence_items': [],
        'acmg_codes': [],
        'drug_interaction_type': None,
        'fda_companion_test': True,
        'allele_registry_id': None,
        'phenotypes': [],
        'variant_origin': "Somatic"
    }


def test_evidence_json(lnscc, evidence):
    """Test civic harvester works correctly for evidence."""
    for ev in evidence:
        if ev['id'] == 3017:
            actual = ev
            break
    assert actual.keys() == lnscc.keys()
    keys = lnscc.keys()
    for key in keys:
        assert actual[key] == lnscc[key]


def test_genes_dux4(dux4, genes):
    """Test civic harvester works correctly for genes."""
    for gene in genes:
        if gene['id'] == 34321:
            actual_dux4 = gene
            break
    assert actual_dux4.keys() == dux4.keys()
    keys = dux4.keys()
    for key in keys:
        assert actual_dux4[key] == dux4[key]


def test_genes_alk(alk, genes):
    """Test civic harvester works correctly for genes."""
    for gene in genes:
        if gene['id'] == 1:
            actual_alk = gene
            break
    assert actual_alk.keys() == alk.keys()
    keys = alk.keys()
    for key in keys:
        assert actual_alk[key] == alk[key]


def test_variants(pdgfra, variants):
    """Test civic harvester works correctly for variants."""
    for variant in variants:
        if variant['id'] == 100:
            actual_pdgfra = variant
            break
    assert actual_pdgfra.keys() == pdgfra.keys()
    keys = pdgfra.keys()
    for key in keys:
        if key == 'variant_aliases' or key == 'hgvs_expressions':
            assert set(actual_pdgfra[key]) == set(pdgfra[key])
        else:
            assert actual_pdgfra[key] == pdgfra[key]


def test_assertions(aid40, assertions):
    """Test civic harvester works correctly for assertions."""
    for assertion in assertions:
        if assertion['id'] == 40:
            actual_aid40 = assertion
            break
    assert actual_aid40.keys() == aid40.keys()
    keys = aid40.keys()
    for key in keys:
        # Ignore evidence_items due to largeness. Tested in others.
        if key != 'evidence_items':
            assert actual_aid40[key] == aid40[key]
