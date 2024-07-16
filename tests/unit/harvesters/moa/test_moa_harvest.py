"""Test MOAlmanac Harvester."""

from tests.conftest import check_source_harvest

from metakb.harvesters.moa import MoaHarvester


def test_harvest(tmp_path):
    """Test MOAlmanac harvest method."""
    moa = MoaHarvester()
    check_source_harvest(tmp_path, moa)
