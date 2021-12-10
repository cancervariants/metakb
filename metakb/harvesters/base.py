"""A module for the Harvester base class"""
from metakb import APP_ROOT
import json
import logging

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Harvester:
    """A base class for content harvesters."""

    def __init__(self):
        """Initialize Harvester class."""
        self.assertions = []

    def harvest(self):
        """
        Retrieve and store records from a resource. Records may be stored in
        any manner, but must be retrievable by :method:`iterate_records`.

        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        raise NotImplementedError

    def iter_assertions(self):
        """
        Yield all :class:`ClinSigAssertion` records for the resource.

        :return: An iterator
        :rtype: Iterator[:class:`ClinSigAssertion`]
        """
        for statement in self.assertions:
            yield statement

    def create_json(self, fn, src, **kwargs) -> bool:
        """Create composite and individual JSON for harvested data.

        :param str fn: File name of composite json
        :param str src: Harvested source. Can be `civic` or `moa`
        :param list kwargs: Lists of evidence data types
        :return: `True` if JSON creation was successful. `False` otherwise.
        """
        composite_dict = dict()
        src_dir = APP_ROOT / 'data' / src / 'harvester'
        src_dir.mkdir(exist_ok=True, parents=True)
        try:
            for arg_name in kwargs:
                composite_dict[arg_name] = kwargs[arg_name]

                with open(f"{src_dir}/{arg_name}.json", 'w+') as f:
                    f.write(json.dumps(composite_dict[arg_name], indent=4))

            with open(f"{src_dir}/{fn}", 'w+') as f:
                json.dump(composite_dict, f, indent=4)
        except Exception as e:
            logger.error(f"Unable to create json: {e}")
            return False
        return True
