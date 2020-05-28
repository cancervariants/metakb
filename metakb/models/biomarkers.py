"""Data models for Biomarkers and supporting concepts."""
from dataclasses import dataclass
from typing import List
from enum import Enum


class VariationType(Enum):
    """A placeholder class that will be covered by the Variant Lexicon."""

    PROTEIN_SUBSTITUTION = 1


@dataclass
class Variation:
    """A placeholder class that will be covered by the Variant Lexicon."""

    pass


@dataclass
class Biomarker:
    """
    Typically a protein or genomic sequence variant, a biomarker can also
    encompass systemic and complex molecular profiles.
    """

    label: str
    genes: List[str]
    variations: List[Variation]
