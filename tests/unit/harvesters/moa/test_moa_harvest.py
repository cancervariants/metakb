"""Test MOAlmanac Harvester."""

from metakb import APP_ROOT
from metakb.harvesters.moa import MoaHarvester


def test_harvest():
    """Test MOAlmanac harvest method."""
    fn = "test_moa_harvester.json"
    assert MoaHarvester().harvest(filename=fn)
    file_path = APP_ROOT / "data" / "moa" / "harvester" / fn
    assert file_path.exists()
    file_path.unlink()
    assert not file_path.exists()
