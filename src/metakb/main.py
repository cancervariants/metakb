"""Main application for FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi

from metakb import __version__
from metakb.log_handle import configure_logs
from metakb.query import QueryHandler

query = QueryHandler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa: ARG001
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
search_study_response_descr = "A response to a validly-formed query."


@app.get(
    "/api/v2/search/studies",
    summary=search_studies_summary,
    response_description=search_study_response_descr,
    description=search_studies_descr,
)
async def get_studies(
    variation: Annotated[str | None, Query(description=v_description)] = None,
    disease: Annotated[str | None, Query(description=d_description)] = None,
    therapy: Annotated[str | None, Query(description=t_description)] = None,
    gene: Annotated[str | None, Query(description=g_description)] = None,
    study_id: Annotated[str | None, Query(description=s_description)] = None,
) -> dict:
    """Get nested studies from queried concepts that match all conditions provided.
    For example, if `variation` and `therapy` are provided, will return all studies
    that have both the provided `variation` and `therapy`.

    :param variation: Variation query (Free text or VRS Variation ID)
    :param disease: Disease query
    :param therapy: Therapy query
    :param gene: Gene query
    :param study_id: Study ID query.
    :return: SearchStudiesService response containing nested studies and service
        metadata
    """
    resp = await query.search_studies(variation, disease, therapy, gene, study_id)
    return resp.model_dump(exclude_none=True)


_batch_search_studies_descr = {
    "summary": "Get nested studies for all provided variations.",
    "description": "Return nested studies associated with any of the provided variations.",
    "arg_variations": "Variations (subject) to search. Can be free text or VRS variation ID.",
}


@app.get(
    "/api/v2/batch_search/studies",
    summary=_batch_search_studies_descr["summary"],
    description=_batch_search_studies_descr["description"],
)
async def batch_get_studies(
    variations: Annotated[
        list[str] | None,
        Query(description=_batch_search_studies_descr["arg_variations"]),
    ] = None,
) -> dict:
    """Fetch all studies associated with `any` of the provided variations.

    :param variations: variations to match against
    :return: batch response object
    """
    response = await query.batch_search_studies(variations)
    return response.model_dump(exclude_none=True)
