"""Provide miscellaneous helper utilities."""

import logging

from metakb.config import get_config
from metakb.schemas.api import ServiceEnvironment


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


def configure_logs(log_level: int = logging.INFO, quiet_upstream: bool = True) -> None:
    """Configure logging.

    MetaKB is a downstream consumer of a *lot* of different data libraries that produce
    very noisy logs. We don't want to restrict our own downstream users too much, but need
    a way to manage logs in our own production environments, so the entry points that we
    define in the library make use of methods here to set some of our preferred baselines.

    :param log_level: global log level to set
    :param quiet_upstream: if True, turn off debug logging for a selection of libraries
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

    if is_deployed:
        # force debug logging in production server
        logger.handlers = []
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
