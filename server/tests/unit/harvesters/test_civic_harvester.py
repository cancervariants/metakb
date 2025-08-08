from pickle import UnpicklingError
from unittest.mock import MagicMock

import pytest
from civicpy import civic as civicpy

from metakb.harvesters.civic import LOCAL_CACHE_PATH, CivicHarvester

_real_load_cache = civicpy.load_cache


@pytest.fixture(autouse=True)
def stub_civicpy(monkeypatch):
    """Stub out civicpy.update_cache and civicpy.load_cache"""
    monkeypatch.setattr(civicpy, "update_cache", MagicMock(spec=civicpy.update_cache))
    monkeypatch.setattr(civicpy, "load_cache", MagicMock(spec=civicpy.load_cache))


def test_default_init():
    """Test that default init works correctly"""
    harvester = CivicHarvester()

    civicpy.update_cache.assert_not_called()
    civicpy.load_cache.assert_not_called()
    assert harvester.local_cache_path == LOCAL_CACHE_PATH


def test_init_update_cache_custom_path(tmp_path):
    """Test that init with update_cache and local_cache_path set work correctly"""
    custom_path = tmp_path / "cache.pkl"
    harvester = CivicHarvester(local_cache_path=str(custom_path))
    harvester.harvest(update_cache=True, update_from_remote=False)

    civicpy.update_cache.assert_called_once_with(from_remote_cache=False)
    assert harvester.local_cache_path == str(custom_path)


def test_init_update_cache_remote_default(tmp_path):
    """Test that init with update_cache=True defaults to remote cache update"""
    custom_path = tmp_path / "cache2.pkl"
    harvester = CivicHarvester(local_cache_path=str(custom_path))
    harvester.harvest(update_cache=True)

    civicpy.update_cache.assert_called_once_with(from_remote_cache=True)
    assert harvester.local_cache_path == str(custom_path)


def test_harvest_default_path_cache():
    """Test that harvest uses default cache path, ignores stale data, and returns None"""
    harvester = CivicHarvester()
    result = harvester.harvest(update_cache=False)

    civicpy.load_cache.assert_called_once_with(LOCAL_CACHE_PATH, on_stale="ignore")
    assert result is None


def test_harvest_custom_cache(tmp_path):
    """Test that harvest uses custom cache path, ignores stale data, and returns None"""
    custom_path = tmp_path / "harvest.pkl"
    harvester = CivicHarvester(local_cache_path=str(custom_path))
    result = harvester.harvest(update_cache=False)

    civicpy.load_cache.assert_called_once_with(str(custom_path), on_stale="ignore")
    assert not custom_path.exists()
    assert result is None


def test_harvest_raises_on_invalid_extension(tmp_path, monkeypatch):
    """Test that harvest raises UnpicklingError on non-pickle file extension"""
    custom_path = tmp_path / "cache.txt"
    custom_path.write_text("hello world")

    monkeypatch.setattr(civicpy, "load_cache", _real_load_cache)

    harvester = CivicHarvester(local_cache_path=str(custom_path))
    with pytest.raises(UnpicklingError):
        harvester.harvest(update_cache=False)
