"""Test MOAlmanac Harvester."""
from metakb.harvesters.moalmanac import MOAlmanac
from metakb import APP_ROOT
import os


def test_harvest():
    """Test MOAlmanac harvest method."""
    assert not MOAlmanac().harvest(fn='')
    fn = 'test_moa_harvester.json'
    assert MOAlmanac().harvest(fn=fn)
    file_path = APP_ROOT / 'data' / 'moa' / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
