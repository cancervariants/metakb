"""A module for the Harvester base class"""
import datetime
import json
import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from metakb import APP_ROOT, DATE_FMT

logger = logging.getLogger(__name__)


class _HarvestedData(BaseModel):
    """Define output for harvested data from a source"""

    variants: list[dict]


class Harvester(ABC):
    """A base class for content harvesters."""

    @abstractmethod
    def harvest(self) -> _HarvestedData:
        """Get source harvester data

        :return: Harvested data
        """

    def save_harvested_data_to_file(
        self, harvested_data: _HarvestedData, harvested_filepath: str | None = None
    ) -> bool:
        """Save harvested data to JSON file

        :param harvested_data: harvested data from a source
        :param harvested_filepath: Path to the JSON file where the harvested data will
            be stored. If not provided, will use the default path of
            ``<APP_ROOT>/data/<src_name>/harvester/<src_name>_harvester_YYYYMMDD.json``
        :return: `True` if JSON creation was successful. `False` otherwise.
        """
        src_name = self.__class__.__name__.lower().split("harvest")[0]

        if not harvested_filepath:
            harvester_dir = APP_ROOT / "data" / src_name / "harvester"
            harvester_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.timezone.utc), DATE_FMT
            )
            harvested_filepath = harvester_dir / f"{src_name}_harvester_{today}.json"

        try:
            with (harvested_filepath).open("w+") as f:
                json.dump(harvested_data.model_dump(), f, indent=2)
        except Exception as e:
            logger.error("Error creating %s harvester JSON: %s", src_name, e)
            return False
        return True
