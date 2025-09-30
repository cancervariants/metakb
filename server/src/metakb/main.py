"""Main application for FastAPI."""

import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ga4gh.va_spec.base import (
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from starlette.templating import Jinja2Templates
from starlette.templating import _TemplateResponse as TemplateResponse

from metakb import __version__
from metakb.config import get_config
from metakb.normalizers import ViccNormalizers
from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_repository import (
    Neo4jRepository,
    get_driver,
)
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
from metakb.services.search import (
    EmptySearchError,
    batch_search_statements,
    search_statements,
)
from metakb.utils import configure_logs

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    configure_logs(logging.DEBUG) if get_config().debug else configure_logs()
    driver = get_driver()
    app.state.driver = driver
    app.state.normalizer = ViccNormalizers()
    yield
    driver.close()


def get_repository() -> Generator[AbstractRepository, None, None]:
    """Provide repository factory for REST API route dependency injection

    :return: generator yielding a repository instance. Performs cleanup when route
        invocation concludes.
    """
    session = app.state.driver.session()
    repository = Neo4jRepository(session)
    yield repository
    session.close()


API_PREFIX = "/api/v2"


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
    docs_url=API_PREFIX,
    openapi_url="/api/v2/openapi.json",
    swagger_ui_parameters={"tryItOutEnabled": True},
    lifespan=lifespan,
)

# TODO double check that this is necessary
# if it is, write up why
origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BUILD_DIR = Path(__file__).parent / "build"
app.mount("/assets", StaticFiles(directory=BUILD_DIR / "assets"), name="assets")

templates = Jinja2Templates(directory=BUILD_DIR.as_posix())


# def serve_react_app(app: FastAPI) -> FastAPI:
#     """Wrap application initialization in Starlette route param converter. This ensures
#     that the static web client files can be served from the backend.
#
#     Client source must be available at the location specified by `BUILD_DIR` in a
#     production environment. However, this may not be necessary during local development,
#     so the `RuntimeError` is simply caught and logged.
#
#     For the live service, `.ebextensions/01_build.config` includes code to build a
#     production version of the client and move it to the proper location.
#     """
#     try:
#         assets = StaticFiles(directory=BUILD_DIR / "assets")
#     except RuntimeError:
#         _logger.exception(
#             "Unable to access static build files '%s' -- does the folder exist?",
#             BUILD_DIR,
#         )
#     else:
#         app.mount(
#             "/assets/",
#             assets,
#             name="Vite application assets",
#         )
#         templates = Jinja2Templates(directory=BUILD_DIR.as_posix())
#
#         @app.get(f"{API_PREFIX}/{{full_path:path}}", include_in_schema=False)
#         async def serve_react_app(request: Request, full_path: str) -> TemplateResponse:  # noqa: ARG001
#             """Add arbitrary path support to FastAPI service.
#
#             React-router provides something akin to client-side routing based out
#             of the Javascript embedded in index.html. However, FastAPI will intercede
#             and handle all client requests, and will 404 on any non-server-defined paths.
#             This function reroutes those otherwise failed requests against the React-Router
#             client, allowing it to redirect the client to the appropriate location.
#
#             :param request: client request object
#             :param full_path: request path
#             :return: Starlette template response object
#             """
#             return templates.TemplateResponse("index.html", {"request": request})
#
#     return app
#
#
# app = serve_react_app(app)


class _Tag(str, Enum):
    """Define tag names for endpoints."""

    META = "Meta"
    SEARCH = "Search"


@app.get(
    f"{API_PREFIX}/service-info",
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
    f"{API_PREFIX}/search/statements",
    summary=search_stmts_summary,
    response_model_exclude_none=True,
    description=search_stmts_descr,
    tags=[_Tag.SEARCH],
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


@app.get(
    f"{API_PREFIX}/batch_search/statements",
    summary=_batch_descr["summary"],
    response_model_exclude_none=True,
    description=_batch_descr["description"],
    tags=[_Tag.SEARCH],
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


# Catch-all for the SPA (put this LAST so it doesn't shadow others)
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})
