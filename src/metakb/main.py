"""Main application for FastAPI."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi

from metakb.log_handle import configure_logs
from metakb.query import QueryHandler
from metakb.version import __version__

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
    "Return nested studies associated to the queried concepts. For example, if "
    "`variation` and `therapy` are provided, will return all studies that have both "
    "the provided `variation` and `therapy`."
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
    variation: str | None = Query(None, description=v_description),
    disease: str | None = Query(None, description=d_description),
    therapy: str | None = Query(None, description=t_description),
    gene: str | None = Query(None, description=g_description),
    study_id: str | None = Query(None, description=s_description),
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
    variations: list[str] | None = Query(  # noqa: B008
        None, description=_batch_search_studies_descr["arg_variations"]
    ),
) -> dict:
    """Fetch all studies associated with the provided variations.

    :param variations: variations to match against
    :return: batch response object
    """
    response = await query.batch_search_studies(variations)
    return response.model_dump(exclude_none=True)
