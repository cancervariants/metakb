"""Create schemas for API"""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, StrictStr

from metakb.schemas.variation_statement import VariantTherapeuticResponseStudy
from metakb.version import __version__


class ServiceMeta(BaseModel):
    """Metadata for MetaKB service."""

    name: Literal["metakb"] = "metakb"
    version: StrictStr = __version__
    url: Literal[
        "https://github.com/cancervariants/metakb"
    ] = "https://github.com/cancervariants/metakb"

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

    variation: Optional[StrictStr] = None
    disease: Optional[StrictStr] = None
    therapy: Optional[StrictStr] = None
    gene: Optional[StrictStr] = None
    study_id: Optional[StrictStr] = None


class SearchStudiesService(BaseModel):
    """Define model for Search Studies Endpoint Response."""

    query: SearchStudiesQuery
    warnings: List[StrictStr] = []
    study_ids: List[StrictStr] = []
    studies: List[VariantTherapeuticResponseStudy] = []
    service_meta_: ServiceMeta
