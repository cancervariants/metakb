"""Manage logging configurations.

MetaKB is a downstream consumer of a *lot* of different data libraries that produce
very noisy logs. We don't want to restrict our own downstream users too much, but need
a way to manage logs in our own production environments, so the entry points that we
define in the library make use of methods here to set some of our preferred baselines.
"""
import logging
import os

LOG_FILENAME = (
    "/tmp/metakb.log" if "METAKB_NORM_EB_PROD" in os.environ else "metakb.log"  # noqa: S108
)


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


def configure_logs(quiet_upstream: bool = True) -> None:
    """Configure logging."""
    if quiet_upstream:
        _quiet_upstream_libs()
    logging.basicConfig(
        filename=LOG_FILENAME,
        format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s",
    )
    logger = logging.getLogger("metakb")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # TODO does this turn off all logs?

    if "METAKB_NORM_EB_PROD" in os.environ:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)
