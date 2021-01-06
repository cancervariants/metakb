"""Test MOAlmanac source"""
import pytest
from metakb.harvesters.moalmanac import MOAlmanac


@pytest.fixture(scope='module')
def variants():
    """Create a list of variants."""
    moa = MOAlmanac()

    return moa._harvest_variants()


@pytest.fixture(scope='module')
def gata3():
    """Create a fixture for variant GATA3 p.M294K (Missense)."""
    return {
        "feature_type": "somatic_variant",
        "feature_id": 313,
        "gene": "GATA3",
        "chromosome": "10",
        "start_position": "8106058.0",
        "end_position": "8106058.0",
        "reference_allele": "T",
        "alternate_allele": "A",
        "cdna_change": "c.881T>A",
        "protein_change": "p.M294K",
        "variant_annotation": "Missense",
        "exon": "4.0",
        "rsid": None,
        "feature": "GATA3 p.M294K (Missense)"
    }


def test_variant_gata3(variants, gata3):
    """Test moa harvester works correctly for variants."""
    for v in variants:
        if v['feature_id'] == 313:
            actual = v
            break
    assert actual.keys() == gata3.keys()
    keys = gata3.keys()
    for key in keys:
        assert actual[key] == gata3[key]
