"""A module for the CIViC harvester."""
import logging
from typing import Dict, List, Optional
from pathlib import Path

from civicpy import civic as civicpy, LOCAL_CACHE_PATH

from metakb.harvesters.base import Harvester  # noqa: I202

logger = logging.getLogger(__name__)


class CIViCHarvester(Harvester):
    """A class for the CIViC harvester."""

    def __init__(
        self,
        update_cache: bool = False,
        update_from_remote: bool = True,
        local_cache_path: Optional[Path] = LOCAL_CACHE_PATH
    ) -> None:
        """Initialize CIViCHarvester class.

        :param update_cache: `True` if civicpy cache should be updated. Note
            this will take several minutes. `False` if to use local cache.
        :param update_from_remote: If set to `True`, civicpy.update_cache will first
            download the remote cache designated by REMOTE_CACHE_URL, store it
            to LOCAL_CACHE_PATH, and then load the downloaded cache into memory.
            This parameter defaults to `True`.
        :param local_cache_path: A filepath destination for the retrieved remote
            cache. This parameter defaults to LOCAL_CACHE_PATH from civicpy.
        """
        if update_cache:
            civicpy.update_cache(from_remote_cache=update_from_remote)

        civicpy.load_cache(local_cache_path=local_cache_path, on_stale="ignore")

        self.genes = []
        self.variants = []
        self.molecular_profiles = []
        self.evidence = []
        self.assertions = []

    def harvest(self, filename: Optional[str] = None) -> bool:
        """Retrieve and store evidence, gene, variant, molecular profile, and assertion
        records from CIViC in composite and individual JSON files.

        :param filename: File name for composite json
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        try:
            self.evidence = self.harvest_evidence()
            self.genes = self.harvest_genes()
            self.variants = self.harvest_variants()
            self.molecular_profiles = self.harvest_molecular_profiles()
            self.assertions = self.harvest_assertions()

            json_created = self.create_json(
                {
                    "evidence": self.evidence,
                    "genes": self.genes,
                    "variants": self.variants,
                    "molecular_profiles": self.molecular_profiles,
                    "assertions": self.assertions
                },
                filename
            )
            if not json_created:
                logger.error(
                    "CIViC Harvester was not successful: JSON files not created."
                )
                return False
        except Exception as e:  # noqa: E722
            logger.error(f"CIViC Harvester was not successful: {e}")
            return False
        else:
            logger.info("CIViC Harvester was successful.")
            return True

    def harvest_evidence(self) -> List[Dict]:
        """Harvest all CIViC evidence item records.

        :return: A list of all CIViC evidence item records represented as dicts
        """
        evidence_items = civicpy.get_all_evidence()
        return [self._dictify(e) for e in evidence_items]

    def harvest_genes(self) -> List[Dict]:
        """Harvest all CIViC gene records.

        :return: A list of all CIViC gene records represented as dicts
        """
        genes = civicpy.get_all_genes()
        return [self._dictify(g) for g in genes]

    def harvest_variants(self) -> List[Dict]:
        """Harvest all CIViC variant records.

        :return: A list of all CIViC variant records represented as dicts
        """
        variants = civicpy.get_all_variants()
        return [self._dictify(v) for v in variants]

    def harvest_molecular_profiles(self) -> List[Dict]:
        """Harvest all CIViC Molecular Profile records

        :return: A list of all CIViC molecular profile records represented as dicts
        """
        molecular_profiles = civicpy.get_all_molecular_profiles()
        return [self._dictify(mp) for mp in molecular_profiles]

    def harvest_assertions(self) -> List[Dict]:
        """Harvest all CIViC assertion records.

        :return: A list of all CIViC assertion records represented as dicts
        """
        assertions = civicpy.get_all_assertions()
        return [self._dictify(a) for a in assertions]

    def _dictify(self, obj: any) -> Dict:
        """Recursively convert object to dictionary

        :param obj: Object to convert to dict
        :return: object represented as a dictionary
        """
        if obj is None:
            return None

        if isinstance(obj, civicpy.CivicRecord):
            return {
                k: self._dictify(v)
                for k, v in obj.__dict__.items() if not k.startswith(("_", "partial"))
            }

        if isinstance(obj, list):
            return [self._dictify(item) for item in obj]

        return obj
