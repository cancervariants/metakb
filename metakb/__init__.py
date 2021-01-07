"""The MetaKB package."""
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logging.basicConfig(
    filename='metakb.log',
    format='[%(asctime)s] %(levelname)s : %(message)s')
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)
