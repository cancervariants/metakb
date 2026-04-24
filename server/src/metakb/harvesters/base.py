"""A module for the Harvester base class"""

import logging
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path

from metakb.source_data import SourceDataStore

_logger = logging.getLogger(__name__)


class FetchMode(StrEnum):
    """Define options for fetching data"""

    FORCE_REFRESH = "force_refresh"  # always hit remote
    CHECK_STALE = "check_stale"  # conditional refresh
    USE_LOCAL = "use_local"  # never hit remote


class Harvester(ABC):
    """A base class for content harvesters."""

    def __init__(self, src_data_dir: SourceDataStore):
        """Initialize harvester class

        :param src_data_dir: container for MetaKB-managed data for this source
        """
        _logger.info(
            "Initializing %s with data dir {%s}", self.__class__.__name__, src_data_dir
        )
        self.src_data_dir = src_data_dir

    @abstractmethod
    def harvest(self, fetch_mode: FetchMode = FetchMode.CHECK_STALE) -> Path:
        """Grab data from a source and stash a copy locally, returning the stashed location

        :param fetch_mode: set data caching/fetching behavior. Not evenly used across sources.
        :return: Location of performed data harvest
        """
        raise NotImplementedError
