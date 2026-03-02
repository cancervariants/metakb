from tests.conftest import check_source_harvest

from metakb.harvesters import FdaPodaHarvester


def test_harvest(tmp_path):
    fda = FdaPodaHarvester()
    check_source_harvest(tmp_path, fda)
