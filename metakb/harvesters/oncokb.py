"""Module for harvesting data from OncoKB"""
import logging
import csv
from pathlib import Path
from typing import Dict, List, Union, Optional
from os import environ
from enum import Enum

import requests

from metakb.harvesters.base import Harvester


logger = logging.getLogger("metakb.harvesters.oncokb")
logger.setLevel(logging.DEBUG)


class OncoKBHarvesterException(Exception):
    """OncoKB Harvester Exceptions"""

    pass


class OncoKBLevels(str, Enum):
    """OncoKB levels of evidence names. https://www.oncokb.org/levels"""

    PROGNOSTIC = "prognostic"
    DIAGNOSTIC = "diagnostic"
    RESISTANCE = "resistance"
    SENSITIVE = "sensitive"


class OncoKBHarvester(Harvester):
    """Class for harvesting OncoKB data via REST API"""

    api_url = "https://www.oncokb.org/api/v1"

    def __init__(self, api_token: Optional[str] = None) -> None:
        """Initialize the OncoKB Harvester class.

        :param Optional[str] api_token: API Token to access OncoKB data via its REST
            API. Can also set the api_token via environment variable `ONCOKB_API_TOKEN`.
            See https://www.oncokb.org/apiAccess for more information
        """
        super().__init__()
        self.api_token = api_token or environ.get("ONCOKB_API_TOKEN")
        if not self.api_token:
            raise OncoKBHarvesterException(
                "Access to OncoKB data via REST API requires an api token. You can set "
                "it during initialization (e.g., OncoKBHarvester(api_token={API_TOKEN})). "  # noqa: E501
                "or by setting the `ONCOKB_API_TOKEN` environment variable. For getting"
                " an API token, visit https://www.oncokb.org/apiAccess.")

    def harvest(self, variants_by_protein_change_path: Path,
                filename: Optional[str] = None) -> bool:
        """Retrieve and store gene and variant and its associated evidence from
        OncoKB in composite and individual JSON files.

        :param Path variants_by_protein_change_path: Path to CSV file containing
            header row with `hugo_symbol` and `protein_change` and associated rows
            containing protein variants you wish to harvest using a comma as the
            delimiter
        :param Optional[str] filename: File name for composite JSON
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        harvest_successful = False
        try:
            self.fda_levels = {}
            self.genes = self.harvest_genes()
            self.variants = self.harvest_variants(variants_by_protein_change_path)
            self.metadata = self.get_metadata()
            self.diagnostic_levels = self._get_api_response(f"/levels/{OncoKBLevels.DIAGNOSTIC.value}")  # noqa: E501
            self.prognostic_levels = self._get_api_response(f"/levels/{OncoKBLevels.PROGNOSTIC.value}")  # noqa: E501
            self.resistance_levels = self._get_api_response(f"/levels/{OncoKBLevels.RESISTANCE.value}")  # noqa: E501
            self.sensitive_levels = self._get_api_response(f"/levels/{OncoKBLevels.SENSITIVE.value}")  # noqa: E501

            json_created = self.create_json(
                {
                    "genes": self.genes,
                    "variants": self.variants,
                    "levels": {
                        "diagnostic": self.diagnostic_levels,
                        "prognostic": self.prognostic_levels,
                        "resistance": self.resistance_levels,
                        "sensitive": self.sensitive_levels,
                        "fda": self.fda_levels
                    },
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
        """Get OncoKB metadata. Will update `fda_levels` instance variable.

        :return: OncoKB API metadata if request is successful
        """
        metadata = self._get_api_response("/info") or None
        if metadata:
            for level in metadata["levels"]:
                if "Fda" in level["levelOfEvidence"]:
                    self.fda_levels[level["levelOfEvidence"]] = level["description"]
            del metadata["levels"]
        return metadata

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
            containing protein variants you wish to harvest using a comma as the
            delimiter
        :return: List of variants and their associated evidence items from OncoKB
            if the request is successful
        """
        return self._harvest_protein_change_variants(variants_by_protein_change_path)

    def _harvest_protein_change_variants(
        self, variants_by_protein_change_path: Path
    ) -> List[Dict]:
        """Harvest protein change variants and their associated evidence items from
        OncoKB.

        :param Path variants_by_protein_change_path: Path to CSV file containing
            header row with `hugo_symbol` and `protein_change` and associated rows
            containing protein variants you wish to harvest using a comma as the
            delimiter
        :return: List of protein change variants and their associated evidence items
            from OncoKB if the request is successful
        """
        variants = list()
        with open(variants_by_protein_change_path, "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for symbol, p_change in reader:
                endpoint = f"/annotate/mutations/byProteinChange?hugoSymbol={symbol}&"\
                           f"alteration={p_change}&referenceGenome=GRCh38"
                resp = self._get_api_response(endpoint)
                if resp:
                    variants.append(resp)
        return variants
