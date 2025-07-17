"""Read and provide runtime configuration.

Currently restricted to a subset of overall app configuration.
"""

import os
from pathlib import Path
from typing import NamedTuple

from wags_tails.utils.storage import get_data_dir

from metakb.schemas.api import ServiceEnvironment


class _Config(NamedTuple):
    """Define config data structure."""

    data_root: Path
    env: ServiceEnvironment


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
    if env_var_env_name := os.environ.get("METAKB_ENV"):
        try:
            env = ServiceEnvironment(env_var_env_name)
        except ValueError as e:
            msg = f"METAKB_ENV must be set to one of {[e.value for e in ServiceEnvironment]}, got {env_var_env_name} instead"
            raise ValueError(msg) from e
    else:
        env = ServiceEnvironment.DEV
    return _Config(data_root=data_root_location, env=env)


config = _get_configs()
