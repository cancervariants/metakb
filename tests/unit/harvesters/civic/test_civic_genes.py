"""Test CIViC source"""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters import CIViCHarvester
from mock import patch
import json


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
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 4
                }
            },
            {
                'name': "EML4-ALK e6-e19 G1269A and AMPLIFICATION",
                'id': 3204,
                'evidence_items': {
                    'accepted_count': 2,
                    'rejected_count': 0,
                    'submitted_count': 2
                }
            },
            {
                'name': "EML4-ALK G1202del",
                'id': 2813,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 1,
                    'submitted_count': 0
                }
            },
            {
                'name': "EML4-ALK L1152R",
                'id': 307,
                'evidence_items': {
                    'accepted_count': 0,
                    'rejected_count': 1,
                    'submitted_count': 1
                }
            },
            {
                'name': "EML4-ALK L1198F",
                'id': 2816,
                'evidence_items': {
                    'accepted_count': 1,
                    'rejected_count': 1,
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


@patch.object(CIViCHarvester, '_get_all_genes')
def test_genes(test_get_all_genes, dux4, alk):
    """Test that CIViC harvest genes method is correct."""
    with open(f"{PROJECT_ROOT}/tests/data/harvesters/civic/genes.json") as f:
        data = json.load(f)
    test_get_all_genes.return_value = data
    genes = CIViCHarvester().harvest_genes()
    actual_dux4 = None
    actual_alk = None
    for gene in genes:
        if gene['id'] == 34321:
            actual_dux4 = gene
        if gene['id'] == 1:
            actual_alk = gene

    assert actual_alk == alk
    assert actual_dux4 == dux4
