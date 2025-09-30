"""Provide route dependencies"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from neo4j import Driver

from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_repository import Neo4jRepository


def _get_driver(request: Request) -> Driver:
    """Pass driver from app state to dependency function

    Don't bother trying to refactor this. Having a separate sub-function to get something
    from the app state is just a quirk of the FastAPI DI system.

    :param request: fastapi request instance
    :return: neo4j driver
    """
    return request.app.state.driver


def get_repository(
    driver: Annotated[Driver, Depends(_get_driver)],
) -> Generator[AbstractRepository, None, None]:
    """Provide repository factory for REST API route dependency injection

    :param driver: Neo4j driver from fastapi app state
    :return: generator yielding a repository instance. Performs cleanup when route
        invocation concludes.
    """
    session = driver.session()
    repository = Neo4jRepository(session)
    yield repository
    session.close()
