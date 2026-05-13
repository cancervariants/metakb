"""Provide route dependencies"""

from collections.abc import AsyncGenerator

from fastapi import Request

from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_repository import Neo4jRepository


async def get_repository(
    request: Request,
) -> AsyncGenerator[AbstractRepository, None]:
    """Provide repository factory for REST API route dependency injection

    :param request: HTTP request instance provided by FastAPI
    :return: generator yielding a repository instance. Performs cleanup when route
        invocation concludes.
    """
    session = request.app.state.driver.session()
    repository = Neo4jRepository(session)
    try:
        yield repository
    finally:
        await session.close()
