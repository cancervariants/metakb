"""Data models for Therapies and supporting concepts."""
from dataclasses import dataclass
from typing import List


@dataclass
class Treatment:
    """
    A treatment used in the course of a :class:`Therapy`.
    Implement in Therapy Normalizer Library?
    """

    pass


@dataclass
class Drug(Treatment):
    """
    A pharmacologic substance used to treat a :class:`Disease`.
    Implement in Therapy Normalizer Library?
    """

    pass


@dataclass
class Therapy:
    """
    A therapy used in the treatment of a :class:`Disease`.
    Implement in Therapy Normalizer Library?
    """

    treatments: List[Treatment]
