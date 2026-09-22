"""Read and support runtime configuration.

Currently restricted to a subset of overall app configuration.
"""

import logging
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


def _quiet_upstream_libs() -> None:
    """Turn off debug logging for chatty upstream library loggers."""
    for lib in (
        "boto3",
        "botocore",
        "urllib3",
        "hgvs.parser",
        "biocommons.seqrepo.seqaliasdb.seqaliasdb",
        "biocommons.seqrepo.fastadir.fastadir",
        "requests_cache.patcher",
        "blib2to3.pgen2.driver",
        "neo4j",
        "asyncio",
    ):
        logging.getLogger(lib).setLevel(logging.INFO)

    for lib in (
        "botocore.tokens",
        "cool_seq_tool.handlers.seqrepo_access",
        "cool_seq_tool.mappers.mane_transcript",
        "cool_seq_tool.sources.uta_database",
    ):
        logging.getLogger(lib).setLevel(logging.ERROR)


def configure_logs(
    log_level: int = logging.INFO,
    quiet_upstream: bool = True,
    console: bool = False,
) -> None:
    """Configure logging.

    MetaKB is a downstream consumer of a *lot* of different data libraries that produce
    very noisy logs. We don't want to restrict our own downstream users too much, but need
    a way to manage logs in our own production environments, so the entry points that we
    define in the library make use of methods here to set some of our preferred baselines.

    :param log_level: global log level to set
    :param quiet_upstream: if True, turn off debug logging for a selection of libraries
    :param console: if True, emit MetaKB logs to stderr in addition to the log file
    """
    if quiet_upstream:
        _quiet_upstream_libs()
    is_deployed = get_config().env in (
        ServiceEnvironment.PROD,
        ServiceEnvironment.STAGING,
        ServiceEnvironment.DEV,
    )
    log_filename = (
        "/tmp/metakb.log" if is_deployed else "metakb.log"  # noqa: S108
    )
    logging.basicConfig(
        filename=log_filename,
        format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s",
    )
    logger = logging.getLogger("metakb")
    logger.setLevel(log_level)

    if is_deployed and console:
        # The API process writes logs to stderr for its runtime log collector. CLI
        # commands intentionally leave this disabled.
        logger.handlers = []
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
