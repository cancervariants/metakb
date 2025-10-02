"""Read and provide runtime configuration.

Currently restricted to a subset of overall app configuration.
"""

from functools import cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from wags_tails.utils.storage import get_data_dir

from metakb.schemas.api import ServiceEnvironment


class Settings(BaseSettings):
    """Create app settings

    This is not a singleton, so every new call to this class will re-compute
    configuration settings, defaults, etc.
    """

    model_config = SettingsConfigDict(
        env_prefix="metakb_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: ServiceEnvironment = ServiceEnvironment.LOCAL
    debug: bool = False
    test: bool = False
    data_dir: Path = Field(default_factory=lambda: get_data_dir() / "metakb")
    db_url: str = "bolt://neo4j:neo4j@localhost:7687"


@cache
def get_config() -> Settings:
    """Get runtime configuration.

    This function is cached, so the config object only gets created/calculated once.

    :return: Settings instance
    """
    return Settings()
