"""Harvest data from cBioPortal studies."""

import logging
import shutil
import tarfile
from pathlib import Path
from typing import NamedTuple

import pandas as pd
from wags_tails.base_source import UnversionedDataSource, get_latest_local_file
from wags_tails.utils.downloads import download_http

from metakb.harvesters.base import FetchMode, Harvester
from metakb.schemas.data import (
    CBioPortalHarvestedData,
    CBioPortalHarvestedStudyData,
    CBioPortalStudyName,
)

_logger = logging.getLogger(__name__)


class CBioPortalStudyDataPaths(NamedTuple):
    """Collect paths to relevant data files for a given study."""

    data_mutations: Path
    data_clinical_patient: Path
    data_clinical_sample: Path
    meta_study: Path


class CBioPortalDataSource(UnversionedDataSource):
    """Provide access to files of interest for a given cBioPortal-hosted study.

    This is rigged a little differently than other wags-tails fetchers because
    we want to be able to a) group a bunch of different studies into one data dir and
    b) pick a specific study to access. Hence, the study name is passed as a kwarg
    to the constructor.

    It'd be nice to merge this back into wags-tails but given divergence from the API
    and the multi-file setup for each source, it'd be tricky.
    """

    _src_name = "cbioportal"
    _filetype = "txt"

    def __init__(
        self, data_dir: Path | None = None, silent: bool = True, **kwargs
    ) -> None:
        """Construct data fetcher instance.

        :param data_dir: direct location to store data files in, if specified.
        :param silent: if True, don't print any info/updates to console
        :keyword study_name: name of study to get
        :raise ValueError: if study_name kwarg not provided.
        """
        study_name = kwargs.get("study_name")
        if not study_name:
            msg = "Study name parameter is required"
            raise ValueError(msg)
        self._study_name: CBioPortalStudyName = study_name
        super().__init__(data_dir, silent)

    def _download_data(self, file_paths: CBioPortalStudyDataPaths) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        def _handle_download(dl_path: Path, outfile_path: Path) -> None:  # noqa: ARG001
            with tarfile.open(dl_path, "r") as tar:
                for orig_name, dest_path in zip(
                    file_paths._fields, file_paths, strict=True
                ):
                    file = tar.extractfile(f"{self._study_name}/{orig_name}.txt")
                    if not file:
                        raise ValueError
                    with dest_path.open("wb") as dst:
                        shutil.copyfileobj(file, dst)

        download_http(
            f"https://datahub.assets.cbioportal.org/{self._study_name.value}.tar.gz",
            file_paths[0].parent,  # not used by handler
            handler=_handle_download,
        )

    def get_latest(  # type: ignore[reportIncompatibleMethodOverride]
        self, from_local: bool = False, force_refresh: bool = False
    ) -> tuple[CBioPortalStudyDataPaths, str]:
        """Get data (unversioned).

        :param from_local: if True, use latest available local file
        :param force_refresh: if True, fetch and return data from remote regardless of
            whether a local copy is present
        :return: Path to location of data, and version value of it
        :raise ValueError: if both ``force_refresh`` and ``from_local`` are True
        """
        if force_refresh and from_local:
            msg = "Cannot set both `force_refresh` and `from_local`"
            raise ValueError(msg)

        # dynamically construct the list of expected file locations
        file_paths = CBioPortalStudyDataPaths(
            *[
                self.data_dir / f"cbioportal_{self._study_name.value}_{name}.txt"
                for name in CBioPortalStudyDataPaths._fields
            ]
        )

        if from_local:
            # check that everything's there
            for file_name in CBioPortalStudyDataPaths._fields:
                get_latest_local_file(self.data_dir, file_name)

            return file_paths, ""

        if not force_refresh:
            if all(p.exists() for p in file_paths):
                return file_paths, ""
            if not all(not p.exists() for p in file_paths):
                _logger.warning(
                    "Existing files, %s, not all available, attempting full download.",
                    file_paths,
                )

        self._download_data(file_paths)
        return file_paths, ""


class CBioPortalHarvester(Harvester):
    """Acquire and restructure cBioPortal study data to prepare for GKS transformation."""

    def harvest(self, fetch_mode: FetchMode = FetchMode.CHECK_STALE) -> Path:
        """Grab data from a source and stash a copy locally, returning the stashed location

        :param fetch_mode: set data caching/fetching behavior.
        :return: Location of performed data harvest
        """
        data = CBioPortalHarvestedData(
            studies=[
                self._harvest_one(study, fetch_mode) for study in CBioPortalStudyName
            ]
        )
        return self.src_data_dir.save_harvested_data(data)

    def _harvest_one(
        self, study: CBioPortalStudyName, fetch_mode: FetchMode
    ) -> CBioPortalHarvestedStudyData:
        """Harvest a single study

        * Acquire data files if they aren't already available locally
        * Copy them into a Pydantic object

        :param study: name of study to harvest
        :param fetch_mode: data fetching behavior setting
        :return: variant, sample, and patient data for a single study
        """
        from_local, force_refresh = False, False
        if fetch_mode == FetchMode.FORCE_REFRESH:
            force_refresh = True
        elif fetch_mode == FetchMode.USE_LOCAL:
            from_local = True
        files, _ = CBioPortalDataSource(study_name=study).get_latest(
            from_local, force_refresh
        )
        # some study variant files have fewer header rows that need to be skipped
        variant_skiprow_studies = {
            CBioPortalStudyName.PANCAN_MAPPYACTS_2022,
            CBioPortalStudyName.CHL_SCCC_2023,
        }
        variant_skiprows = 2 if study in variant_skiprow_studies else 0

        variants = pd.read_csv(
            files.data_mutations,
            sep="\t",
            comment="#",
            skiprows=variant_skiprows,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        patients = pd.read_csv(
            files.data_clinical_patient,
            sep="\t",
            # skiprows=4,
            comment="#",
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        samples = pd.read_csv(
            files.data_clinical_sample,
            sep="\t",
            comment="#",
            # skiprows=4,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        metadata = pd.read_csv(
            files.meta_study,
            sep="\t",
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        return CBioPortalHarvestedStudyData(
            study_name=study,
            variants=variants,
            patients=patients,
            samples=samples,
            metadata=metadata,
        )
