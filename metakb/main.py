"""Main application for FastAPI."""
from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi
from metakb.query import QueryHandler
from typing import Optional

app = FastAPI(docs_url='/api/v2', openapi_url='/api/v2/openapi.json')
query = QueryHandler(uri="bolt://localhost:7687",
                     credentials=("neo4j", "admin"))


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
         response_description=search_response_description,
         # response_model=,
         description=search_description)
def search(variation: Optional[str] = Query(None, description=q_description),
           disease: Optional[str] = Query(None),
           therapy: Optional[str] = Query(None),
           gene: Optional[str] = Query(None)):
    """Search endpoint"""
    return query.search(variation, disease, therapy, gene)
