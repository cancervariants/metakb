"""Test MOAlmanac assertions"""

import json
from unittest.mock import patch

import pytest
from tests.conftest import TEST_HARVESTERS_DIR

from metakb.harvesters.moa import MoaHarvester
from metakb.schemas.app import SourceName


@pytest.fixture(scope="session")
def assertion164():
    """Create a fixture for assertion #164."""
    return {
        "id": 164,
        "context": "Resistance to BRAFi monotherapy",
        "description": "Administration of bevacizumab in a dabrafenib-resistant melanoma cancer cell line (A375R) counteracted the tumor growth stimulating effect of administering dabrafenib post-resistance. This study suggests that a regime which combines BRAFi with bevacizumab or inhibitors of PI3K/Akt/mTOR may be more effective than BRAFi monotherapy in the setting of resistance.",
        "deprecated": False,
        "disease": {
            "name": "Melanoma",
            "oncotree_code": "MEL",
            "oncotree_term": "Melanoma",
        },
        "therapy": {
            "name": "Dabrafenib + Bevacizumab",
            "type": "Targeted therapy",
            "strategy": "B-RAF inhibition + VEGF/VEGFR inhibition",
            "resistance": "",
            "sensitivity": 1,
        },
        "predictive_implication": "Preclinical",
        "favorable_prognosis": "",
        "created_on": "02/07/25",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_id": 70,
        "variant": {
            "id": 144,
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


@pytest.fixture(scope="session")
def assertion120():
    return {
        "id": 120,
        "context": "",
        "deprecated": False,
        "description": "ARID1A mutations were associated with poorer prognosis in a study of 109 microdissected pancreatic adenocarcinoma tumors.",
        "disease": {
            "name": "Pancreatic Adenocarcinoma",
            "oncotree_code": "PAAD",
            "oncotree_term": "Pancreatic Adenocarcinoma",
        },
        "therapy": {
            "name": "",
            "type": "",
            "strategy": "",
            "resistance": "",
            "sensitivity": "",
        },
        "predictive_implication": "Clinical evidence",
        "favorable_prognosis": 0,
        "created_on": "10/02/25",
        "last_updated": "2017-11-03",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_id": 54,
        "variant": {
            "id": 120,
            "alternate_allele": None,
            "cdna_change": None,
            "chromosome": None,
            "end_position": None,
            "exon": None,
            "feature_type": "somatic_variant",
            "gene": "ARID1A",
            "protein_change": None,
            "reference_allele": None,
            "rsid": None,
            "start_position": None,
            "variant_annotation": None,
            "feature": "ARID1A",
        },
    }


@patch.object(MoaHarvester, "_get_all_variants")
@patch.object(MoaHarvester, "_get_all_assertions")
def test_assertion_164(test_get_all_assertions, test_get_all_variants, assertion164):
    """Test moa harvester works correctly for assertions."""
    moa_harvester_test_dir = TEST_HARVESTERS_DIR / SourceName.MOA.value
    with (moa_harvester_test_dir / "assertions.json").open() as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with (moa_harvester_test_dir / "variants.json").open() as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    assertion_resp = MoaHarvester()._get_all_assertions()
    _, variants_list = MoaHarvester().harvest_variants()
    assertions = MoaHarvester().harvest_assertions(assertion_resp, variants_list)

    actual = None
    for a in assertions:
        if a["id"] == assertion164["id"]:
            actual = a
            break
    assert actual == assertion164


@patch.object(MoaHarvester, "_get_all_variants")
@patch.object(MoaHarvester, "_get_all_assertions")
def test_assertion_120(test_get_all_assertions, test_get_all_variants, assertion120):
    """Test moa harvester works correctly for assertions."""
    moa_harvester_test_dir = TEST_HARVESTERS_DIR / SourceName.MOA.value
    with (moa_harvester_test_dir / "assertions.json").open() as f:
        data = json.load(f)
    test_get_all_assertions.return_value = data

    with (moa_harvester_test_dir / "variants.json").open() as f:
        data = json.load(f)
    test_get_all_variants.return_value = data

    assertion_resp = MoaHarvester()._get_all_assertions()
    _, variants_list = MoaHarvester().harvest_variants()
    assertions = MoaHarvester().harvest_assertions(assertion_resp, variants_list)

    actual = None
    for a in assertions:
        if a["id"] == assertion120["id"]:
            actual = a
            break
    assert actual == assertion120
