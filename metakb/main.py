"""Main application for FastAPI."""
from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi

app = FastAPI(docs_url='api/v2', openapi_url='api/v2/openapi.json')


def custom_openapi():
    """Generate custom fields for OpenAPI response."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="The VICC Meta-Knowledgebase",
        version="2.0",
        description="A search interface for cancer variant interpretations"
                    " assembled by aggregating and harmonizing across multiple"
                    " cancer variant interpretation knowledgebases.",
        routes=app.routes
    )

    openapi_schema['info']['contact'] = {
        "name": "VICC",
        "email": "help@cancervariants.org"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
search_summary = ""
search_response_description = ""
search_description = ""
q_description = ""


@app.get('/api/v2/search',
         summary=search_summary,
         operation_id="getQueryResponse",
         response_desceription=search_response_description,
         # response_model=,
         description=search_description)
def search(q: str = Query(..., description=q_description)):
    """Search endpoint"""
    pass
