"""A module for the OncoKB harvester."""
import logging
from typing import Optional

from metakb.harvesters.base import Harvester

logger = logging.getLogger('metakb.harvesters.oncokb')
logger.setLevel(logging.DEBUG)

class OncoKBHarvester(Harvester):
  """A class for the OncoKB harvester."""
  
  def harvest(self, filename: Optional[str] = None):
      """
        Retrieve and store evidence, gene, variant, and assertion
        records from OncoKB in composite and individual JSON files.
        
        :param Optional[str] filename: File name for composite json
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
      """
      try:
        if not json_created:
                logger.error('OncoKB Harvester was not successful.')
                return False
      except Exception as e:  # noqa: E722
        logger.error(f'OncoKB Harvester was not successful: {e}')
        return False
      else:
        logger.info('OncoKB Harvester was successful.')
        return True
 
