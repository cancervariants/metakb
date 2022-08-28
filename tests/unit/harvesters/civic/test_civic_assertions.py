"""Test CIViC source"""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters import CIViCHarvester
from mock import patch
import json


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
        'gene_id': 24,
        'variant_id': 3232,
        'disease': {
            'id': 3,
            'name': "Acute Myeloid Leukemia",
            'display_name': "Acute Myeloid Leukemia",
            'doid': "9119",
            'disease_url': "http://www.disease-ontology.org/?id=DOID:9119"
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
        'phenotypes': [],
        'variant_origin': "Somatic"
    }


@patch.object(CIViCHarvester, '_get_all_assertions')
def test_assertions(test_get_all_assertions, aid40):
    """Test that CIViC harvest assertions method is correct."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/civic/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data
    assertions = CIViCHarvester().harvest_assertions()
    c_assertion = None
    for assertion in assertions:
        if assertion['id'] == 40:
            c_assertion = assertion
    assert c_assertion['evidence_items']
    c_assertion['evidence_items'] = []
    assert c_assertion == aid40
