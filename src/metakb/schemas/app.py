"""Module containing app schemas and enums"""
from enum import Enum


class SourceName(str, Enum):
    """Define enum for sources that are supported"""

    CIVIC = "civic"
    MOA = "moa"
