"""A module for the Harvester base class"""
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime as dt

from metakb import APP_ROOT, DATE_FMT

logger = logging.getLogger("metakb.harvesters.base")
logger.setLevel(logging.DEBUG)


class Harvester:
    """A base class for content harvesters."""

    def __init__(self) -> None:
        """Initialize Harvester class."""
        self.assertions = []

    def harvest(self) -> bool:
        """
        Retrieve and store records from a resource. Records may be stored in
        any manner, but must be retrievable by :method:`iterate_records`.

        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        raise NotImplementedError

    def create_json(self, items: Dict[str, List],
                    filename: Optional[str] = None) -> bool:
        """Create composite and individual JSON for harvested data.

        :param Dict items: item types keyed to Lists of values
        :param Optional[str] filename: custom filename for composite document
        :return: `True` if JSON creation was successful. `False` otherwise.
        """
        composite_dict = dict()
        src = self.__class__.__name__.lower().split("harvest")[0]
        src_dir = APP_ROOT / "data" / src / "harvester"
        src_dir.mkdir(exist_ok=True, parents=True)
        today = dt.strftime(dt.today(), DATE_FMT)
        try:
            for item_type, item_list in items.items():
                composite_dict[item_type] = item_list

                with open(src_dir / f"{item_type}_{today}.json", "w+") as f:
                    f.write(json.dumps(item_list, indent=4))
            if filename is None:
                filename = f"{src}_harvester_{today}.json"
            with open(src_dir / filename, "w+") as f:
                f.write(json.dumps(composite_dict, indent=4))
        except Exception as e:
            logger.error(f"Unable to create json: {e}")
            return False
        return True
