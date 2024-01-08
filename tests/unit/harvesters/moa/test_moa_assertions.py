"""Test MOAlmanac assertions"""
import json

import pytest
from mock import patch

from metakb import PROJECT_ROOT  # noqa: I202
from metakb.harvesters import MoaHarvester


@pytest.fixture(scope="module")
def assertion165():
    """Create a fixture for assertion #165."""
    return {
        "id": 165,
        "context": "Resistance to BRAFi monotherapy",
        "description": "Administration of bevacizumab in a dabrafenib-resistant melanoma cancer cell line (A375R) counteracted the tumor growth stimulating effect of administering dabrafenib post-resistance. This study suggests that a regime which combines BRAFi with bevacizumab or inhibitors of PI3K/Akt/mTOR may be more effective than BRAFi monotherapy in the setting of resistance.",  # noqa: E501
        "disease": {
            "name": "Melanoma",
            "oncotree_code": "MEL",
            "oncotree_term": "Melanoma"
        },
        "therapy_name": "Dabrafenib + Bevacizumab",
        "therapy_type": "Targeted therapy",
        "clinical_significance": "sensitivity",
        "predictive_implication": "Preclinical",
        "favorable_prognosis": "",
        "created_on": "12/07/23",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_ids": 69,
        "variant": {
            "id": 145,
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
            "feature": "BRAF p.V600E (Missense)"
        }
    }


@patch.object(MoaHarvester, "_get_all_variants")
@patch.object(MoaHarvester, "_get_all_assertions")
def test_assertion_170(test_get_all_assertions, test_get_all_variants,
                       assertion165):
    """Test moa harvester works correctly for assertions."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/assertions.json") as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/moa/variants.json") as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    assertion_resp = MoaHarvester()._get_all_assertions()
    _, variants_list = MoaHarvester().harvest_variants()
    assertions = MoaHarvester().harvest_assertions(
        assertion_resp, variants_list)

    actual = None
    for a in assertions:
        if a["id"] == assertion165["id"]:
            actual = a
            break
    assert actual == assertion165
