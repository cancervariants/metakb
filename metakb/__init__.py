"""The MetaKB package."""
from pathlib import Path
import logging
from os import environ

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logging.basicConfig(
    filename='metakb.log',
    format='[%(asctime)s] %(levelname)s : %(message)s')
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


version = "1.0.1"


if 'METAKB_NORM_EB_PROD' in environ:
    environ['VARIANT_NORM_EB_PROD'] = "true"
    environ['GENE_NORM_EB_PROD'] = "true"
    environ['THERAPY_NORM_EB_PROD'] = "true"
    environ['DISEASE_NORM_EB_PROD'] = "true"
