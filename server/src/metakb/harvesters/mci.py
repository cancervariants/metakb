"""Fetch NCH Molecular Characterization Initiative (MCI) structured knowledge"""

import json
from pathlib import Path

import requests
from ga4gh.va_spec.base import Statement
from pydantic import BaseModel
from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http

from metakb.harvesters.base import FetchMode, Harvester


class FdaPodaHarvestedData(BaseModel):
    """Hold statements and variants grabbed from FDA PODA data"""

    statements: list[Statement]


class _FdaPodaDataFetcher(DataSource):
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
    """Harvest FDA PODA data"""

    def _get_fda_poda_data(self, fetch_mode: FetchMode) -> dict:
        """Fetch raw data

        :param fetch_mode: behavior for fetching/caching data
        :return: JSON loaded from fetched file
        """
        from_local, force_refresh = False, False
        if fetch_mode == FetchMode.FORCE_REFRESH:
            force_refresh = True
        elif fetch_mode == FetchMode.USE_LOCAL:
            from_local = True
        data, _ = _FdaPodaDataFetcher().get_latest(from_local, force_refresh)
        with data.open() as f:
            return json.load(f)

    def harvest(self, fetch_mode: FetchMode = FetchMode.CHECK_STALE) -> Path:
        """Grab data from a source and stash a copy locally, returning the stashed location

        :param fetch_mode: set data caching/fetching behavior.
        :return: Location of performed data harvest
        """
        source_data = self._get_fda_poda_data(fetch_mode)
        harvested_data = FdaPodaHarvestedData(**source_data)
        return self.src_data_dir.save_harvested_data(harvested_data)
