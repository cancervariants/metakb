"""Main application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from metakb import __version__
from metakb.config import get_config
from metakb.normalizers import ViccNormalizers
from metakb.repository.base import AbstractRepository, RepositoryStats
from metakb.repository.neo4j_repository import (
    get_driver,
)
from metakb.restapi.dependencies import get_repository
from metakb.restapi.search import api_router as search_router
from metakb.schemas.api import (
    METAKB_DESCRIPTION,
    ServiceInfo,
    ServiceOrganization,
    ServiceType,
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


class _Tag(str, Enum):
    """Define tag names for endpoints."""

    META = "Meta"
    SEARCH = "Search"


app.include_router(search_router, tags=[_Tag.SEARCH], prefix=API_PREFIX)


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


@app.get(
    f"{API_PREFIX}/stats",
    summary="Get basic statistics about MetaKB data.",
    tags=[_Tag.META],
)
def stats(
    repository: Annotated[AbstractRepository, Depends(get_repository)],
) -> RepositoryStats:
    """Provide stats for MetaKB data"""
    return repository.get_stats()


origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://metakb-dev-eb.us-east-2.elasticbeanstalk.com/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUILD_DIR = Path(__file__).parent / "build"
try:
    app.mount("/assets", StaticFiles(directory=BUILD_DIR / "assets"), name="assets")
except RuntimeError:
    _logger.warning(
        "Unable to locate static frontend files under path `%s`. Proceeding without defining `get_client()`",
        BUILD_DIR,
    )
    _logger.debug("Build dir contents: %s", BUILD_DIR.rglob("*"))
else:
    templates = Jinja2Templates(directory=BUILD_DIR.as_posix())

    @app.get("/{full_path:path}", include_in_schema=False)
    async def get_client(request: Request, full_path: str):  # noqa: ANN201, ARG001
        """Serve static client files

        This route should be the VERY LAST thing associated with the Fastapi `app` object,
        because it should shadow all unclaimed paths
        """
        return templates.TemplateResponse("index.html", {"request": request})
