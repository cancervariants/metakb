"""Test CIViC Harvester."""
from metakb.harvesters.civic import CIViC
from metakb import PROJECT_ROOT
import os


def test_harvest():
    """Test CIViC harvest method."""
    assert not CIViC().harvest(fn='')
    fn = 'test_civic_harvester.json'
    assert CIViC().harvest(fn=fn)
    file_path = PROJECT_ROOT / 'data' / 'civic' / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()
