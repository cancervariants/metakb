"""A module for the CIViC harvester."""

from pathlib import Path

from civicpy import LOCAL_CACHE_PATH
from civicpy import civic as civicpy

from metakb.harvesters.base import FetchMode, Harvester


class CivicHarvester(Harvester):
    """A class for the CIViC harvester."""

    def harvest(self, fetch_mode: FetchMode = FetchMode.CHECK_STALE) -> Path:
        """Grab data from a source and stash a copy locally, returning the stashed location

        :param fetch_mode: set data caching/fetching behavior.
        :return: Location of performed data harvest
        """
        if fetch_mode == FetchMode.FORCE_REFRESH:
            civicpy.update_cache()
        civicpy_cache_path = Path(LOCAL_CACHE_PATH)
        return self.src_data_dir.save_harvested_file(civicpy_cache_path)
