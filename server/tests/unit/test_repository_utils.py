import pytest
from ga4gh.va_spec.base import Method, Statement

from metakb.repository.base import is_loadable_statement


@pytest.fixture
def civic_aid5_statement(civic_method: Method):
    return Statement()


def test_is_loadable_statement(civic_aid6_statement, civic_aid5_statement: Statement):
    assert is_loadable_statement(Statement(**civic_aid6_statement))
    assert is_loadable_statement(civic_aid5_statement)
