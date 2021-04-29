"""Main application for FastAPI."""
from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi
from metakb.query import QueryHandler
from metakb.schemas import SearchService, SearchIDService
from typing import Optional

app = FastAPI(docs_url='/api/v2', openapi_url='/api/v2/openapi.json')
query = QueryHandler()


def custom_openapi():
    """Generate custom fields for OpenAPI response."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="The VICC Meta-Knowledgebase",
        version="2.0.0-alpha.1",
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
search_summary = ("Given variation, disease, therapy, and/or gene, "
                  "return associated statements and propositions.")
search_response_description = "A response to a validly-formed query."
search_description = ("Return statements and propositions associated"
                      " to the queried concepts.")
v_description = "Variation (subject) to search"
d_description = "Disease (object qualifier) to search"
t_description = "Therapy (object) to search"
g_description = "Gene to search"
s_description = "Statement ID to search"
detail_description = "Display all descriptors, methods, and documents."


@app.get('/api/v2/search',
         summary=search_summary,
         operation_id="getQueryResponse",
         response_description=search_response_description,
         response_model=SearchService,
         description=search_description,
         response_model_exclude_none=True)
def search(variation: Optional[str] = Query(None, description=v_description),
           disease: Optional[str] = Query(None, description=d_description),
           therapy: Optional[str] = Query(None, description=t_description),
           gene: Optional[str] = Query(None, description=g_description),
           statement_id: Optional[str] = Query(None, description=s_description),  # noqa: E501
           detail: Optional[bool] = Query(False, description=detail_description)  # noqa: E501
           ):
    """Search endpoint"""
    return query.search(variation, disease, therapy, gene, statement_id,
                        detail)


id_query_desc = ("Given Meta-KB statement_id, proposition_id, descriptor_id,"
                 " document_id, or method_id return the node content.")
id_search_description = ("Return node of the queried node id.")
id_description = "Node ID to search"


@app.get('/api/v2/search/{id}',
         summary=id_query_desc,
         operation_id="getIDResponse",
         response_description=search_response_description,
         response_model=SearchIDService,
         description=id_search_description,
         response_model_exclude_none=True)
async def search_by_id(id: str = Query(None, description=id_description)):
    """Search by ID endpoint"""
    return query.search_by_id(id)
