from pathlib import Path

from tests.conftest import check_source_harvest

from metakb.core.source_data import SourceDataStore
from metakb.harvesters import MoaHarvester
from metakb.schemas.app import SourceName


def test_harvest(tmp_path: Path):
    harvester = MoaHarvester(
        SourceDataStore(src_name=SourceName.MOA, harvested_dir=tmp_path)
    )
    check_source_harvest(harvester)
