"""Main application for FastAPI."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi

from metakb import __version__
from metakb.log_handle import configure_logs
from metakb.query import PaginationParamError, QueryHandler
from metakb.schemas.api import (
    BatchSearchStudiesQuery,
    BatchSearchStudiesService,
    SearchStudiesQuery,
    SearchStudiesService,
    ServiceMeta,
)

query = QueryHandler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    configure_logs()
    yield
    query.driver.close()


app = FastAPI(
    docs_url="/api/v2",
    openapi_url="/api/v2/openapi.json",
    swagger_ui_parameters={"tryItOutEnabled": True},
    lifespan=lifespan,
)


def custom_openapi() -> dict:
    """Generate custom fields for OpenAPI response."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="The VICC Meta-Knowledgebase",
        version=__version__,
        description="A search interface for cancer variant interpretations"
        " assembled by aggregating and harmonizing across multiple"
        " cancer variant interpretation knowledgebases.",
        routes=app.routes,
    )

    openapi_schema["info"]["contact"] = {
        "name": "VICC",
        "email": "help@cancervariants.org",
        "url": "https://cancervariants.org",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
search_studies_summary = (
    "Get nested studies from queried concepts that match all conditions provided."
)
search_studies_descr = (
    "Return nested studies that match the intersection of queried concepts. For "
    "example, if `variation` and `therapy` are provided, will return all studies that "
    "have both the provided `variation` and `therapy`."
)
v_description = "Variation (subject) to search. Can be free text or VRS Variation ID."
d_description = "Disease (object qualifier) to search"
t_description = "Therapy (object) to search"
g_description = "Gene to search"
s_description = "Study ID to search."
start_description = "The index of the first result to return. Use for pagination."
limit_description = "The maximum number of results to return. Use for pagination."


@app.get(
    "/api/v2/search/studies",
    summary=search_studies_summary,
    description=search_studies_descr,
)
async def get_studies(
    variation: Annotated[str | None, Query(description=v_description)] = None,
    disease: Annotated[str | None, Query(description=d_description)] = None,
    therapy: Annotated[str | None, Query(description=t_description)] = None,
    gene: Annotated[str | None, Query(description=g_description)] = None,
    study_id: Annotated[str | None, Query(description=s_description)] = None,
    start: Annotated[int, Query(description=start_description)] = 0,
    limit: Annotated[int | None, Query(description=limit_description)] = None,
) -> dict:
    """Get nested studies from queried concepts that match all conditions provided.
    For example, if `variation` and `therapy` are provided, will return all studies
    that have both the provided `variation` and `therapy`.

    :param variation: Variation query (Free text or VRS Variation ID)
    :param disease: Disease query
    :param therapy: Therapy query
    :param gene: Gene query
    :param study_id: Study ID query.
    :param start: The index of the first result to return. Use for pagination.
    :param limit: The maximum number of results to return. Use for pagination.
    :return: SearchStudiesService response containing nested studies and service
        metadata
    """
    try:
        resp = await query.search_studies(
            variation, disease, therapy, gene, study_id, start, limit
        )
    except PaginationParamError:
        resp = SearchStudiesService(
            query=SearchStudiesQuery(
                variation=variation,
                disease=disease,
                therapy=therapy,
                gene=gene,
                study_id=study_id,
            ),
            service_meta_=ServiceMeta(),
            warnings=["`start` and `limit` params must both be nonnegative"],
        )
    return resp.model_dump(exclude_none=True)


_batch_descr = {
    "summary": "Get nested studies for all provided variations.",
    "description": "Return nested studies associated with any of the provided variations.",
    "arg_variations": "Variations (subject) to search. Can be free text or VRS variation ID.",
    "arg_start": "The index of the first result to return. Use for pagination.",
    "arg_limit": "The maximum number of results to return. Use for pagination.",
}


@app.get(
    "/api/v2/batch_search/studies",
    summary=_batch_descr["summary"],
    description=_batch_descr["description"],
)
async def batch_get_studies(
    variations: Annotated[
        list[str] | None,
        Query(description=_batch_descr["arg_variations"]),
    ] = None,
    start: Annotated[int, Query(description=_batch_descr["arg_start"])] = 0,
    limit: Annotated[int | None, Query(description=_batch_descr["arg_limit"])] = None,
) -> dict:
    """Fetch all studies associated with `any` of the provided variations.

    :param variations: variations to match against
    :param start: The index of the first result to return. Use for pagination.
    :param limit: The maximum number of results to return. Use for pagination.
    :return: batch response object
    """
    try:
        response = await query.batch_search_studies(variations, start, limit)
    except PaginationParamError:
        response = BatchSearchStudiesService(
            query=BatchSearchStudiesQuery(variations=[]),
            service_meta_=ServiceMeta(),
            warnings=["`start` and `limit` params must both be nonnegative"],
        )

    return response.model_dump(exclude_none=True)
