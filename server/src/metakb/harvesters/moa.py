"""A module for the Molecular Oncology Almanac harvester"""

import logging

import requests
import requests_cache

from metakb.harvesters.base import Harvester, _HarvestedData

logger = logging.getLogger(__name__)


class MoaHarvestedData(_HarvestedData):
    """Define output for harvested data from MOA"""

    genes: list[str]
    assertions: list[dict]
    sources: list[dict]


class MoaHarvester(Harvester):
    """A class for the Molecular Oncology Almanac harvester."""

    def harvest(self) -> MoaHarvestedData:
        """Get MOAlmanac assertion, source, variant, and gene data

        :return: MOA assertions, sources, variants, and genes
        """
        assertion_resp = self._get_all_assertions()
        sources = self._harvest_sources(assertion_resp)
        variants, variants_list = self.harvest_variants()
        assertions = self.harvest_assertions(assertion_resp, variants_list)
        genes = self._harvest_genes()
        return MoaHarvestedData(
            assertions=assertions, sources=sources, variants=variants, genes=genes
        )

    @staticmethod
    def _harvest_genes() -> list[str]:
        """Harvest all genes from MOAlmanac

        :return: List of MOA gene names
        """
        genes = []
        with requests_cache.disabled():
            r = requests.get("https://moalmanac.org/api/genes", timeout=60)
            if r.status_code == 200:
                genes = r.json()
        return genes

    def _harvest_sources(self, assertion_resp: list[dict]) -> list[dict]:
        """Harvest all MOA sources

        :param List[Dict] assertion_resp: A list of MOA assertion records
        :return: A list of sources
        """
        sources = []

        for assertion in assertion_resp:
            source = assertion["sources"][0]
            s = self._source_item(source)
            if s not in sources:
                sources.append(s)

        return sources

    def harvest_variants(self) -> tuple[list[dict], list[dict]]:
        """Harvest all MOA variants

        :return: A list of variants
        """
        variants_list = self._get_all_variants()
        variants = []

        for variant in variants_list:
            v = self._harvest_variant(variant)
            variants.append(v)

        return variants, variants_list

    def harvest_assertions(
        self, assertion_resp: list[dict], variants_list: list[dict]
    ) -> list[dict]:
        """Harvest all MOA assertions

        :param assertion_resp: A list of MOA assertion records
        :param variants_list: A list of MOA variant records
        :return: A list of assertions
        """
        assertions = []
        for assertion in assertion_resp:
            a = self._harvest_assertion(assertion, variants_list)
            assertions.append(a)

        return assertions

    def _get_all_assertions(self) -> list[dict]:
        """Return all assertion records.

        :return: All moa assertion records
        """
        with requests_cache.disabled():
            r = requests.get("https://moalmanac.org/api/assertions", timeout=60)
            return r.json()

    def _get_all_variants(self) -> list[dict]:
        """Return all variant records

        :return: All moa variant records
        """
        with requests_cache.disabled():
            r = requests.get("https://moalmanac.org/api/features", timeout=60)
            return r.json()

    def _source_item(self, source: dict) -> dict:
        """Harvest an individual MOA source of evidence

        :param source: source record of each assertion record
        :return: a dictionary containing MOA source of evidence data
        """
        return {
            "id": source["source_id"],
            "type": source["source_type"],
            "doi": source["doi"],
            "nct": source["nct"],
            "pmid": source["pmid"],
            "url": source["url"],
            "citation": source["citation"],
        }

    def _harvest_variant(self, variant: dict) -> dict:
        """Harvest an individual MOA variant record.

        :param variant: A MOA variant record
        :return: A dictionary containing MOA variant data
        """
        variant_record = {"id": variant["feature_id"]}

        variant_record.update(dict(variant["attributes"][0].items()))
        variant_record.update(self._get_feature(variant_record))

        return variant_record

    def _harvest_assertion(self, assertion: dict, variants_list: list[dict]) -> dict:
        """Harvest an individual MOA assertion record

        :param assertion: a MOA assertion record
        :param variants_list: a list of MOA variant records
        :return: A dictionary containing MOA assertion data
        """
        assertion_record = {
            "id": assertion["assertion_id"],
            "context": assertion["context"],
            "deprecated": assertion["deprecated"],
            "description": assertion["description"],
            "disease": {
                "name": assertion["disease"],
                "oncotree_code": assertion["oncotree_code"],
                "oncotree_term": assertion["oncotree_term"],
            },
            "therapy": {
                "name": assertion["therapy_name"],
                "type": assertion["therapy_type"],
                "strategy": assertion["therapy_strategy"],
                "resistance": assertion["therapy_resistance"],
                "sensitivity": assertion["therapy_sensitivity"],
            },
            "predictive_implication": assertion["predictive_implication"],
            "favorable_prognosis": assertion["favorable_prognosis"],
            "created_on": assertion["created_on"],
            "last_updated": assertion["last_updated"],
            "submitted_by": assertion["submitted_by"],
            "validated": assertion["validated"],
            "source_id": assertion["sources"][0]["source_id"],
        }

        for v in variants_list:
            if v["attributes"][0] == assertion["features"][0]["attributes"][0]:
                assertion_record.update({"variant": self._harvest_variant(v)})

        return assertion_record

    def _get_feature(self, v: dict) -> dict:
        """Get feature name from the harvested variants

        :param v: harvested MOA variant
        :return: feature name same format as displayed in moalmanac.org
        """
        feature_type = v["feature_type"]
        if feature_type == "rearrangement":
            feature = "{}{}{}".format(
                v["gene1"],
                f"--{v['gene2']}" if v["gene2"] else "",
                f" {v['rearrangement_type']}" if v["rearrangement_type"] else "",
            )
        elif feature_type == "somatic_variant":
            feature = "{}{}{}".format(
                v["gene"],
                f" {v['protein_change']}" if v["protein_change"] else "",
                f" ({v['variant_annotation']})" if v["variant_annotation"] else "",
            )
        elif feature_type == "germline_variant":
            feature = "{}{}".format(
                v["gene"], " (Pathogenic)" if v["pathogenic"] == "1.0" else ""
            )
        elif feature_type == "copy_number":
            feature = "{} {}".format(v["gene"], v["direction"])
        elif feature_type == "microsatellite_stability":
            feature = "{}".format(v.get("status"))
        elif feature_type == "mutational_signature":
            csn = v.get("cosmic_signature_number", "")
            feature = f"COSMIC Signature {csn}"
        elif feature_type == "mutational_burden":
            clss = v["classification"]
            min_mut = v["minimum_mutations"]
            mut_per_mb = v["mutations_per_mb"]
            feature = "{}{}".format(
                clss,
                f" (>= {min_mut} mutations)"
                if min_mut
                else (f" (>= {mut_per_mb} mutations/Mb)" if mut_per_mb else ""),
            )
        elif feature_type == "neoantigen_burden":
            feature = "{}".format(v["classification"])
        elif feature_type == "knockdown" or feature_type == "silencing":
            feature = "{}{}".format(
                v["gene"], f" ({v['technique']})" if v["technique"] else ""
            )
        else:
            feature = "{}".format(v["event"])

        return {"feature": feature.strip()}
