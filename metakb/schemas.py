"""Common data model"""
from enum import Enum, IntEnum
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
    MOA = 'moa'


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
    PATHOGENIC = 'pathogenicity_proposition'


class PredictivePredicate(str, Enum):
    """Define constraints for predictive predicate."""

    SENSITIVITY = 'predicts_sensitivity_to'
    RESISTANCE = 'predicts_resistance_to'


class DiagnosticPredicate(str, Enum):
    """Define constraints for diagnostic predicate."""

    POSITIVE = 'is_diagnostic_inclusion_criterion_for'
    NEGATIVE = 'is_diagnostic_exclusion_criterion_for'


class PrognosticPredicate(str, Enum):
    """Define constraints for prognostic predicate."""

    BETTER_OUTCOME = 'is_prognostic_of_better_outcome_for'
    POOR_OUTCOME = 'is_prognostic_of_worse_outcome_for'


class PathogenicPredicate(str, Enum):
    """Define constraints for the pathogenicity predicate."""

    UNCERTAIN_SIGNIFICANCE = 'is_of_uncertain_significance_for'
    PATHOGENIC = 'is_pathogenic_for'
    BENIGN = 'is_benign_for'


class FunctionalPredicate(str, Enum):
    """Define constraints for functional predicate."""

    GAIN_OF_FUNCTION = 'causes_gain_of_function_of'
    LOSS_OF_FUNCTION = 'causes_loss_of_function_of'
    UNALTERED_FUNCTION = 'does_not_change_function_of'
    NEOMORPHIC = 'causes_neomorphic_function_of'
    DOMINATE_NEGATIVE = 'causes_dominant_negative_function_of'


class VariationOrigin(str, Enum):
    """Define constraints for variant origin."""

    SOMATIC = 'somatic'
    GERMLINE = 'germline'
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
    type = PropositionType.PREDICTIVE.value
    predicate: Optional[PredictivePredicate]
    variation_origin: Optional[VariationOrigin]
    has_originating_context: Optional[str]  # vrs:Variation
    disease_context: Optional[str]  # vicc:Disease
    therapy: Optional[str]  # Therapy value object


class MethodID(IntEnum):
    """Create AssertionMethod id constants for harvested sources."""

    CIVIC_EID_SOP = 1
    CIVIC_AID_AMP_ASCO_CAP = 2
    CIVIC_AID_ACMG = 3
    MOA_EID_BIORXIV = 4


class Assertion(BaseModel):
    """Define assertion model."""

    id: str
    type = 'Assertion'
    description: str
    direction: Optional[Direction]
    assertion_level: str
    proposition: str
    methods: List[str]
    evidence: List[str]
    document: str
    # contributions: List[str]


class Evidence(BaseModel):
    """Define evidence model."""

    id: str
    type = 'Evidence'
    description: Optional[str]
    direction: Optional[Direction]
    evidence_level: str
    proposition: str
    variation_descriptor: str
    therapy_descriptor: Optional[str]
    disease_descriptor: Optional[str]
    method: str
    document: str
    # contribution: str  TODO: After metakb first pass


class Document(BaseModel):
    """Define model for Document."""

    id: str
    document_id: str
    label: str
    description: Optional[str]
    xrefs: Optional[List[str]]


class Date(BaseModel):
    """Define model for date."""

    year: int
    month: Optional[int]
    day: Optional[int]


class Method(BaseModel):
    """Define model for methods used in evidence curation and classifications."""  # noqa: E501

    id: str
    label: str
    url: str
    version: Date
    reference: str


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
    value: Gene


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
