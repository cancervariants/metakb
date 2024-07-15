"""Create schemas for API"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr

from metakb.schemas.variation_statement import VariantTherapeuticResponseStudy
from metakb.version import __version__


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


class SearchStudiesQuery(BaseModel):
    """Queries for the Search Studies Endpoint."""

    variation: StrictStr | None = None
    disease: StrictStr | None = None
    therapy: StrictStr | None = None
    gene: StrictStr | None = None
    study_id: StrictStr | None = None


class SearchStudiesService(BaseModel):
    """Define model for Search Studies Endpoint Response."""

    query: SearchStudiesQuery
    warnings: list[StrictStr] = []
    study_ids: list[StrictStr] = []
    studies: list[VariantTherapeuticResponseStudy] = []
    service_meta_: ServiceMeta


class NormalizedQuery(BaseModel):
    """Define structure of user-provided query. If possible, add normalized ID."""

    term: StrictStr
    normalized_id: StrictStr | None = None


class BatchSearchStudiesQuery(BaseModel):
    """Define query as reported in batch search studies endpoint."""

    variations: list[NormalizedQuery] = []


class BatchSearchStudiesService(BaseModel):
    """Define response model for batch search studies endpoint response."""

    query: BatchSearchStudiesQuery
    warnings: list[StrictStr] = []
    study_ids: list[StrictStr] = []
    studies: list[VariantTherapeuticResponseStudy] = []
    service_meta_: ServiceMeta
