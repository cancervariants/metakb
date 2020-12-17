"""PMKB harvester"""
import logging
from .base import Harvester
from metakb import PROJECT_ROOT, FileDownloadException
import requests
import re
import csv
import json


logger = logging.getLogger('Harvesters')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class PMKB(Harvester):
    """Harvester class for Weill Cornell PMKB"""

    def __init__(self):
        """Set up harvester object"""
        self.assertions = []

    def harvest(self) -> bool:
        """Harvest PMKB source. Retrieve and store genes, variants, and
        interpretations.

        :return: `True` if successful, `False` otherwise.
        :rtype: bool
        """
        self._data_dir = PROJECT_ROOT / 'data' / 'pmkb'
        self._data_dir.mkdir(exist_ok=True, parents=True)
        files = [f for f in self._data_dir.iterdir()
                 if f.name.startswith('PMKB_Interpretations_Complete')]
        if not files:
            self._download_csv()
            files = [f for f in self._data_dir.iterdir()
                     if f.name.startswith('PMKB_Interpretations_Complete')]
        newest_filename = sorted(files, reverse=True)[0]   # get most recent
        infile = open(newest_filename, 'r')
        reader = csv.reader(infile)
        next(reader)  # skip header

        genes = []
        variants = []
        interpretations = []
        for row in reader:
            pass  # TODO

        self._create_json(genes, variants, interpretations)
        logger.info('PMKB Harvester was successful.')
        return True

    def _download_csv(self):
        """Download source data from PMKB server."""
        PMKB_URL = "https://pmkb.weill.cornell.edu/therapies/downloadCSV.csv"
        response = requests.get(PMKB_URL, stream=True)
        if response.status_code == 200:
            fname = ''
            if "Content-Disposition" in response.headers.keys():
                fname = re.findall("filename=(.+)",
                                   response.headers["Content-Disposition"])[0]
                fname = fname.strip('\"')
            else:
                fname = PMKB_URL.split("/")[-1]
            with open(self._data_dir / fname, 'wb') as f:
                f.write(response.content)
        else:
            logger.error(f"PMKB source download failed with status code: {response.status_code}")  # noqa: E501
            raise FileDownloadException("PMKB source download failed")

    def _create_json(self, genes, variants, interpretations):
        """Create composite JSON file containing genes, variants, and
        interpretations, and create individual JSON files for each assertion.

        :param list genes: List of genes
        :param list variants: List of variants
        :param list interpretations: List of interpretations
        """
        composite_dict = {
            'genes': genes,
            'variants': variants,
            'interpretations': interpretations
        }

        data_dir = PROJECT_ROOT / 'data' / 'pmkb'
        with open(data_dir / 'pmkb_harvester.json', 'w+') as f:
            json.dump(composite_dict, f)

        for d in ['genes', 'variants', 'assertions']:
            with open(data_dir / f"{d}.json", 'w+') as f:
                json.dump(composite_dict[d], f)
