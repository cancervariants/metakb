"""Test PMKB harvester."""
from metakb.harvesters.pmkb import PMKB
from metakb import PROJECT_ROOT
import os


def test_harvest():
    """Test PMKB harvest method."""
    assert not PMKB().harvest(fn='')
    fn = 'test_pmkb_harvester.json'
    assert PMKB().harvest(fn=fn)
    file_path = PROJECT_ROOT / 'data' / 'pmkb' / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
