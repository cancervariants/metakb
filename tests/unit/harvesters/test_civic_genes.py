"""Test CIViC source"""
import pytest
from metakb.harvesters.civic import CIViC
from civicpy import civic as civicpy


@pytest.fixture(scope='module')
def civic():
    """Create CIViC Harvester test fixture.."""
    class CIViCGenes:

        def __init__(self):
            civicpy.load_cache(on_stale='ignore')
            self.c = CIViC()

        def _harvest_gene_by_id(self, gene_id):
            gene = civicpy.get_gene_by_id(gene_id)
            return self.c._harvest_gene(gene)
    return CIViCGenes()


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
            # TODO: Check if we should be downloading from API query
            # {
            #     'name': "EML4-ALK (E6;A19) G1269A and AMPLIFICATION",
            #     'id': 3204,
            #     'evidence_items': {
            #         'accepted_count': 0,
            #         'rejected_count': 0,
            #         'submitted_count': 1
            #     }
            # },
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


def test_genes_dux4(dux4, civic):
    """Test civic harvester works correctly for genes."""
    actual_dux4 = civic._harvest_gene_by_id(34321)
    assert actual_dux4.keys() == dux4.keys()
    keys = dux4.keys()
    for key in keys:
        assert actual_dux4[key] == dux4[key]


def test_genes_alk(alk, civic):
    """Test civic harvester works correctly for genes."""
    actual_alk = civic._harvest_gene_by_id(1)
    assert actual_alk.keys() == alk.keys()
    keys = alk.keys()
    for key in keys:
        assert actual_alk[key] == alk[key]
