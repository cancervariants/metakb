"""Test MOAlmanac assertions"""
import json

import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters import MOAHarvester
from mock import patch


@pytest.fixture(scope="module")
def assertion170():
    """Create a fixture for assertion #170."""
    return {
        "id": 170,
        "context": "",
        "description": "Administration of bevacizumab in a dabrafenib-resistant cell "
        "line counteracted the tumor growth stimulating effect of "
        "administering dabrafenib post-resistance.",
        "disease": {
            "name": "Melanoma",
            "oncotree_code": "MEL",
            "oncotree_term": "Melanoma",
        },
        "therapy_name": "Bevacizumab",
        "therapy_type": "Targeted therapy",
        "clinical_significance": "sensitivity",
        "predictive_implication": "Preclinical",
        "favorable_prognosis": False,
        "created_on": "09/08/22",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_ids": 69,
        "variant": {
            "id": 149,
            "alternate_allele": "T",
            "cdna_change": "c.1799T>A",
            "chromosome": "7",
            "end_position": "140453136",
            "exon": "15",
            "feature_type": "somatic_variant",
            "gene": "BRAF",
            "protein_change": "p.V600E",
            "reference_allele": "A",
            "rsid": "rs113488022",
            "start_position": "140453136",
            "variant_annotation": "Missense",
            "feature": "BRAF p.V600E (Missense)",
        },
    }


@patch.object(MOAHarvester, "_get_all_variants")
@patch.object(MOAHarvester, "_get_all_assertions")
def test_assertion_170(test_get_all_assertions, test_get_all_variants, assertion170):
    """Test moa harvester works correctly for assertions."""
    with open(f"{PROJECT_ROOT}/tests/data/" f"harvesters/moa/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with open(f"{PROJECT_ROOT}/tests/data/" f"harvesters/moa/variants.json") as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    assertion_resp = MOAHarvester()._get_all_assertions()
    _, variants_list = MOAHarvester().harvest_variants()
    assertions = MOAHarvester().harvest_assertions(assertion_resp, variants_list)

    actual = None
    for a in assertions:
        if a["id"] == 170:
            actual = a
            break
    assert actual == assertion170
