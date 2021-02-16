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
        "description": "Administration of bevacizumab in a dabrafenib"
                       "-resistant cell line counteracted the tumor growth "
                       "stimulating effect of administering dabrafenib "
                       "post-resistance.",
        "disease": {
            "name": "Melanoma",
            "oncotree_code": "MEL",
            "oncotree_term": "Melanoma"
        },
        "therapy_name": "Bevacizumab",
        "therapy_type": "Targeted therapy",
        "clinical_significance": "sensitivity",
        "predictive_implication": "Preclinical",
        "feature_ids": [
            168
        ],
        "favorable_prognosis": None,
        "created_on": "02/04/21",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_ids": [
            67
        ],
        "variant": {
            "id": 168,
            "feature_type": "somatic_variant",
            "gene": "BRAF",
            "chromosome": "7",
            "start_position": "140453136.0",
            "end_position": "140453136.0",
            "reference_allele": "A",
            "alternate_allele": "T",
            "cdna_change": "c.1799T>A",
            "protein_change": "p.V600E",
            "variant_annotation": "Missense",
            "exon": "15.0",
            "rsid": "rs113488022",
            "feature": "BRAF p.V600E (Missense)"
        }
    }


@patch.object(MOAlmanac, '_get_all_definitions')
@patch.object(MOAlmanac, '_get_all_variants')
@patch.object(MOAlmanac, '_get_all_assertions')
def test_assertion_168(test_get_all_assertions, test_get_all_variants,
                       test_get_all_definitions, assertion168):
    """Test moa harvester works correctly for assertions."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/variants.json") as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/definitions.json") as f:
        data = json.load(f)
    test_get_all_definitions.return_value = [data[0], data[1]]

    variants = MOAlmanac()._harvest_variants()
    assertions = MOAlmanac()._harvest_assertions(variants)

    actual = None
    for a in assertions:
        if a['id'] == 168:
            actual = a
            break
    assert actual == assertion168
