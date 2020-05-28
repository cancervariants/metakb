"""This module tests the Harvester base class."""
from metakb.harvesters import base
from metakb.models.assertions import Assertion
import pytest


@pytest.fixture
def bh(scope='module'):
    """Create a base Harvester fixture for testing."""
    bh = base.Harvester()
    return bh


def test_base_harvester_harvest_not_implemented(bh):
    """The base Harvester harvest should raise a NotImplementedError."""
    with pytest.raises(NotImplementedError):
        bh.harvest()


@pytest.mark.skip(reason='This requires development of Assertions')
def test_base_harvester_yields_assertions(bh):
    """Harvesters should yield Assertion records."""
    for assertion in bh.iter_assertions():
        assert isinstance(assertion, Assertion)
    iter_assertions = list(bh.iter_assertions())
    iter_class = list(bh)
    for assertion1, assertion2 in zip(iter_assertions, iter_class):
        assert assertion1 == assertion2
