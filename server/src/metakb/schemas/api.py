"""Create schemas for API"""

from enum import Enum
from typing import Literal

from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Statement
from ga4gh.vrs import VRS_VERSION
from ga4gh.vrs import (
    __version__ as vrs_python_version,
)
from pydantic import BaseModel, ConfigDict, StrictStr

from metakb import __version__


class ServiceEnvironment(str, Enum):
    """Define current runtime environment."""

    DEV = "dev"
    PROD = "prod"
    TEST = "test"
    STAGING = "staging"


class ServiceOrganization(BaseModel):
    """Define service_info response for organization field"""

    name: Literal["Variant Interpretation for Cancer Consortium"] = (
        "Variant Interpretation for Cancer Consortium"
    )
    url: Literal["https://cancervariants.org/"] = "https://cancervariants.org/"


class ServiceType(BaseModel):
    """Define service_info response for type field"""

    group: Literal["org.cancervariants"] = "org.cancervariants"
    artifact: Literal["MetaKB API"] = "MetaKB API"
    version: str = __version__


class SpecMetadata(BaseModel):
    """Define substructure for reporting specification metadata."""

    vrs_version: str = VRS_VERSION


class ImplMetadata(BaseModel):
    """Define substructure for reporting metadata about internal software dependencies."""

    vrs_python_version: str = vrs_python_version


METAKB_DESCRIPTION = "A search interface for cancer variant interpretations assembled by aggregating and harmonizing across multiple cancer variant interpretation knowledgebases."


class ServiceInfo(BaseModel):
    """Define response structure for GA4GH /service_info endpoint."""

    id: Literal["org.cancervariants.metakb"] = "org.cancervariants.metakb"
    name: Literal["metakb"] = "metakb"
    type: ServiceType
    description: str = METAKB_DESCRIPTION
    organization: ServiceOrganization
    contactUrl: Literal["Alex.Wagner@nationwidechildrens.org"] = (
        "Alex.Wagner@nationwidechildrens.org"
    )
    documentationUrl: Literal["https://github.com/cancervariants/metakb"] = (
        "https://github.com/cancervariants/metakb"
    )
    createdAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"
    updatedAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"
    environment: ServiceEnvironment
    version: str = __version__
    spec_metadata: SpecMetadata = SpecMetadata()
    impl_metadata: ImplMetadata = ImplMetadata()


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
