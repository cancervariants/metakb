"""Data models for Assertions and supporting concepts."""
from dataclasses import dataclass
from .biomarkers import Biomarker
from .diseases import Disease
from .therapies import Therapy
from enum import Enum


class AssertionType(Enum):
    """
    The clinical significance assertion types, drawn from the
    `AMP/ASCO/CAP Guidelines`_ describing evidence.

    _AMP/ASCO/CAP Guidelines: https://pubmed.ncbi.nlm.nih.gov/27993330/
    """

    THERAPEUTIC_PREDICTIVE = 1
    DIAGNOSTIC = 2
    PROGNOSTIC = 3
    PREDISPOSING = 4


@dataclass
class Assertion:
    """
    A VICC assertion of the clinical significance of a :class:`Biomarker` to a
    :class:`Disease` (when applicable), along with provenance of the supporting
    evidence.
    """

    biomarker: Biomarker
    disease: Disease
    therapy: Therapy
    type: AssertionType
