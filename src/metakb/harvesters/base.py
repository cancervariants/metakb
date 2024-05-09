"""A module for the Harvester base class"""
import datetime
import json
import logging
from typing import Dict, List, Optional

from metakb import APP_ROOT, DATE_FMT

logger = logging.getLogger(__name__)


class Harvester:
    """A base class for content harvesters."""

    def harvest(self) -> bool:
        """Retrieve and store records from a resource. Records may be stored in
        any manner, but must be retrievable by :method:`iterate_records`.

        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        raise NotImplementedError

    def create_json(
        self, items: Dict[str, List], filename: Optional[str] = None
    ) -> bool:
        """Create composite and individual JSON for harvested data.

        :param items: item types keyed to Lists of values
        :param filename: custom filename for composite document
        :return: `True` if JSON creation was successful. `False` otherwise.
        """
        composite_dict = {}
        src = self.__class__.__name__.lower().split("harvest")[0]
        src_dir = APP_ROOT / "data" / src / "harvester"
        src_dir.mkdir(exist_ok=True, parents=True)
        today = datetime.datetime.strftime(
            datetime.datetime.now(tz=datetime.timezone.utc), DATE_FMT
        )
        try:
            for item_type, item_list in items.items():
                composite_dict[item_type] = item_list

                with (src_dir / f"{item_type}_{today}.json").open("w+") as f:
                    f.write(json.dumps(item_list, indent=4))
            if not filename:
                filename = f"{src}_harvester_{today}.json"
            with (src_dir / filename).open("w+") as f:
                f.write(json.dumps(composite_dict, indent=4))
        except Exception as e:
            logger.error("Unable to create json: %s", e)
            return False
        return True
