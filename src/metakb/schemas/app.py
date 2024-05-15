"""Module containing app schemas and enums"""
from enum import StrEnum


class SourceName(StrEnum):
    """Define enum for sources that are supported"""

    CIVIC = "civic"
    MOA = "moa"

    def as_print_case(self) -> str:
        """Provide enum value with natural print casing (i.e. value-specific for
        natural text).

        :return: correctly-cased string
        :raise ValueError: if called on a source value that we forgot to define here
        """
        if self == "civic":
            return "CIViC"
        if self == "moa":
            return "MOA"
        raise ValueError
