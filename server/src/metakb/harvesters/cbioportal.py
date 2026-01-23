import logging
import os
import tarfile

import pandas as pd
import requests

from metakb.harvesters.base import Harvester, _HarvestedData

# --------------------------
# Config
# --------------------------

STUDIES: list[str] = [
    "pptc_2019",
    "all_phase2_target_2018_pub",
    "rt_target_2018_pub",
    "wt_target_2018_pub",
    "aml_target_2018_pub",
    "nbl_target_2018_pub",
    "pediatric_dkfz_2017",
    "mixed_pipseq_2017",
    "all_stjude_2016",
    "all_stjude_2015",
    "es_dfarber_broad_2014",
    "es_iocurie_2014",
    "mbl_pcgp",
    "pancan_mappyacts_2022",
    "chl_sccc_2023",
]

FILE_PATH = "data/cbioportal"  # where extracted studies go
COMPRESSED_PATH = "compressed_data"  # where .tar.gz files go
FILE_TYPES = [
    "data_mutations",
    "data_clinical_patient",
    "data_clinical_sample",
    "meta_study",
]

logger = logging.getLogger(__name__)
SPECIAL_VARIANT_SKIPROWS = {"pancan_mappyacts_2022", "chl_sccc_2023"}


# --------------------------
# Helpers
# --------------------------


def _download_and_extract_one(study: str) -> None:
    """Download one study tarball into compressed_data/ and extract into data/cbioportal/."""
    os.makedirs(FILE_PATH, exist_ok=True)
    os.makedirs(COMPRESSED_PATH, exist_ok=True)

    # url = f"https://cbioportal-datahub.s3.amazonaws.com/{study}.tar.gz"
    url = f"https://datahub.assets.cbioportal.org/{study}.tar.gz"
    out = os.path.join(COMPRESSED_PATH, f"{study}.tar.gz")

    r = requests.get(
        url, stream=True, timeout=60, headers={"User-Agent": "python-requests"}
    )
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise

    with open(out, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

    with tarfile.open(out, mode="r:gz") as tar:
        tar.extractall(path=FILE_PATH)


def _ensure_study_dir(study: str) -> str:
    """Ensure data/cbioportal/<study> exists; download if missing."""
    base = os.path.abspath(FILE_PATH)
    study_dir = os.path.join(base, study)

    if not os.path.isdir(study_dir):
        _download_and_extract_one(study)

        # Recheck and fallback
        if not os.path.isdir(study_dir):
            matches = [d for d in os.listdir(base) if d.startswith(study)]
            if matches:
                study_dir = os.path.join(base, matches[0])

    if not os.path.isdir(study_dir):
        msg = f"Could not locate study directory for '{study}' in {base}"
        raise FileNotFoundError(msg)
    return study_dir


# --------------------------
# Data Model
# --------------------------


class cBioportalHarvestedData(_HarvestedData):
    variants: list[dict]
    patients: list[dict]
    samples: list[dict]
    metadata: list[dict]


# --------------------------
# Harvester
# --------------------------


class cBioportalHarvester(Harvester):
    """Reads cBioPortal study folders under FILE_PATH."""

    def __init__(self, studies: list[str] | None = None):
        self.studies = studies or STUDIES
        self.basepath = FILE_PATH
        os.makedirs(self.basepath, exist_ok=True)

    def _read_one(self, study: str) -> cBioportalHarvestedData:
        study_dir = _ensure_study_dir(study)
        variant_skip = 2 if study in SPECIAL_VARIANT_SKIPROWS else 0

        variants = pd.read_csv(
            os.path.join(study_dir, f"{FILE_TYPES[0]}.txt"),
            sep="\t",
            skiprows=variant_skip,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        patients = pd.read_csv(
            os.path.join(study_dir, f"{FILE_TYPES[1]}.txt"),
            sep="\t",
            skiprows=4,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        samples = pd.read_csv(
            os.path.join(study_dir, f"{FILE_TYPES[2]}.txt"),
            sep="\t",
            skiprows=4,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        metadata = pd.read_csv(
            os.path.join(study_dir, f"{FILE_TYPES[3]}.txt"),
            sep="\t",
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        ).to_dict(orient="records")

        return cBioportalHarvestedData(
            variants=variants, patients=patients, samples=samples, metadata=metadata
        )

    def harvest(
        self, study: str | None = None
    ) -> cBioportalHarvestedData | dict[str, cBioportalHarvestedData]:
        if study is not None:
            return self._read_one(study)
        out: dict[str, cBioportalHarvestedData] = {}
        for s in self.studies:
            out[s] = self._read_one(s)
        return out


# --------------------------
# Optional: bulk pre-download
# --------------------------
if __name__ == "__main__":
    os.makedirs(FILE_PATH, exist_ok=True)
    os.makedirs(COMPRESSED_PATH, exist_ok=True)
    for s in STUDIES:
        _ensure_study_dir(s)

    # def __init__(self, study = STUDY_NAME[0]): # TODO: hard coded for now, eventually for study in STUDY_NAME
    # TODO: Methods to download and gunzip?
    # TODO: Proposed usage: g = cBioportalHarvester(), data_by_study = g.harvest() ---> data_by_study['es_dfarber_broad_2014'] (one harvestedData obj per study, accessible by dictionary)
