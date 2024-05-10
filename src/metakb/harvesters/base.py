"""A module for the Harvester base class"""
import datetime
import json
import logging
from abc import abstractmethod

from metakb import APP_ROOT, DATE_FMT

logger = logging.getLogger(__name__)


class Harvester:
    """A base class for content harvesters."""

    def harvest(self, harvested_filepath: str | None = None) -> None:
        """Retrieve records from a resource and store harvested data in a JSON file.

        :param harvested_filepath: Path to the JSON file where the harvested data will
            be stored. If not provided, will use the default path of
            ``<APP_ROOT>/data/<src_name>/harvester/<src_name>_harvester_YYYYMMDD.json``
        """
        harvested_data = self.get_harvester_data()
        self.create_json(harvested_data, harvested_filepath=harvested_filepath)

    @abstractmethod
    def get_harvester_data(self) -> dict[str, list[dict]]:
        """Get source harvester data

        :return: Dictionary with each key representing a source item type and its
            corresponding value being a list of records for that source item type
        """

    def create_json(
        self, items: dict[str, list], harvested_filepath: str | None = None
    ) -> bool:
        """Create composite and individual JSON for harvested data.

        :param items: item types keyed to Lists of values
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

        composite_dict = {}
        try:
            for item_type, item_list in items.items():
                composite_dict[item_type] = item_list

            with (harvested_filepath).open("w+") as f:
                json.dump(composite_dict, f, indent=2)
        except Exception as e:
            logger.error("Error creating %s harvester JSON: %s", src_name, e)
            return False
        return True
