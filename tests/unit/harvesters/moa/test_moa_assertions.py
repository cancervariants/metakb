"""Test MOAlmanac assertions"""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters.moalmanac import MOAlmanac
from mock import patch
import json


@pytest.fixture(scope='module')
def assertion168():
    """Create a fixture for assertion #168."""
    return {
        "id": 168,
        "context": None,
        "description": "Administration of bevacizumab in a "
                       "dabrafenib-resistant cell line counteracted the tumor"
                       " growth stimulating effect of administering "
                       "dabrafenib post-resistance.",
        "disease": {
            "name": "Melanoma",
            "oncotree_code": "MEL",
            "oncotree_term": "Melanoma"
        },
        "therapy_name": "Bevacizumab",
        "therapy_type": "Targeted therapy",
        "clinical_significance": "sensitivity",
        "predictive_implication": "Preclinical",
        "favorable_prognosis": None,
        "created_on": "03/31/21",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_ids": 67,
        "variant": {
            "id": 147,
            "alternate_allele": "T",
            "cdna_change": "c.1799T>A",
            "chromosome": "7",
            "end_position": "140453136.0",
            "exon": "15.0",
            "feature_type": "somatic_variant",
            "gene": "BRAF",
            "protein_change": "p.V600E",
            "reference_allele": "A",
            "rsid": "rs113488022",
            "start_position": "140453136.0",
            "variant_annotation": "Missense",
            "feature": "BRAF p.V600E (Missense)"
        }
    }


@patch.object(MOAlmanac, '_get_all_variants')
@patch.object(MOAlmanac, '_get_all_assertions')
def test_assertion_168(test_get_all_assertions, test_get_all_variants,
                       assertion168):
    """Test moa harvester works correctly for assertions."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/variants.json") as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    assertion_resp = MOAlmanac()._get_all_assertions()
    variants, variants_list = MOAlmanac()._harvest_variants()
    assertions = MOAlmanac()._harvest_assertions(assertion_resp, variants_list)

    actual = None
    for a in assertions:
        if a['id'] == 168:
            actual = a
            break
    assert actual == assertion168
