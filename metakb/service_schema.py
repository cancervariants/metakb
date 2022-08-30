"""Define schemas for MetaKB service"""
from typing import List, Optional, Union, Dict, Any, Type

from ga4gh.vrsatile.pydantic.vrs_models import CURIE
from ga4gh.vrsatile.pydantic.vrsatile_models import GeneDescriptor, \
    VariationDescriptor, TherapeuticDescriptor, DiseaseDescriptor
from pydantic import BaseModel
from pydantic.types import StrictBool, StrictStr


from metakb.schemas import Direction, VariationGermlinePathogenicityProposition, \
    VariationGermlinePathogenicityStatement, \
    VariationNeoplasmTherapeuticResponseProposition, \
    VariationNeoplasmTherapeuticResponseStatement, Method, Document, VariationOrigin
from metakb.version import __version__, LAST_UPDATED


class Response(BaseModel):
    """Define the Response Model."""

    statements: List[Union[VariationGermlinePathogenicityStatement,
                           VariationNeoplasmTherapeuticResponseStatement]]
    target_propositions: List[Union[VariationGermlinePathogenicityProposition,
                                    VariationNeoplasmTherapeuticResponseProposition]]
    variation_descriptors: List[VariationDescriptor]
    gene_descriptors: List[GeneDescriptor]
    therapeutic_descriptors: Optional[List[TherapeuticDescriptor]]
    disease_descriptors: List[DiseaseDescriptor]
    methods: List[Method]
    documents: List[Document]


class NestedStatementResponse(BaseModel):
    """Define Statement Response for Search Endpoint."""

    id: CURIE
    type: StrictStr
    description: StrictStr
    direction: Optional[Direction]
    evidence_level: CURIE
    variation_origin: Optional[VariationOrigin]
    target_proposition: List[Union[VariationGermlinePathogenicityProposition,
                                   VariationNeoplasmTherapeuticResponseProposition]]
    variation_descriptor: VariationDescriptor
    therapeutic_descriptor: Optional[TherapeuticDescriptor]
    disease_descriptor: DiseaseDescriptor
    method: Method
    documents: List[Document]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['NestedStatementResponse']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            # TODO: Update
            schema['example'] = {}


class SearchQuery(BaseModel):
    """Queries for the Search Endpoint."""

    variation: Optional[StrictStr]
    disease: Optional[StrictStr]
    therapeutic: Optional[StrictStr]
    gene: Optional[StrictStr]
    statement_id: Optional[StrictStr]
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
                "therapeutic": "Afatinib",
                "statement_id": "civic.eid:2997",
                "detail": False
            }


class SearchStatementsQuery(BaseModel):
    """Queries for the Search Endpoint."""

    variation: Optional[StrictStr]
    disease: Optional[StrictStr]
    therapy: Optional[StrictStr]
    gene: Optional[StrictStr]
    statement_id: Optional[StrictStr]

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['SearchStatementsQuery']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            schema['example'] = {
                "variation": "NP_005219.2:p.Leu858Arg",
                "disease": "Lung Non-small Cell Carcinoma",
                "therapeutic": "Afatinib",
                "statement_id": "civic.eid:2997"
            }


class Matches(BaseModel):
    """Statements and Propositions that match the queried parameters."""

    statements: List[StrictStr]
    propositions: List[StrictStr]

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
                "propositions": ["proposition:133"]
            }


class ServiceMeta(BaseModel):
    """Metadata for MetaKB service."""

    name = "metakb"
    version = __version__
    last_updated = LAST_UPDATED
    url = "https://github.com/cancervariants/metakb"

    class Config:
        """Configure schema example."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type["ServiceMeta"]) -> None:
            """Configure OpenAPI schema"""
            if "title" in schema.keys():
                schema.pop("title", None)
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)
            schema["example"] = {
                "name": "metakb",
                "version": "1.1.0-alpha.4",
                "last_updated": "2021-12-16",
                "url": "https://github.com/cancervariants/metakb"
            }


class SearchService(BaseModel):
    """Define model for Search Endpoint Response."""

    query: SearchQuery
    warnings: Optional[List[str]]
    matches: Matches
    statements: Optional[List[Union[VariationGermlinePathogenicityStatement,
                                    VariationNeoplasmTherapeuticResponseStatement]]]
    target_propositions: Optional[List[Union[VariationGermlinePathogenicityProposition,
                                             VariationNeoplasmTherapeuticResponseProposition]]]  # noqa: E501
    variation_descriptors: Optional[List[VariationDescriptor]]
    gene_descriptors: Optional[List[GeneDescriptor]]
    therapeutic_descriptors: Optional[List[TherapeuticDescriptor]]
    disease_descriptors: Optional[List[DiseaseDescriptor]]
    methods: Optional[List[Method]]
    documents: Optional[List[Document]]
    service_meta_: ServiceMeta

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
            # TODO: Update
            schema['example'] = {}


class SearchIDService(BaseModel):
    """Define model for Search by ID Endpoint Response."""

    query: str
    warnings: Optional[List[str]]
    statement: Optional[Union[VariationGermlinePathogenicityStatement,
                              VariationNeoplasmTherapeuticResponseStatement]]
    target_proposition: Union[VariationGermlinePathogenicityProposition,
                              VariationNeoplasmTherapeuticResponseProposition]
    variation_descriptor: Optional[VariationDescriptor]
    gene_descriptor: Optional[GeneDescriptor]
    therapeutic_descriptor: Optional[TherapeuticDescriptor]
    disease_descriptor: Optional[DiseaseDescriptor]
    document: Optional[Document]
    method: Optional[Method]
    service_meta_: ServiceMeta

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
            # TODO: Update
            schema['example'] = {}


class SearchStatementsService(BaseModel):
    """Define model for Search Statements Endpoint Response."""

    query: SearchStatementsQuery
    warnings: Optional[List[str]]
    matches: Matches
    statements: Optional[List[NestedStatementResponse]]
    service_meta_: ServiceMeta

    class Config:
        """Configure examples."""

        @staticmethod
        def schema_extra(schema: Dict[str, Any],
                         model: Type['SearchStatementsService']) -> None:
            """Configure OpenAPI schema"""
            if 'title' in schema.keys():
                schema.pop('title', None)
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)
            # TODO: Update
            schema['example'] = {}
