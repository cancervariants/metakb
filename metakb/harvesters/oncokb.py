"""A module for the OncoKB harvester."""
import logging
from typing import Optional
import os
import requests
import requests_cache

from metakb.harvesters.base import Harvester

logger = logging.getLogger('metakb.harvesters.oncokb')
logger.setLevel(logging.DEBUG)

ONCOKB_API_KEY = os.getenv('ONCOKB_API_KEY')
oncokb_api_base_url = "https://www.oncokb.org/api/v1"

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
            civicpy.load_cache(on_stale='ignore')
            evidence = self._harvest_evidence()
            genes = self._harvest_genes()
            variants = self._harvest_variants()
            assertions = self._harvest_assertions()
            self.assertions = assertions
            json_created = self.create_json(
                {
                    "evidence": evidence,
                    "genes": genes,
                    "variants": variants,
                    "assertions": assertions
                },
                filename
            )
            if not json_created:
                logger.error('OncoKB Harvester was not successful.')
                return False
      except Exception as e:  # noqa: E722
        logger.error(f'OncoKB Harvester was not successful: {e}')
        return False
      else:
        logger.info('OncoKB Harvester was successful.')
        return True
 
    def _get_all_genes(self):
        """Return all gene records.
        :return: All OncoKB gene records
        """
        headers = { 'accept': 'application/json',
                    'Authorization':ONCOKB_API_KEY}
        url = oncokb_api_base_url+"/utils/allCuratedGenes?includeEvidence=true"
        with requests_cache.disabled():
            r = requests.get(url=url,headers=headers)
            genes = r.json()

        return genes
    
    def _harvest_genes(self):
        """Harvest all OncoKB gene records.
        :return: A list of all OncoKB gene records.
        """
        genes = self._get_all_genes()
        genes_list = list()
        for gene in genes:
            g = self._harvest_gene(self._get_dict(gene))
            genes_list.append(g)
        return genes_list
    
    def _harvest_gene(self, gene):
        """Harvest an individual OncoKB gene record.
        :param Gene gene: A OncoKB gene object
        :return: A dictionary containing OncoKB gene data
        """
        g = {
            'hugoSymbol': gene['hugoSymbol'],
            'entrezGeneId': gene['entrezGeneId'],
            'summary': gene['summary']
        }
        return g
   
