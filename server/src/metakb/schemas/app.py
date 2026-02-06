"""Module containing app schemas and enums"""

from enum import Enum


class SourceName(str, Enum):
    """Define enum for sources that are supported"""

    CIVIC = "civic"
    MOA = "moa"
    CBIOPORTAL = "cbioportal"

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
        if self == "cbioportal":
            return "cBioPortal"
        raise NotImplementedError

    def __repr__(self) -> str:
        """Print as simple string rather than enum wrapper, e.g. 'civic' instead of
        <NormalizerName.CIVIC: 'civic'>.

        Makes Click error messages prettier.

        :return: formatted enum value
        """
        return f"'{self.value}'"
