"""A module for the Harvester base class"""


class Harvester:
    """A base class for content harvesters."""
def __init__(self):
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
