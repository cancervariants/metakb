from pathlib import Path

from tests.conftest import check_source_harvest

from metakb.core.source_data import SourceDataStore
from metakb.harvesters import FdaPodaHarvester
from metakb.schemas.app import SourceName


def test_harvest(tmp_path: Path):
    harvester = FdaPodaHarvester(
        SourceDataStore(src_name=SourceName.FDA_PODA, harvested_dir=tmp_path)
    )
    check_source_harvest(harvester)
