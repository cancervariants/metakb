from metakb.schemas.api import BatchSearchStatementsService, SearchStatementsService


def assert_no_match(response):
    """No match assertions for queried concepts in search_statements."""
    assert response.statements == response.statement_ids == []
    assert len(response.warnings) > 0


def find_and_check_stmt(
    resp: SearchStatementsService | BatchSearchStatementsService,
    expected_stmt: dict,
    assertion_checks: callable,
    should_find_match: bool = True,
):
    """Check that expected statement is or is not in response"""
    if should_find_match:
        assert expected_stmt["id"] in resp.statement_ids
    else:
        assert expected_stmt["id"] not in resp.statement_ids

    actual_stmt = None
    for stmt in resp.statements:
        if stmt.id == expected_stmt["id"]:
            actual_stmt = stmt
            break

    if should_find_match:
        assert (
            actual_stmt
        ), f"Did not find statement ID {expected_stmt['id']} in statements"
        resp_stmts = [actual_stmt.model_dump(exclude_none=True)]
        assertion_checks(resp_stmts, [expected_stmt])
    else:
        assert actual_stmt is None
