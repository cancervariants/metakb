"""A module for the Harvester base class"""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel

from metakb import APP_ROOT, DATE_FMT

logger = logging.getLogger(__name__)


class _HarvestedData(BaseModel):
    """Define output for harvested data from a source"""

    variants: list[dict]

    @classmethod
    def get_subclass_by_prefix(
        cls: type["_HarvestedData"], prefix: str
    ) -> type["_HarvestedData"]:
        """Get subclass whose name starts with provided prefix

        :param prefix: Prefix to search for in subclass names
        :raises ValueError: If no subclasses defined or if no subclass found with prefix
        :return: Matching subclass with given prefix, if found
        """
        subclasses = cls.__subclasses__()
        if not subclasses:
            msg = "No subclasses have been defined"
            raise ValueError(msg)

        for subclass in subclasses:
            if subclass.__name__.lower().startswith(prefix):
                return subclass

        msg = f"No subclass starting with '{prefix}' found"
        raise ValueError(msg)


class Harvester(ABC):
    """A base class for content harvesters."""

    @abstractmethod
    def harvest(self) -> _HarvestedData:
        """Get source harvester data

        :return: Harvested data
        """

    def save_harvested_data_to_file(
        self, harvested_data: _HarvestedData, harvested_filepath: Path | None = None
    ) -> bool:
        """Save harvested data to JSON file

        :param harvested_data: harvested data from a source
        :param harvested_filepath: Path to the JSON file where the harvested data will
            be stored. If not provided, will use the default path of
            ``<APP_ROOT>/data/<src_name>/harvester/<src_name>_harvester_YYYYMMDD.json``
        :return: ``True`` if JSON creation was successful. ``False`` otherwise.
        """
        src_name = self.__class__.__name__.lower().split("harvest")[0]

        if not harvested_filepath:
            harvester_dir = APP_ROOT / "data" / src_name / "harvester"
            harvester_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            harvested_filepath = harvester_dir / f"{src_name}_harvester_{today}.json"

        try:
            with (harvested_filepath).open("w+") as f:
                json.dump(harvested_data.model_dump(), f, indent=2)
        except Exception:
            logger.exception("Error creating %s harvester JSON", src_name)
            return False
        return True
