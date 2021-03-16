"""Common data model"""
from enum import Enum
from pydantic import BaseModel
from pydantic.fields import Field
from typing import List, Optional, Union


class XrefSystem(str, Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = 'clinvar'
    CLINGEN = 'caid'
    DB_SNP = 'dbsnp'
    NCBI = 'ncbigene'
    DISEASE_ONTOLOGY = 'do'


class NamespacePrefix(str, Enum):
    """Define constraints for Namespace prefixes."""

    CIVIC = 'civic'
    NCIT = 'ncit'


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = 'pmid'
    ASCO = 'asco'


class PropositionType(str, Enum):
    """Define constraints for proposition type."""

    PREDICTIVE = 'therapeutic_response_proposition'
    DIAGNOSTIC = 'diagnostic_proposition'
    PROGNOSTIC = 'prognostic_proposition'
    PREDISPOSING = 'predisposition_proposition'
    FUNCTIONAL = 'functional_consequence_proposition'
    ONCOGENIC = 'oncogenicity_proposition'


class Predicate(str, Enum):
    """Define constraints for predicate."""

    SENSITIVITY = 'predicts_sensitivity_to'
    RESISTANCE = 'predicts_resistance_to'
    REDUCED_SENSITIVITY = 'predicts_reduced_sensitivity_to'
    ADVERSE_RESPONSE = 'predicts_adverse_response_to'


class VariationOrigin(str, Enum):
    """Define constraints for variant origin."""

    SOMATIC = 'somatic'
    RARE_GERMLINE = 'rare_germline'
    COMMON_GERMLINE = 'common_germline'
    UNKNOWN = 'unknown'
    NOT_APPLICABLE = 'N/A'


class Direction(str, Enum):
    """Define constraints for evidence direction."""

    SUPPORTS = 'supports'
    DOES_NOT_SUPPORT = 'does_not_support'


class MoleculeContext(str, Enum):
    """Define constraints for types of molecule context."""

    GENOMIC = 'genomic'
    TRANSCRIPT = 'transcript'
    PROTEIN = 'protein'


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


class TherapeuticResponseProposition(BaseModel):
    """Define therapeutic Response Proposition model"""

    id: str = Field(..., alias='_id')
    type: Optional[str]
    predicate: Optional[Predicate]
    variation_origin: Optional[VariationOrigin]
    has_originating_context: str  # vrs:Variation
    gene: str
    disease_context: str  # vicc:Disease
    therapy: str  # Therapy value object


class Evidence(BaseModel):
    """Define evidence model."""

    id: str
    type = 'Evidence'
    description: str
    direction: Optional[Direction]
    evidence_level: str
    proposition: str
    variation_descriptor: str
    gene_descriptor: str
    therapy_descriptor: str
    disease_descriptor: str
    evidence_sources: List[str]
    # assertion: str  TODO
    # contribution: str  TODO: After metakb first pass


class EvidenceSource(BaseModel):
    """Define evidence source model."""

    id: str
    source_id: str
    label: str
    description: Optional[str]
    xrefs: Optional[List[str]]


class Extension(BaseModel):
    """Extend descriptions with other attributes unique to a content provider. -GA4GH"""  # noqa: E501

    type = 'Extension'
    name: str
    value: Union[str, dict, List]


class Expression(BaseModel):
    """Enable descriptions based on a specified nomenclature or syntax for representing an object. - GA4GH"""  # noqa: E501

    type = 'Expression'
    syntax: str
    value: str
    version: Optional[str]


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


class GeneDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Gene Value Objects."""

    type = 'GeneDescriptor'


class SequenceDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Sequence value objects."""

    type = 'SequenceDescriptor'
    residue_type: Optional[str]


class LocationDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Location value objects."""

    type = 'LocationDescriptor'
    sequence_descriptor: Optional[SequenceDescriptor]


class VariationDescriptor(ValueObjectDescriptor):
    """Reference GA4GH Variation value objects."""

    type = 'VariationDescriptor'
    molecule_context: Optional[MoleculeContext]
    structural_type: Optional[str]
    expressions: Optional[List[Expression]]
    ref_allele_seq: Optional[str]
    gene_context: Optional[Union[str, GeneDescriptor]]
    location_descriptor: Optional[LocationDescriptor]
    sequence_descriptor: Optional[SequenceDescriptor]
    allelic_state: Optional[str]
