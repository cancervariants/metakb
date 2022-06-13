"""A module to transform OncoKB"""
from typing import Optional, Dict, List, Set
from pathlib import Path
import logging

from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, \
    Extension, Expression, GeneDescriptor, ValueObjectDescriptor

from metakb.transform.base import Transform
import metakb.schemas as schemas


logger = logging.getLogger('metakb.transform.civic')
logger.setLevel(logging.DEBUG)

class OncoKBTransform(Transform):
    """A class for transforming OncoKB to the common data model."""
    
     async def transform(self):
        """Transform OncoKB harvested json to common data model."""
        
