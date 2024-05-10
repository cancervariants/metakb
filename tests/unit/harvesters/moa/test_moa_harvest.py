"""Test MOAlmanac Harvester."""

from metakb.harvesters.moa import MoaHarvester


def test_harvest(tmp_path):
    """Test MOAlmanac harvest method."""
    moa = MoaHarvester()
    harvested_data = moa.harvest()

    try:
        harvested_filepath = tmp_path / "test_moa_harvester.json"
        moa.save_harvested_data_to_file(
            harvested_data, harvested_filepath=harvested_filepath
        )
    finally:
        assert harvested_filepath.exists()
        harvested_filepath.unlink()
        assert not harvested_filepath.exists()
