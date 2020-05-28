"""Data models for representing VICC records."""
from dataclasses import dataclass
from enum import Enum


class Biomarker:
    """
    Typically a protein or genomic sequence variant, a biomarker can also
    encompass systemic and complex molecular profiles.
    """

    pass


class Disease:
    """
    A diagnosed condition describing an impaired or deviant physiological
    state. Instances typically describe a type of cancer, e.g. Small Cell
    Lung Cancer.
    """

    pass


class Therapeutic:
    """
    A drug, drug class, regimen, or therapeutic procedure used in the
    treatment of :class:`Disease`.
    """

    pass


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
    therapeutic: Therapeutic
    type: AssertionType
