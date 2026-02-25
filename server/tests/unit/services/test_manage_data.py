import json
from pathlib import Path

import pytest
from ga4gh.va_spec.base import Statement

from metakb.services.manage_data import is_loadable_statement


@pytest.fixture(scope="session")
def statements(test_data_dir: Path):
    with (test_data_dir / "services" / "statements_to_load.json").open() as f:
        data = json.load(f)
    return {k: Statement(**v) for k, v in data.items()}


@pytest.mark.ci_ok
def test_is_loadable_statement(
    civic_aid6_statement: dict, statements: dict[str, Statement]
):
    assert is_loadable_statement(Statement(**civic_aid6_statement))
    assert is_loadable_statement(statements["civic.eid:7157"])
    assert is_loadable_statement(statements["moa.assertion:66"])
    assert is_loadable_statement(statements["moa.assertion:120"])
    assert is_loadable_statement(statements["moa.assertion:166"])

    # variant didn't normalize
    assert not is_loadable_statement(statements["civic.eid:116"])

    # disease didn't normalize
    assert not is_loadable_statement(statements["civic.aid:91"])

    # drug in therapygroup and variant both didn't normalize
    assert not is_loadable_statement(statements["civic.eid:12014"])

    # variant in evidence line didn't normalize
    assert not is_loadable_statement(statements["civic.aid:20"])
