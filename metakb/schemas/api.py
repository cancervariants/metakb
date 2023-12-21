"""Create schemas for API"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr

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
                "url": "https://github.com/cancervariants/metakb"
            }
        }
    )


class SearchQuery(BaseModel):
    """Queries for the Search Endpoint."""

    variation: Optional[str] = None
    disease: Optional[str] = None
    therapy: Optional[str] = None
    gene: Optional[str] = None
    statement_id: Optional[str] = None
    detail: StrictBool = False


class Matches(BaseModel):
    """Studies that match the queried parameters."""

    study_ids: List[str]


class SearchStudiesService(BaseModel):
    """Define model for Search Endpoint Response."""

    query: SearchQuery
    warnings: List[StrictStr] = []
    matches: Matches
    studies: List = []
    service_meta_: ServiceMeta


class SearchIdService(BaseModel):
    """Define model for Search by ID Endpoint Response."""

    query: StrictStr
    warnings: List[StrictStr] = []
    node: Optional[Dict] = {}
    node_labels: List[StrictStr] = []
