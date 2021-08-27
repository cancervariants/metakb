"""The MetaKB package."""
from pathlib import Path
import logging
from os import environ

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if 'METAKB_NORM_EB_PROD' in environ:
    environ['VARIATION_NORM_EB_PROD'] = "true"
    environ['GENE_NORM_EB_PROD'] = "true"
    environ['THERAPY_NORM_EB_PROD'] = "true"
    environ['DISEASE_NORM_EB_PROD'] = "true"
    LOG_FN = "/tmp/metakb.log"
else:
    LOG_FN = "metakb.log"

logging.basicConfig(
    filename=LOG_FN,
    format='[%(asctime)s] - %(name)s - %(levelname)s : %(message)s')
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)
