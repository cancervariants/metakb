"""Common data model"""
from enum import Enum, IntEnum
from pydantic import BaseModel
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


class ValueObject(BaseModel):
    """Define model for value object."""

    id: str
    type: str


class Gene(ValueObject):
    """GA4GH Gene Value Object."""

    type = "Gene"


class Disease(ValueObject):
    """Disease Value Object"""

    type = "Disease"


class Therapy(ValueObject):
    """A procedure or substance used in the treatment of a disease."""

    type = "Therapy"


class Drug(Therapy):
    """A pharmacologic substance used to treat a medical condition."""

    type = "Drug"


class TherapeuticResponseProposition(BaseModel):
    """Define therapeutic Response Proposition model"""

    id: str
    type = PropositionType.PREDICTIVE.value
    predicate: Optional[PredictivePredicate]
    subject: str  # vrs:Variation
    object_qualifier: str  # vicc:Disease
    object: str  # Therapy value object


class MethodID(IntEnum):
    """Create AssertionMethod id constants for harvested sources."""

    CIVIC_EID_SOP = 1
    CIVIC_AID_AMP_ASCO_CAP = 2
    CIVIC_AID_ACMG = 3


class Statement(BaseModel):
    """Define Statement model."""

    id: str
    type = 'Statement'
    description: str
    direction: Optional[Direction]
    evidence_level: str
    proposition: str
    variation_origin: Optional[VariationOrigin]
    variation_descriptor: str
    therapy_descriptor: str
    disease_descriptor: str
    method: str
    supported_by: List[str]
    # contribution: str  TODO: After metakb first pass


class Document(BaseModel):
    """Define model for Source."""

    id: str
    document_id: Optional[str]
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
    authors: str


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


class Response(BaseModel):
    """Define the Response Model."""

    statements: List[Statement]
    propositions: List[TherapeuticResponseProposition]
    variation_descriptors: List[VariationDescriptor]
    gene_descriptors: List[GeneDescriptor]
    therapy_descriptors: List[ValueObjectDescriptor]
    disease_descriptors: List[ValueObjectDescriptor]
    methods: List[Method]
    documents: List[Document]
