from pathlib import Path

from tests.conftest import check_source_harvest

from metakb.harvesters.cbioportal import CBioPortalHarvester
from metakb.schemas.app import SourceName
from metakb.source_data import SourceDataStore


def test_cbioportal_harvester(tmp_path: Path):
    harvester = CBioPortalHarvester(
        SourceDataStore(src_name=SourceName.CBIOPORTAL, harvested_dir=tmp_path)
    )
    check_source_harvest(harvester)
