"""Provide API endpoints for meta-level service information"""

from typing import Annotated

from fastapi import APIRouter, Depends

from metakb.config import get_config
from metakb.repository.base import AbstractRepository, RepositoryStats
from metakb.restapi.dependencies import get_repository
from metakb.schemas.api import ServiceInfo, ServiceOrganization, ServiceType

api_router = APIRouter()


@api_router.get(
    "/service-info",
    summary="Get basic service information",
    description="Retrieve service metadata, such as versioning and contact info. Structured in conformance with the [GA4GH service info API specification](https://www.ga4gh.org/product/service-info/)",
)
def service_info() -> ServiceInfo:
    """Provide service info per GA4GH Service Info spec"""
    return ServiceInfo(
        organization=ServiceOrganization(),
        type=ServiceType(),
        environment=get_config().env,
    )


@api_router.get(
    "/stats",
    summary="Get basic statistics about MetaKB data.",
)
async def stats(
    repository: Annotated[AbstractRepository, Depends(get_repository)],
) -> RepositoryStats:
    """Provide stats for MetaKB data"""
    return await repository.get_stats()
