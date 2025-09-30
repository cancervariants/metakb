from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from ga4gh.va_spec.base import (
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)

from metakb.normalizers import ViccNormalizers
from metakb.repository.base import AbstractRepository
from metakb.restapi.dependencies import get_repository
from metakb.schemas.api import (
    BatchSearchStatementsResponse,
    SearchStatementsQuery,
    SearchStatementsResponse,
    ServiceMeta,
)
from metakb.services.search import (
    EmptySearchError,
    batch_search_statements,
    search_statements,
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


api_router = APIRouter()


@api_router.get(
    "/search/statements",
    summary=search_stmts_summary,
    response_model_exclude_none=True,
    description=search_stmts_descr,
)
async def get_statements(
    request: Request,
    repository: Annotated[AbstractRepository, Depends(get_repository)],
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
    start_time = perf_counter()
    normalizer: ViccNormalizers = request.app.state.normalizer
    try:
        search_results = await search_statements(
            repository,
            normalizer,
            variation,
            disease,
            therapy,
            gene,
            statement_id,
            start,
            limit,
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

    end_time = perf_counter()
    return SearchStatementsResponse(
        query=SearchStatementsQuery(**mapped_terms),
        start=start,
        limit=limit,
        service_meta_=ServiceMeta(),
        statement_ids=statement_ids,
        duration_s=end_time - start_time,
        **grouped_statements,
    )


_batch_descr = {
    "summary": "Get nested statements for all provided variations.",
    "description": "Return nested statements associated with any of the provided variations.",
    "arg_variations": "Variations (subject) to search. Can be free text or VRS variation ID.",
    "arg_start": "The index of the first result to return. Use for pagination.",
    "arg_limit": "The maximum number of results to return. Use for pagination.",
}


@api_router.get(
    "/batch_search/statements",
    summary=_batch_descr["summary"],
    response_model_exclude_none=True,
    description=_batch_descr["description"],
)
async def batch_get_statements(
    request: Request,
    repository: Annotated[AbstractRepository, Depends(get_repository)],
    variations: Annotated[
        list[str] | None,
        Query(description=_batch_descr["arg_variations"]),
    ] = None,
    start: Annotated[int, Query(description=_batch_descr["arg_start"])] = 0,
    limit: Annotated[int | None, Query(description=_batch_descr["arg_limit"])] = None,
) -> BatchSearchStatementsResponse:
    """Fetch all statements associated with `any` of the provided variations."""
    start_time = perf_counter()

    normalizer: ViccNormalizers = request.app.state.normalizer
    try:
        results = await batch_search_statements(
            repository, normalizer, variations, start, limit
        )
    except EmptySearchError as e:
        raise HTTPException(
            status_code=422,
            detail="At least one search parameter must be provided, but no variations values have been given.",
        ) from e
    end_time = perf_counter()
    return BatchSearchStatementsResponse(
        search_terms=results.search_terms,
        start=start,
        limit=limit,
        service_meta_=ServiceMeta(),
        statements=results.statements,
        duration_s=end_time - start_time,
    )
