from pathlib import Path

from tests.conftest import check_source_harvest

from metakb.harvesters.civic import CivicHarvester
from metakb.schemas.app import SourceName
from metakb.source_data import SourceDataStore


def test_harvest(tmp_path: Path):
    harvester = CivicHarvester(
        SourceDataStore(src_name=SourceName.CIVIC, harvested_dir=tmp_path)
    )
    check_source_harvest(harvester)
