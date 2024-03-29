"""Module containing app schemas and enums"""
from enum import StrEnum


class SourceName(StrEnum):
    """Define enum for sources that are supported"""

    CIVIC = "civic"
    MOA = "moa"
