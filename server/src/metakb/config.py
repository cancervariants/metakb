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
    db_url: str


def _get_data_root_location() -> Path:
    if env_var_data_dir := os.environ.get("METAKB_DATA_DIR"):
        return Path(env_var_data_dir)
    return get_data_dir() / "metakb"


def _get_env_name() -> ServiceEnvironment:
    if env_var_env_name := os.environ.get("METAKB_ENV"):
        try:
            return ServiceEnvironment(env_var_env_name)
        except ValueError as e:
            msg = f"METAKB_ENV must be set to one of {[e.value for e in ServiceEnvironment]}, got {env_var_env_name} instead"
            raise ValueError(msg) from e
    return ServiceEnvironment.DEV


def _get_db_url() -> str:
    return os.environ.get("METAKB_DB_URL", "bolt://neo4j:neo4j@localhost:7687")


def get_configs() -> _Config:
    """Fetch config values from environment.

    Eventually this may be transformed into something using `pydantic-settings` but for
    now it just assembles a NamedTuple.

    :return: constructed config object
    """
    data_root_location = _get_data_root_location()
    env = _get_env_name()
    db_url = _get_db_url()

    return _Config(data_root=data_root_location, env=env, db_url=db_url)
