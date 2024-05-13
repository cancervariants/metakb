"""Main application for FastAPI."""
from typing import Dict, Optional

from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi

from metakb.query import QueryHandler
from metakb.version import __version__

app = FastAPI(
    docs_url="/api/v2",
    openapi_url="/api/v2/openapi.json",
    swagger_ui_parameters={"tryItOutEnabled": True},
)
query = QueryHandler()


def custom_openapi() -> Dict:
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
    variation: Optional[str] = Query(None, description=v_description),
    disease: Optional[str] = Query(None, description=d_description),
    therapy: Optional[str] = Query(None, description=t_description),
    gene: Optional[str] = Query(None, description=g_description),
    study_id: Optional[str] = Query(None, description=s_description),
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
