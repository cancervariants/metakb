"""Common data model"""
from enum import Enum


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
