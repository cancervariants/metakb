"""The MetaKB package."""
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)
