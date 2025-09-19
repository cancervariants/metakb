"""Main application for FastAPI."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from ga4gh.va_spec.base import (
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)

from metakb import __version__
from metakb.config import get_config
from metakb.query import EmptySearchError, QueryHandler
from metakb.schemas.api import (
    METAKB_DESCRIPTION,
    BatchSearchStatementsResponse,
    SearchStatementsQuery,
    SearchStatementsResponse,
    ServiceInfo,
    ServiceMeta,
    ServiceOrganization,
    ServiceType,
)
from metakb.utils import configure_logs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    configure_logs(logging.DEBUG) if get_config().debug else configure_logs()
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
    """Provide service info per GA4GH Service Info spec"""
    return ServiceInfo(
        organization=ServiceOrganization(),
        type=ServiceType(),
        environment=get_config().env,
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
    start: Annotated[int, Query(description=start_description, ge=0)] = 0,
    limit: Annotated[int | None, Query(description=limit_description, ge=0)] = None,
) -> SearchStatementsResponse:
    """Get nested statements from queried concepts that match all conditions provided.

    For example, if `variation` and `therapy` are provided, will return all statements
    that have both the provided `variation` and `therapy`.
    """
    query: QueryHandler = request.app.state.query
    try:
        search_results = await query.search_statements(
            variation, disease, therapy, gene, statement_id, start, limit
        )
    except EmptySearchError as e:
        raise HTTPException(
            status_code=422,
            detail="At least one search parameter (variation, disease, therapy, gene, statement_id) must be provided.",
        ) from e

    mapped_terms = {term.term_type.value: term for term in search_results.search_terms}

    # group statements
    grouped_statements = {
        "therapeutic_statements": {},
        "diagnostic_statements": {},
        "prognostic_statements": {},
    }
    statement_ids = []
    for statement in search_results.statements:
        statement_ids.append(statement.id)
        variant_id = statement.proposition.subjectVariant.id
        predicate = statement.proposition.predicate
        if isinstance(statement.proposition, VariantTherapeuticResponseProposition):
            key = f"{variant_id}|{statement.proposition.conditionQualifier.root.id}|{statement.proposition.objectTherapeutic.root.id}|{predicate}"
            grouped_statements["therapeutic_statements"].setdefault(key, []).append(
                statement
            )
        elif isinstance(statement.proposition, VariantDiagnosticProposition):
            key = f"{variant_id}|{statement.proposition.objectCondition.root.id}|{predicate}"
            grouped_statements["diagnostic_statements"].setdefault(key, []).append(
                statement
            )
        elif isinstance(statement.proposition, VariantPrognosticProposition):
            key = f"{variant_id}|{statement.proposition.objectCondition.root.id}|{predicate}"
            grouped_statements["prognostic_statements"].setdefault(key, []).append(
                statement
            )
        else:
            msg = f"Unrecognized proposition type `{type(statement.proposition)}` in {statement}"
            raise ValueError(msg)  # noqa: TRY004

    return SearchStatementsResponse(
        query=SearchStatementsQuery(**mapped_terms),
        start=start,
        limit=limit,
        service_meta_=ServiceMeta(),
        statement_ids=statement_ids,
        **grouped_statements,
    )


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
) -> BatchSearchStatementsResponse:
    """Fetch all statements associated with `any` of the provided variations."""
    query = request.app.state.query
    try:
        results = await query.batch_search_statements(variations, start, limit)
    except EmptySearchError as e:
        raise HTTPException(
            status_code=422,
            detail="At least one search parameter must be provided, but no variations values have been given.",
        ) from e
    return BatchSearchStatementsResponse(
        search_terms=results.search_terms,
        start=start,
        limit=limit,
        service_meta_=ServiceMeta(),
        statements=results.statements,
    )
