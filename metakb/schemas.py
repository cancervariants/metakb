"""Common data model"""
from enum import Enum, IntEnum
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any, Type
from pydantic.types import StrictBool


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


class NormalizerPrefix(str, Enum):
    """Define contraints for normalizer prefixes."""

    GENE = 'gene'


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


class Proposition(BaseModel):
    """Define Proposition model."""

    id: str
    type: str
    predicate: Optional[Union[PredictivePredicate, DiagnosticPredicate,
                        PrognosticPredicate, PathogenicPredicate,
                        FunctionalPredicate]]
    subject: str  # vrs:Variation
    object_qualifier: str  # vicc:Disease


class TherapeuticResponseProposition(Proposition):
    """Define therapeutic Response Proposition model"""

    type = PropositionType.PREDICTIVE.value
    predicate: Optional[PredictivePredicate]
    object: str  # Therapy value object

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['TherapeuticResponseProposition']) \
                -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "id": "proposition:109",
                "predicate": "predicts_sensitivity_to",
                "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
                "object_qualifier": "ncit:C2926",
                "object": "ncit:C66940",
                "type": "therapeutic_response_proposition"
            }


class PrognosticProposition(Proposition):
    """Defines the Prognostic Proposition model."""

    type = PropositionType.PROGNOSTIC.value
    predicate: Optional[PrognosticPredicate]


class MethodID(IntEnum):
    """Create AssertionMethod id constants for harvested sources."""

    CIVIC_EID_SOP = 1
    CIVIC_AID_AMP_ASCO_CAP = 2
    CIVIC_AID_ACMG = 3
    MOA_ASSERTION_BIORXIV = 4


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
    therapy_descriptor: Optional[str]
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

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['StatementResponse']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "year": 2019,
                "month": 11,
                "day": 29
            }


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
    propositions: List[Union[TherapeuticResponseProposition,
                             PrognosticProposition]]
    variation_descriptors: List[VariationDescriptor]
    gene_descriptors: List[GeneDescriptor]
    therapy_descriptors: Optional[List[ValueObjectDescriptor]]
    disease_descriptors: List[ValueObjectDescriptor]
    methods: List[Method]
    documents: List[Document]


class StatementResponse(BaseModel):
    """Define Statement Response for Search Endpoint."""

    id: str
    type = 'Statement'
    description: str
    direction: Optional[Direction]
    evidence_level: str
    variation_origin: Optional[VariationOrigin]
    proposition: str
    variation_descriptor: str
    therapy_descriptor: str
    disease_descriptor: str
    method: str
    supported_by: List[str]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['StatementResponse']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "id": "civic:eid2997",
                "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                "direction": "supports",
                "evidence_level": "civic.evidence_level:A",
                "variation_origin": "somatic",
                "proposition": "proposition:109",
                "variation_descriptor": "civic:vid33",
                "therapy_descriptor": "civic:tid146",
                "disease_descriptor": "civic:did8",
                "method": "method:001",
                "supported_by": [
                    "pmid:23982599"
                ],
                "type": "Statement"
            }


class SearchQuery(BaseModel):
    """Queries for the Search Endpoint."""

    variation: Optional[str]
    disease: Optional[str]
    therapy: Optional[str]
    gene: Optional[str]
    statement_id: Optional[str]
    detail: StrictBool

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['SearchQuery']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "variation": "NP_005219.2:p.Leu858Arg",
                "disease": "Lung Non-small Cell Carcinoma",
                "therapy": "Afatinib",
                "statement_id": "civic:eid2997",
                "detail": False
            }


class Matches(BaseModel):
    """Statements and Propositions that match the queried parameters."""

    statements: Optional[List[str]]
    propositions: Optional[List[str]]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['Matches']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "statements": ["civic:eid2997"],
                "propositions": ["proposition:109"]
            }


class SearchService(BaseModel):
    """Define model for Search Endpoint Response."""

    query: SearchQuery
    warnings: Optional[List[str]]
    matches: Matches
    statements: Optional[List[StatementResponse]]
    propositions: Optional[List[TherapeuticResponseProposition]]
    variation_descriptors: Optional[List[VariationDescriptor]]
    gene_descriptors: Optional[List[GeneDescriptor]]
    therapy_descriptors: Optional[List[ValueObjectDescriptor]]
    disease_descriptors: Optional[List[ValueObjectDescriptor]]
    methods: Optional[List[Method]]
    documents: Optional[List[Document]]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['SearchService']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "query": {
                    "variation": "EGFR L858R",
                    "disease": "Lung Non-small Cell Carcinoma",
                    "therapy": "Afatinib",
                    "statement_id": "civic:eid2997",
                    "detail": False
                },
                "warnings": [],
                "matches": {
                    "statements": ["civic:eid2997"],
                    "propositions": ["proposition:109"]
                },
                "statements": [
                    {
                        "id": "civic:eid2997",
                        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                        "direction": "supports",
                        "evidence_level": "civic.evidence_level:A",
                        "variation_origin": "somatic",
                        "proposition": "proposition:109",
                        "variation_descriptor": "civic:vid33",
                        "therapy_descriptor": "civic:tid146",
                        "disease_descriptor": "civic:did8",
                        "method": "method:001",
                        "supported_by": [
                            "pmid:23982599"
                        ],
                        "type": "Statement"
                    }
                ],
                "propositions": [
                    {
                        "id": "proposition:109",
                        "predicate": "predicts_sensitivity_to",
                        "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
                        "object_qualifier": "ncit:C2926",
                        "object": "ncit:C66940",
                        "type": "therapeutic_response_proposition"
                    }
                ]
            }
