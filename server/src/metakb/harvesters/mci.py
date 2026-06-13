"""Fetch NCH Molecular Characterization Initiative (MCI) structured knowledge"""

import json
import re
from pathlib import Path

import requests
from ga4gh.va_spec.aac_2017.models import VariantClinicalSignificanceStatement
from pydantic import BaseModel
from wags_tails.base_source import DataSource
from wags_tails.utils.downloads import HTTPS_REQUEST_TIMEOUT, download_http, handle_zip

from metakb.harvesters.base import FetchMode, Harvester


class MciHarvestedData(BaseModel):
    """Hold statements and variants grabbed from MCI data"""

    statements: list[VariantClinicalSignificanceStatement]


class _MciDataFetcher(DataSource):
    _src_name = "mci"
    _filetype = "json"

    def _get_latest_version(self) -> str:
        response = requests.get(
            "https://api.github.com/repos/GenomicMedLab/mci-knowledge-pilot/releases",
            timeout=HTTPS_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()[0]["tag_name"]

    def _download_data(self, version: str, outfile: Path) -> None:
        """Download data file to specified location.

        :param version: version to acquire
        :param outfile: location and filename for final data file
        """
        releases_response = requests.get(
            "https://api.github.com/repos/GenomicMedLab/mci-knowledge-pilot/releases",
            timeout=HTTPS_REQUEST_TIMEOUT,
        )
        releases_response.raise_for_status()
        assets = next(i for i in releases_response.json() if i["tag_name"] == version)[
            "assets"
        ]
        asset_url = next(
            i["browser_download_url"]
            for i in assets
            if re.match(r"mci-gks.*json\.zip", i["name"])
        )
        download_http(
            asset_url, outfile, handler=handle_zip, tqdm_params=self._tqdm_params
        )


class MciHarvester(Harvester):
    """Harvest MCI data"""

    def _get_mci_data(self, fetch_mode: FetchMode) -> dict:
        """Fetch raw data

        :param fetch_mode: behavior for fetching/caching data
        :return: JSON loaded from fetched file
        """
        from_local, force_refresh = False, False
        if fetch_mode == FetchMode.FORCE_REFRESH:
            force_refresh = True
        elif fetch_mode == FetchMode.USE_LOCAL:
            from_local = True
        data, _ = _MciDataFetcher().get_latest(from_local, force_refresh)
        with data.open() as f:
            return json.load(f)

    def harvest(self, fetch_mode: FetchMode = FetchMode.CHECK_STALE) -> Path:
        """Grab data from a source and stash a copy locally, returning the stashed location

        :param fetch_mode: set data caching/fetching behavior.
        :return: Location of performed data harvest
        """
        source_data = self._get_mci_data(fetch_mode)["statements"][0]
        harvested_data = MciHarvestedData(
            statements=[VariantClinicalSignificanceStatement(**i) for i in source_data]
        )
        return self.src_data_dir.save_harvested_data(harvested_data)
