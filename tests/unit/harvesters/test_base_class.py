"""This module tests the Harvester base class."""
from metakb.harvesters import base
import pytest


@pytest.fixture(scope='module')
def bh():
    """Create a base Harvester fixture for testing."""
    bh = base.Harvester()
    return bh


def test_base_harvester_harvest_not_implemented(bh):
    """The base Harvester harvest should raise a NotImplementedError."""
    with pytest.raises(NotImplementedError):
        bh.harvest()
