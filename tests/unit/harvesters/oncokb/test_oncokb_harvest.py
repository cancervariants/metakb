"""Test OncoKB Harvester"""
import os

from metakb.harvesters import OncoKBHarvester
from metakb import APP_ROOT, PROJECT_ROOT


def test_harvest():
    """Test OncoKB harvest method"""
    ONCOKB_API_TOKEN = os.environ.get("ONCOKB_API_TOKEN")
    o = OncoKBHarvester(api_token=ONCOKB_API_TOKEN)
    assert not o.harvest("")
    fn = "test_oncokb_harvester.json"
    variants_by_protein_change_path = PROJECT_ROOT / "tests" / "data" / "harvesters" / \
        "oncokb" / "variants_by_protein_change.csv"
    assert o.harvest(variants_by_protein_change_path, fn)
    for var in [o.genes, o.variants, o.metadata, o.diagnostic_levels,
                o.prognostic_levels, o.sensitive_levels, o.sensitive_levels]:
        assert var
    file_path = APP_ROOT / "data" / "oncokb" / "harvester" / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
