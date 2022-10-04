"""Test CIViC Harvester."""
from metakb.harvesters import CIViCHarvester
from metakb import APP_ROOT
import os


def test_harvest():
    """Test CIViC harvest method."""
    assert not CIViCHarvester().harvest(filename='')
    fn = 'test_civic_harvester.json'
    assert CIViCHarvester().harvest(filename=fn)
    file_path = APP_ROOT / 'data' / 'civic' / 'harvester' / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
