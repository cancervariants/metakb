import json
from pathlib import Path

import pytest
from ga4gh.va_spec.base import Statement


@pytest.fixture(scope="session")
def statements(test_data_dir: Path):
    with (test_data_dir / "services" / "loadable_statements_input.json").open() as f:
        data = json.load(f)
    return {k: Statement(**v) for k, v in data.items()}


def test_load_from_json():
    pass  # TODO
