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

if 'METAKB_NORM_EB_PROD' in environ:
    environ['VARIANT_NORM_EB_PROD'] = "true"
    environ['GENE_NORM_EB_PROD'] = "true"
    environ['THERAPY_NORM_EB_PROD'] = "true"
    environ['DISEASE_NORM_EB_PROD'] = "true"


from metakb.schemas import HarvesterSourceName, TransformSourceName  # noqa: E402, E501

# Get harvester source's class name from string
# {'civic': CIViC, 'moa': MOAlmanac}
HARVESTER_SOURCE_CLASS = {s.value.lower(): eval(s.value) for s in HarvesterSourceName.__members__.values()}  # noqa: E501

# Get tranform source's class name from string
# {'civic': CIViCTransform, 'moa': MOAlmanacTransform}
TRANSFORM_SOURCE_CLASS = {s.value.lower(): eval(s.value) for s in TransformSourceName.__members__.values()}  # noqa: E501
