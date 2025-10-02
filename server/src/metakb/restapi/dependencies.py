"""Provide route dependencies"""

from collections.abc import Generator

from fastapi import Request

from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_repository import Neo4jRepository


def get_repository(
    request: Request,
) -> Generator[AbstractRepository, None, None]:
    """Provide repository factory for REST API route dependency injection

    :param driver: Neo4j driver from fastapi app state
    :return: generator yielding a repository instance. Performs cleanup when route
        invocation concludes.
    """
    session = request.app.state.driver.session()
    repository = Neo4jRepository(session)
    yield repository
    session.close()
