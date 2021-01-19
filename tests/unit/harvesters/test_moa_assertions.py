"""Test MOAlmanac source"""
import pytest
from metakb.harvesters.moalmanac import MOAlmanac


@pytest.fixture(scope='module')
def assertions():
    """Create a list of assertions."""
    moa = MOAlmanac()
    variants = moa._harvest_variants()

    return moa._harvest_assertions(variants)


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
        "created_on": "01/16/21",
        "last_updated": "2019-06-13",
        "submitted_by": "breardon@broadinstitute.org",
        "validated": True,
        "source_ids": [
            67
        ],
        "variant": {
            "feature_type": "somatic_variant",
            "feature_id": 168,
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


def test_assertion_168(assertions, assertion168):
    """Test moa harvester works correctly for assertions."""
    for a in assertions:
        if a['id'] == 168:
            actual = a
            break
    assert actual.keys() == assertion168.keys()
    keys = assertion168.keys()
    for key in keys:
        assert actual[key] == assertion168[key]
