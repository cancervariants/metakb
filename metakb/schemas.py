"""Common data model"""
from enum import Enum, IntEnum
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any, Type
from pydantic.types import StrictBool
from ga4gh.vrsatile.pydantic.vrsatile_model import ValueObjectDescriptor, \
    GeneDescriptor, VariationDescriptor


class SourceName(str, Enum):
    """Resources we import directly."""

    CIVIC = 'civic'
    MOA = 'moa'


class XrefSystem(str, Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = 'clinvar'
    CLINGEN = 'caid'
    DB_SNP = 'dbsnp'
    NCBI = 'ncbigene'
    DISEASE_ONTOLOGY = 'do'


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = 'pmid'
    ASCO = 'asco'


class NormalizerPrefix(str, Enum):
    """Define constraints for normalizer prefixes."""

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


class DiagnosticProposition(Proposition):
    """Defines the Diagnostic Proposition model."""

    type = PropositionType.DIAGNOSTIC.value
    predicate: Optional[DiagnosticPredicate]


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
    type = 'Document'


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
    type = 'Method'


class Response(BaseModel):
    """Define the Response Model."""

    statements: List[Statement]
    propositions: List[Union[TherapeuticResponseProposition,
                             PrognosticProposition,
                             DiagnosticProposition]]
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
    therapy_descriptor: Optional[str]
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
                "id": "civic.eid:2997",
                "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                "direction": "supports",
                "evidence_level": "civic.evidence_level:A",
                "variation_origin": "somatic",
                "proposition": "proposition:109",
                "variation_descriptor": "civic.vid:33",
                "therapy_descriptor": "civic.tid:146",
                "disease_descriptor": "civic.did:8",
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
                "statement_id": "civic.eid:2997",
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
                "statements": ["civic.eid:2997"],
                "propositions": ["proposition:109"]
            }


class SearchService(BaseModel):
    """Define model for Search Endpoint Response."""

    query: SearchQuery
    warnings: Optional[List[str]]
    matches: Matches
    statements: Optional[List[StatementResponse]]
    propositions: Optional[List[Union[TherapeuticResponseProposition,
                                      DiagnosticProposition,
                                      PrognosticProposition]]]
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
                    "statement_id": "civic.eid:2997",
                    "detail": False
                },
                "warnings": [],
                "matches": {
                    "statements": ["civic.eid:2997"],
                    "propositions": ["proposition:109"]
                },
                "statements": [
                    {
                        "id": "civic.eid:2997",
                        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                        "direction": "supports",
                        "evidence_level": "civic.evidence_level:A",
                        "variation_origin": "somatic",
                        "proposition": "proposition:109",
                        "variation_descriptor": "civic.vid:33",
                        "therapy_descriptor": "civic.tid:146",
                        "disease_descriptor": "civic.did:8",
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


class SearchIDService(BaseModel):
    """Define model for Search by ID Endpoint Response."""

    query: str
    warnings: Optional[List[str]]
    statement: Optional[StatementResponse]
    proposition: Optional[Union[TherapeuticResponseProposition,
                                DiagnosticProposition,
                                PrognosticProposition]]
    variation_descriptor: Optional[VariationDescriptor]
    gene_descriptor: Optional[GeneDescriptor]
    therapy_descriptor: Optional[ValueObjectDescriptor]
    disease_descriptor: Optional[ValueObjectDescriptor]
    document: Optional[Document]
    method: Optional[Method]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['SearchIDService']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "query": {
                    "node_id": "civic.vid:33"
                },
                "warnings": [],
                "matches": {
                    "node": "civic.vid:33"
                },
                "variation_descriptors": [
                    {
                        "id": "civic.vid:33",
                        "type": "VariationDescriptor",
                        "label": "L858R",
                        "description": "EGFR L858R has long been recognized "
                                       "as a functionally significant "
                                       "mutation in cancer, and is one of "
                                       "he most prevalent single mutations in"
                                       " lung cancer. Best described in "
                                       "non-small cell lung cancer (NSCLC), "
                                       "the mutation seems to confer "
                                       "sensitivity to first and second "
                                       "generation TKI's like gefitinib and"
                                       " neratinib. NSCLC patients with this"
                                       " mutation treated with TKI's show "
                                       "increased overall and "
                                       "progression-free survival, as "
                                       "compared to chemotherapy alone. "
                                       "Third generation TKI's are currently"
                                       " in clinical trials that specifically"
                                       " focus on mutant forms of EGFR, a few"
                                       " of which have shown efficacy in "
                                       "treating patients that failed to "
                                       "respond to earlier generation "
                                       "TKI therapies.",
                        "value_id": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",  # noqa: E501
                        "value": {
                            "location": {
                                "interval": {
                                    "end": 858,
                                    "start": 857,
                                    "type": "SimpleInterval"
                                },
                                "sequence_id": "ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",  # noqa: E501
                                "type": "SequenceLocation"
                            },
                            "state": {
                                "sequence": "R",
                                "type": "SequenceState"
                            },
                            "type": "Allele"
                        },
                        "xrefs": [
                            "clinvar:376280",
                            "clinvar:16609",
                            "clinvar:376282",
                            "caid:CA126713",
                            "dbsnp:121434568"
                        ],
                        "alternate_labels": [
                            "LEU858ARG"
                        ],
                        "extensions": [
                            {
                                "name": "civic_representative_coordinate",
                                "value": {
                                    "chromosome": "7",
                                    "start": 55259515,
                                    "stop": 55259515,
                                    "reference_bases": "T",
                                    "variant_bases": "G",
                                    "representative_transcript": "ENST00000275493.2",  # noqa: E501
                                    "ensembl_version": 75,
                                    "reference_build": "GRCh37"
                                },
                                "type": "Extension"
                            },
                            {
                                "name": "civic_actionability_score",
                                "value": "352.5",
                                "type": "Extension"
                            }
                        ],
                        "structural_type": "SO:0001583",
                        "expressions": [
                            {
                                "syntax": "hgvs:genomic",
                                "value": "NC_000007.13:g.55259515T>G",
                                "type": "Expression"
                            },
                            {
                                "syntax": "hgvs:protein",
                                "value": "NP_005219.2:p.Leu858Arg",
                                "type": "Expression"
                            },
                            {
                                "syntax": "hgvs:transcript",
                                "value": "NM_005228.4:c.2573T>G",
                                "type": "Expression"
                            },
                            {
                                "syntax": "hgvs:transcript",
                                "value": "ENST00000275493.2:c.2573T>G",
                                "type": "Expression"
                            }
                        ],
                        "gene_context": "civic.gid:19"
                    }
                ]
            }
