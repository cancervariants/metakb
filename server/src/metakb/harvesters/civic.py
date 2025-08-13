"""A module for the CIViC harvester."""

import logging

from civicpy import LOCAL_CACHE_PATH
from civicpy import civic as civicpy

from metakb.harvesters.base import Harvester

_logger = logging.getLogger(__name__)


class CivicHarvester(Harvester[None]):
    """A class for the CIViC harvester."""

    def __init__(
        self,
        local_cache_path: str = LOCAL_CACHE_PATH,
    ) -> None:
        """Initialize CivicHarvester class.

        :param local_cache_path: A filepath destination for the retrieved remote
            cache. This parameter defaults to LOCAL_CACHE_PATH from civicpy.
        """
        self.local_cache_path = local_cache_path

    def harvest(
        self, update_cache: bool = False, update_from_remote: bool = True
    ) -> None:
        """Harvest CIViC data

        :param update_cache: ``True`` if civicpy cache should be updated. Note
            this will take several minutes. ``False`` if to use local cache.
        :param update_from_remote: If set to ``True``, civicpy.update_cache will first
            download the remote cache designated by REMOTE_CACHE_URL, store it
            to LOCAL_CACHE_PATH, and then load the downloaded cache into memory.
            This parameter defaults to ``True``.
        """
        if update_cache:
            civicpy.update_cache(from_remote_cache=update_from_remote)

        civicpy.load_cache(self.local_cache_path, on_stale="ignore")
        _logger.info("Harvested data from %s", self.local_cache_path)
