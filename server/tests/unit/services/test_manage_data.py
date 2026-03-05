import json
from pathlib import Path

import pytest
from ga4gh.va_spec.base import Statement

from metakb.services.manage_data import is_loadable_assertion


@pytest.fixture(scope="session")
def statements(test_data_dir: Path):
    with (test_data_dir / "services" / "loadable_statements_input.json").open() as f:
        data = json.load(f)
    return {k: Statement(**v) for k, v in data.items()}


@pytest.mark.ci_ok
def test_is_loadable_statement(statements: dict[str, Statement]):
    assert is_loadable_assertion(
        statements["metakb.assertion:F-6C4CgAIyw3cf2zdxRVOVfe3L1GbHqa"]
    )
    assert not is_loadable_assertion(statements["moa.assertion:1"])
