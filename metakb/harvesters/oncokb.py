"""Module for harvesting data from OncoKB"""
import logging
import csv
from pathlib import Path
from typing import Dict, List, Union, Optional

import requests

from metakb.harvesters.base import Harvester


logger = logging.getLogger("metakb.harvesters.oncokb")
logger.setLevel(logging.DEBUG)


class OncoKBHarvester(Harvester):
    """Class for OncoKB harvester."""

    api_url = "https://www.oncokb.org/api/v1"

    def __init__(self, api_token: str) -> None:
        """Initialize the OncoKB Harvester class.

        :param str api_token: API Token to access OncoKB data via its REST API
            See https://api.oncokb.org/oncokb-website/api for more information
        """
        super().__init__()
        self.api_token = api_token

    def harvest(self, variants_by_protein_change_path: Path,
                filename: Optional[str] = None) -> bool:
        """Retrieve and store gene and variant and its associated evidence from
        OncoKB in composite and individual JSON files.

        :param Path variants_by_protein_change_path: Path to CSV file containing
            header row with `hugo_symbol` and `protein_change` and associated rows
            containing protein variants you wish to harvest
        :param Optional[str] filename: File name for composite JSON
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        harvest_successful = False
        try:
            self.genes = self.harvest_genes()
            self.variants = self.harvest_variants(variants_by_protein_change_path)
            self.metadata = self.get_metadata()
            json_created = self.create_json(
                {
                    "genes": self.genes,
                    "variants": self.variants,
                    "metadata": self.metadata
                }, filename
            )
            if json_created:
                harvest_successful = True
            else:
                logger.error("OncoKB Harvester was not successful")
        except Exception as e:  # noqa: E722
            logger.error(f"OncoKB Harvester was not successful: {e}")
        return harvest_successful

    def _get_api_response(self, endpoint: str) -> Optional[Union[Dict, List[Dict]]]:
        """Get response from OncoKB endpoint

        :param str endpoint: Endpoint you wish to query, containing query string
            parameters if applicable.
        :return: Response from querying OncoKB endpoint
        """
        resp = None
        url = requests.utils.requote_uri(f"{self.api_url}{endpoint}")
        r = requests.get(url, headers={"Authorization": f"Bearer {self.api_token}"})
        if r.status_code == 200:
            resp = r.json()
        else:
            logger.error(f"{url} returned status_code: {r.status_code}")
        return resp

    def get_metadata(self) -> Optional[Dict]:
        """Get OncoKB metadata

        :return: OncoKB API metadata if request is successful
        """
        return self._get_api_response("/info") or None

    def harvest_genes(self) -> List[Dict]:
        """Harvest all curated genes in OncoKB

        :return: Gene data from OncoKB if request is successful
        """
        return self._get_api_response("/utils/allCuratedGenes") or list()

    def harvest_variants(self, variants_by_protein_change_path: Path) -> List[Dict]:
        """Harvest variants and their associated evidence items from OncoKB. We
        currently only pull from /annotate/mutations/byProteinChange endpoint.

        :param Path variants_by_protein_change_path: Path to CSV file containing
            header row with `hugo_symbol` and `protein_change` and associated rows
            containing protein variants you wish to harvest
        :return: List of variants and their associated evidence items from OncoKB
            if the request is successful
        """
        variants = self._harvest_protein_change_variants(
            variants_by_protein_change_path)
        return variants

    def _harvest_protein_change_variants(
        self, variants_by_protein_change_path: Path
    ) -> List[Dict]:
        """Harvest protein change variants and their associated evidence items from
        OncoKB.

        :param Path variants_by_protein_change_path: Path to CSV file containing
            header row with `hugo_symbol` and `protein_change` and associated rows
            containing protein variants you wish to harvest
        :return: List of protein change variants and their associated evidence items
            from OncoKB if the request is successful
        """
        variants = list()
        with open(variants_by_protein_change_path, "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                symbol, p_change = row
                endpoint = f"/annotate/mutations/byProteinChange?hugoSymbol={symbol}&"\
                           f"alteration={p_change}&referenceGenome=GRCh38"
                resp = self._get_api_response(endpoint)
                if resp:
                    variants.append(resp)
        return variants
