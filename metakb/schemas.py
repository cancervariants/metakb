"""Common data model"""
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Union


class EvidenceLevel(Enum):
    """Define constraints for Evidence Level."""

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class XrefSystem(Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = 'clinvar'
    CLINGEN = 'caid'
    DB_SNP = 'dbsnp'
    NCBI = 'ncbigene'
    DISEASE_ONTOLOGY = 'do'


class NamespacePrefix(Enum):
    """Define constraints for Namespace prefixes."""

    CIVIC = 'civic'
    NCIT = 'ncit'


class SourcePrefix(Enum):
    """Define constraints for source prefixes."""

    PUBMED = 'pmid'
    ASCO = 'asco'


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
    direction: Optional[Direction]
    evidence_level: str
    strength: str


class EvidenceSource(BaseModel):
    """Define evidence source model."""

    id: str
    label: str
    description: str
    xrefs: List[str]


class Extension(BaseModel):
    """Extend descriptions with other attributes unique to a content provider. -GA4GH"""  # noqa: E501

    type = 'Extension'
    name: str
    value: Union[str, dict, List]


class ValueObjectDescriptor(BaseModel):
    """GA4GH Value Object Descriptor."""

    id: str
    type: str
    label: Optional[str]
    description: Optional[str]
    value_id: Optional[str]
    value: Optional[dict]
    xrefs: Optional[List[str]]
    alternate_labels: Optional[List[str]]
    extensions: Optional[List[Extension]]


class MoleculeContext(str, Enum):
    """Define constraints for types of molecule context."""

    GENOMIC = 'genomic'
    TRANSCRIPT = 'transcript'
    PROTEIN = 'protein'


class Expression(BaseModel):
    """Enable descriptions based on a specified nomenclature or syntax for representing an object. - GA4GH"""  # noqa: E501

    type = 'Expression'
    syntax: str
    value: str
    version: Optional[str]


class GeneDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Gene Value Objects."""

    type = 'GeneDescriptor'


class Gene(BaseModel):
    """GA4GH Gene Value Object."""

    gene_id: str
    type = "Gene"


class Disease(BaseModel):
    """Disease Value Object"""

    disease_id: str
    type = "Disease"


class Therapy(BaseModel):
    """Therapy Value Object"""

    therapy_id: str
    type = "Therapy"


class VariationDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Variation Value Objects."""

    type = 'VariationDescriptor'
    molecule_context: Optional[MoleculeContext]
    structural_type: Optional[str]
    expressions: Optional[List[Expression]]
    ref_allele_seq: Optional[str]
    gene_context: Optional[Union[str, GeneDescriptor]]
