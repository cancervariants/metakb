"""Create schemas for API"""

from typing import Literal

from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Statement
from pydantic import BaseModel, ConfigDict, StrictStr

from metakb import __version__


class ServiceMeta(BaseModel):
    """Metadata for MetaKB service."""

    name: Literal["metakb"] = "metakb"
    version: StrictStr = __version__
    url: Literal["https://github.com/cancervariants/metakb"] = (
        "https://github.com/cancervariants/metakb"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "metakb",
                "version": __version__,
                "url": "https://github.com/cancervariants/metakb",
            }
        }
    )


class SearchStatementsQuery(BaseModel):
    """Queries for the Search Statements Endpoint."""

    variation: StrictStr | None = None
    disease: StrictStr | None = None
    therapy: StrictStr | None = None
    gene: StrictStr | None = None
    statement_id: StrictStr | None = None


class SearchStatementsService(BaseModel):
    """Define model for Search Statements Endpoint Response."""

    query: SearchStatementsQuery
    warnings: list[StrictStr] = []
    statement_ids: list[StrictStr] = []
    statements: list[
        Statement
        | VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = []
    service_meta_: ServiceMeta


class NormalizedQuery(BaseModel):
    """Define structure of user-provided query. If possible, add normalized ID."""

    term: StrictStr
    normalized_id: StrictStr | None = None


class BatchSearchStatementsQuery(BaseModel):
    """Define query as reported in batch search statements endpoint."""

    variations: list[NormalizedQuery] = []


class BatchSearchStatementsService(BaseModel):
    """Define response model for batch search statements endpoint response."""

    query: BatchSearchStatementsQuery
    warnings: list[StrictStr] = []
    statement_ids: list[StrictStr] = []
    statements: list[
        Statement
        | VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = []
    service_meta_: ServiceMeta
