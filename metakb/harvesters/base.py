"""A module for the Harvester base class"""
from abc import ABC, abstractmethod


class Harvester(ABC):
    """An abstract class for content harvesters."""

    @abstractmethod
    def harvest(self, *args, **kwargs):
        """
        Retrieve and store records from a resource. Records may be stored in
        any manner, but must be retrievable by :method:`iterate_records`.

        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """

    @abstractmethod
    def iter_statements(self):
        """
        Yield all :class:`ClinSigAssertion` records for the resource.

        :return: An iterator
        :rtype: Iterator[:class:`ClinSigAssertion`]
        """
        pass
