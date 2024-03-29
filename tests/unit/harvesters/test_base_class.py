"""Tests the Harvester base class."""
import pytest

from metakb.harvesters import base


@pytest.fixture(scope="module")
def bh():
    """Create a base Harvester fixture for testing."""
    return base.Harvester()


def test_base_harvester_harvest_not_implemented(bh):
    """The base Harvester harvest should raise a NotImplementedError."""
    with pytest.raises(NotImplementedError):
        bh.harvest()
