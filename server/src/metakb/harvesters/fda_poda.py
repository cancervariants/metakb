"""Fetch curated FDA pediatric oncology drug approval data.

This class shouldn't need to do much other than grabbing it from the source repo and
stashing it locally.
"""

import json
from pathlib import Path

import requests
from ga4gh.va_spec.base import Statement
from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http

from metakb.harvesters.base import Harvester, _HarvestedData


class FdaPodaHarvestedData(_HarvestedData):
    statements: list[Statement]
    variants: list[dict]


class _FdaPodaData(DataSource):
    _src_name = "fda_poda"
    _filetype = "json"

    def _get_latest_version(self) -> str:
        response = requests.get(
            "https://api.github.com/repos/GenomicMedLab/fda_pediatric_oncology_drug_approvals/releases",
            timeout=HTTPS_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()[0]["tag_name"]

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        url = f"https://github.com/genomicmedlab/fda_pediatric_oncology_drug_approvals/releases/download/{version}/fda_poda.json"
        download_http(url, outfile, tqdm_params=self._tqdm_params)


class FdaPodaHarvester(Harvester):
    def _get_fda_poda_data(self) -> dict:
        data, _ = _FdaPodaData().get_latest()
        with data.open() as f:
            return json.load(f)

    def harvest(self) -> _HarvestedData:
        source_data = self._get_fda_poda_data()
        return FdaPodaHarvestedData(variants=[], **source_data)
