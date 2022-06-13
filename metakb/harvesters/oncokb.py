"""A module for the OncoKB harvester."""
import logging
from typing import Optional

from metakb.harvesters.base import Harvester

logger = logging.getLogger('metakb.harvesters.oncokb')
logger.setLevel(logging.DEBUG)
