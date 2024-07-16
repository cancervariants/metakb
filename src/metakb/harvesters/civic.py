"""A module for the CIViC harvester."""

import logging
from typing import Any

from civicpy import LOCAL_CACHE_PATH
from civicpy import civic as civicpy

from metakb.harvesters.base import Harvester, _HarvestedData

logger = logging.getLogger(__name__)


class CivicHarvestedData(_HarvestedData):
    """Define output for harvested data from CIViC"""

    genes: list[dict]
    evidence: list[dict]
    molecular_profiles: list[dict]
    assertions: list[dict]


class CivicHarvester(Harvester):
    """A class for the CIViC harvester."""

    def __init__(
        self,
        update_cache: bool = False,
        update_from_remote: bool = True,
        local_cache_path: str = LOCAL_CACHE_PATH,
    ) -> None:
        """Initialize CivicHarvester class.

        :param update_cache: ``True`` if civicpy cache should be updated. Note
            this will take several minutes. ``False`` if to use local cache.
        :param update_from_remote: If set to ``True``, civicpy.update_cache will first
            download the remote cache designated by REMOTE_CACHE_URL, store it
            to LOCAL_CACHE_PATH, and then load the downloaded cache into memory.
            This parameter defaults to ``True``.
        :param local_cache_path: A filepath destination for the retrieved remote
            cache. This parameter defaults to LOCAL_CACHE_PATH from civicpy.
        """
        if update_cache:
            civicpy.update_cache(from_remote_cache=update_from_remote)

        civicpy.load_cache(local_cache_path=local_cache_path, on_stale="ignore")

    def harvest(self) -> CivicHarvestedData:
        """Get CIViC evidence, gene, variant, molecular profile, and assertion data

        :return: CIViC evidence items, genes, variants, molecular profiles, and
            assertions
        """
        evidence = self.harvest_evidence()
        genes = self.harvest_genes()
        variants = self.harvest_variants()
        molecular_profiles = self.harvest_molecular_profiles()
        assertions = self.harvest_assertions()
        return CivicHarvestedData(
            evidence=evidence,
            genes=genes,
            variants=variants,
            molecular_profiles=molecular_profiles,
            assertions=assertions,
        )

    def harvest_evidence(self) -> list[dict]:
        """Harvest all CIViC evidence item records.

        :return: A list of all CIViC evidence item records represented as dicts
        """
        evidence_items = civicpy.get_all_evidence()
        return [self._dictify(e) for e in evidence_items]

    def harvest_genes(self) -> list[dict]:
        """Harvest all CIViC gene records.

        :return: A list of all CIViC gene records represented as dicts
        """
        genes = civicpy.get_all_genes()
        return [self._dictify(g) for g in genes]

    def harvest_variants(self) -> list[dict]:
        """Harvest all CIViC variant records.

        :return: A list of all CIViC variant records represented as dicts
        """
        variants = civicpy.get_all_variants()
        return [self._dictify(v) for v in variants]

    def harvest_molecular_profiles(self) -> list[dict]:
        """Harvest all CIViC Molecular Profile records

        :return: A list of all CIViC molecular profile records represented as dicts
        """
        molecular_profiles = civicpy.get_all_molecular_profiles()
        return [self._dictify(mp) for mp in molecular_profiles]

    def harvest_assertions(self) -> list[dict]:
        """Harvest all CIViC assertion records.

        :return: A list of all CIViC assertion records represented as dicts
        """
        assertions = civicpy.get_all_assertions()
        return [self._dictify(a) for a in assertions]

    def _dictify(self, obj: Any) -> dict:  # noqa: ANN401
        """Recursively convert object to dictionary

        :param obj: Object to convert to dict
        :return: object represented as a dictionary
        """
        if obj is None:
            return None

        if isinstance(obj, civicpy.CivicRecord):
            return {
                k: self._dictify(v)
                for k, v in obj.__dict__.items()
                if not k.startswith(("_", "partial"))
            }

        if isinstance(obj, list):
            return [self._dictify(item) for item in obj]

        return obj
