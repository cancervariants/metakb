"""Read and provide runtime configuration.

Currently restricted to a subset of overall app configuration.
"""

import os
from pathlib import Path
from typing import NamedTuple

from wags_tails.utils.storage import get_data_dir


class _Config(NamedTuple):
    """Define config data structure."""

    data_root: Path


def _get_configs() -> _Config:
    """Fetch config values from environment.

    Eventually this may be transformed into something using `pydantic-settings` but for
    now it just assembles a NamedTuple.

    :return: constructed config object
    """
    if env_var_data_dir := os.environ.get("METAKB_DATA_DIR"):
        data_root_location = Path(env_var_data_dir)
    else:
        data_root_location = get_data_dir() / "metakb"
    return _Config(data_root=data_root_location)


config = _get_configs()
