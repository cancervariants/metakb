"""Main application for FastAPI."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request

from metakb import __version__
from metakb.config import config
from metakb.log_handle import configure_logs
from metakb.query import PaginationParamError, QueryHandler
from metakb.schemas.api import (
    METAKB_DESCRIPTION,
    BatchSearchStatementsQuery,
    BatchSearchStatementsService,
    SearchStatementsQuery,
    SearchStatementsService,
    ServiceInfo,
    ServiceMeta,
    ServiceOrganization,
    ServiceType,
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    configure_logs()
    query = QueryHandler()
    app.state.query = query
    yield
    query.driver.close()


app = FastAPI(
    title="The VICC Meta-Knowledgebase",
    description=METAKB_DESCRIPTION,
    version=__version__,
    license={
        "name": "MIT",
        "url": "https://github.com/cancervariants/metakb/blob/main/LICENSE",
    },
    contact={
        "name": "Alex H. Wagner",
        "email": "Alex.Wagner@nationwidechildrens.org",
        "url": "https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab",
    },
    docs_url="/api/v2",
    openapi_url="/api/v2/openapi.json",
    swagger_ui_parameters={"tryItOutEnabled": True},
    lifespan=lifespan,
)


class _Tag(str, Enum):
    """Define tag names for endpoints."""

    META = "Meta"
    SEARCH = "Search"


@app.get(
    "/service-info",
    summary="Get basic service information",
    description="Retrieve service metadata, such as versioning and contact info. Structured in conformance with the [GA4GH service info API specification](https://www.ga4gh.org/product/service-info/)",
    tags=[_Tag.META],
)
def service_info() -> ServiceInfo:
    """Provide service info per GA4GH Service Info spec

    :return: conformant service info description
    """
    return ServiceInfo(
        organization=ServiceOrganization(), type=ServiceType(), environment=config.env
    )


search_stmts_summary = (
    "Get nested statements from queried concepts that match all conditions provided."
)
search_stmts_descr = (
    "Return nested statements that match the intersection of queried concepts. For "
    "example, if `variation` and `therapy` are provided, will return all statements "
    "that have both the provided `variation` and `therapy`."
)
v_description = "Variation (subject) to search. Can be free text or VRS Variation ID."
d_description = "Disease (object qualifier) to search"
t_description = "Therapy (object) to search"
g_description = "Gene to search"
s_description = "Statement ID to search."
start_description = "The index of the first result to return. Use for pagination."
limit_description = "The maximum number of results to return. Use for pagination."


@app.get(
    "/api/v2/search/statements",
    summary=search_stmts_summary,
    response_model=SearchStatementsService,
    response_model_exclude_none=True,
    description=search_stmts_descr,
    tags=[_Tag.SEARCH],
)
async def get_statements(
    request: Request,
    variation: Annotated[str | None, Query(description=v_description)] = None,
    disease: Annotated[str | None, Query(description=d_description)] = None,
    therapy: Annotated[str | None, Query(description=t_description)] = None,
    gene: Annotated[str | None, Query(description=g_description)] = None,
    statement_id: Annotated[str | None, Query(description=s_description)] = None,
    start: Annotated[int, Query(description=start_description)] = 0,
    limit: Annotated[int | None, Query(description=limit_description)] = None,
) -> SearchStatementsService:
    """Get nested statements from queried concepts that match all conditions provided.
    For example, if `variation` and `therapy` are provided, will return all statements
    that have both the provided `variation` and `therapy`.

    :param request: FastAPI request object
    :param variation: Variation query (Free text or VRS Variation ID)
    :param disease: Disease query
    :param therapy: Therapy query
    :param gene: Gene query
    :param statement_id: Statement ID query.
    :param start: The index of the first result to return. Use for pagination.
    :param limit: The maximum number of results to return. Use for pagination.
    :return: SearchStatementsService response containing nested statements and service
        metadata
    """
    query = request.app.state.query
    try:
        resp = await query.search_statements(
            variation, disease, therapy, gene, statement_id, start, limit
        )
    except PaginationParamError:
        resp = SearchStatementsService(
            query=SearchStatementsQuery(
                variation=variation,
                disease=disease,
                therapy=therapy,
                gene=gene,
                statement_id=statement_id,
            ),
            service_meta_=ServiceMeta(),
            warnings=["`start` and `limit` params must both be nonnegative"],
        )
    return resp


_batch_descr = {
    "summary": "Get nested statements for all provided variations.",
    "description": "Return nested statements associated with any of the provided variations.",
    "arg_variations": "Variations (subject) to search. Can be free text or VRS variation ID.",
    "arg_start": "The index of the first result to return. Use for pagination.",
    "arg_limit": "The maximum number of results to return. Use for pagination.",
}


@app.get(
    "/api/v2/batch_search/statements",
    summary=_batch_descr["summary"],
    response_model=BatchSearchStatementsService,
    response_model_exclude_none=True,
    description=_batch_descr["description"],
    tags=[_Tag.SEARCH],
)
async def batch_get_statements(
    request: Request,
    variations: Annotated[
        list[str] | None,
        Query(description=_batch_descr["arg_variations"]),
    ] = None,
    start: Annotated[int, Query(description=_batch_descr["arg_start"])] = 0,
    limit: Annotated[int | None, Query(description=_batch_descr["arg_limit"])] = None,
) -> BatchSearchStatementsService:
    """Fetch all statements associated with `any` of the provided variations.

    :param request: FastAPI request object
    :param variations: variations to match against
    :param start: The index of the first result to return. Use for pagination.
    :param limit: The maximum number of results to return. Use for pagination.
    :return: batch response object
    """
    query = request.app.state.query
    try:
        response = await query.batch_search_statements(variations, start, limit)
    except PaginationParamError:
        response = BatchSearchStatementsService(
            query=BatchSearchStatementsQuery(variations=[]),
            service_meta_=ServiceMeta(),
            warnings=["`start` and `limit` params must both be nonnegative"],
        )

    return response
