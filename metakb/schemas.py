"""Common data model"""
from enum import Enum
from pydantic import BaseModel
from typing import List


class EvidenceLevel(Enum):
    """Define constraints for Evidence Level."""

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class XrefSystem(Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = 'ClinVar'
    CLINGEN = 'ClinGenAlleleRegistry'
    DB_SNP = 'dbSNP'
    NCBI = 'ncbigene'
    DISEASE_ONTOLOGY = 'DiseaseOntology'


class NamespacePrefix(Enum):
    """Define constraints for Namespace prefixes."""

    CIVIC = 'civic'
    NCIT = 'ncit'


class SourcePrefix(Enum):
    """Define constraints for source prefixes."""

    PUBMED = 'pmid'


class Predicate(str, Enum):
    """Define constraints for predicate."""

    SENSITIVITY = 'predicts_sensitivity_to'
    RESISTANCE = 'predicts_resistance_to'
    REDUCED_SENSITIVITY = 'predicts_reduced_sensitivity_to'
    ADVERSE_RESPONSE = 'predicts_adverse_response_to'


class VariationOrigin(Enum):
    """Define constraints for variant origin."""

    SOMATIC = 'somatic'
    RARE_GERMLINE = 'rare_germline'
    COMMON_GERMLINE = 'common_germline'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'N/A'


class TherapeuticProposition(BaseModel):
    """Define therapeutic proposition model"""

    predicate: Predicate
    variation_origin: VariationOrigin


class Direction(str, Enum):
    """Define constraints for evidence direction."""

    SUPPORTS = 'supports'
    DOES_NOT_SUPPORT = 'does_not_support'


class Evidence(BaseModel):
    """Define evidence model."""

    id: str
    description: str
    direction: Direction
    evidence_level: str
    strength: str


class EvidenceSource(BaseModel):
    """Define evidence source model."""

    id: str
    label: str
    description: str
    xrefs: List[str]
