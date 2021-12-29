"""Test MOAlmanac Harvester."""
from metakb.harvesters import MOAHarvester
from metakb import APP_ROOT
import os


def test_harvest():
    """Test MOAlmanac harvest method."""
    assert not MOAHarvester().harvest(fn='')
    fn = 'test_moa_harvester.json'
    assert MOAHarvester().harvest(fn=fn)
    file_path = APP_ROOT / 'data' / 'moa' / 'harvester' / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
