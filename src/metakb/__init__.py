"""The MetaKB package."""
import logging
from os import environ
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[0]
LOG_FN = "/tmp/metakb.log" if "METAKB_NORM_EB_PROD" in environ else "metakb.log"  # noqa: S108

logging.basicConfig(
    filename=LOG_FN, format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s"
)
logger = logging.getLogger("metakb")
logger.setLevel(logging.DEBUG)
logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("python_jsonschema_objects").setLevel(logging.INFO)
logging.getLogger("hgvs.parser").setLevel(logging.INFO)
logging.getLogger("biocommons.seqrepo.seqaliasdb.seqaliasdb").setLevel(logging.INFO)
logging.getLogger("biocommons.seqrepo.fastadir.fastadir").setLevel(logging.INFO)
logging.getLogger("requests_cache.patcher").setLevel(logging.INFO)
logging.getLogger("bioregistry.resource_manager").setLevel(logging.INFO)
logging.getLogger("blib2to3.pgen2.driver").setLevel(logging.INFO)
logging.getLogger("neo4j").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logger.handlers = []

if "METAKB_NORM_EB_PROD" in environ:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


# default date format for all saved data files
DATE_FMT = "%Y%m%d"
