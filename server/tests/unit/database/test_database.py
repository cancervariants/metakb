"""Test basic database functions."""

import pytest
from ga4gh.va_spec.base import Statement

from metakb.repository.neo4j_repository import Neo4jRepository, get_driver


@pytest.fixture
def repository():
    """Provide a new repository session"""
    driver = get_driver()
    session = driver.session()

    repository = Neo4jRepository(session)
    repository.teardown_db()
    repository.initialize()
    yield repository

    session.close()
    driver.close()


@pytest.mark.ci_only
def test_add_statement(repository: Neo4jRepository, civic_eid2997_study_stmt: dict):
    statement = Statement(**civic_eid2997_study_stmt)
    repository.load_statement(statement)

    result = repository.search_statements(statement_ids=["civic.eid:2997"])
    assert len(result) == 1
    assert result[0].id == "civic.eid:2997"
    assert result[0].proposition.subjectVariant.id == "civic.mpid:33"
    assert result[0].proposition.objectTherapeutic.root.id == "civic.tid:146"
    assert result[0].proposition.conditionQualifier.root.id == "civic.did:8"
    assert result[0].proposition.geneContextQualifier.id == "civic.gid:19"
