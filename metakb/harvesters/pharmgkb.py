"""Harvester for PharmGKB"""
from .base import Harvester
from metakb import PROJECT_ROOT
import logging


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class PharmGKB(Harvester):
    """Class for harvesting from PharmGKB."""

    def harvest(self, fn='pharmgkb_harvester.json',
                data_path=PROJECT_ROOT / 'data' / 'pharmgkb'):
        """Retrieve and store data from PharmGKB resource.

        :param string fn: filename for composite JSON document
        :param Path data_path: path to PharmGKB input data directory
        :return: bool, True if successful and False otherwise
        """
        try:
            self.pharmgkb_dir = data_path
            self._check_files()
            variants = self._get_all_variants()
            annotations = self._get_all_annotations()
            return True
        except Exception as e:  # noqa: E722
            logger.error(f"PharmGKB Harvester was not successful: {e}")
            return False

    def _check_files(self):
        """Check for existence of input data directory and files, and call
        download methods if needed.
        """
        self.pharmgkb_dir.mkdir(exist_ok=True, parents=True)

        ann_files = list(self.pharmgkb_dir.glob('pharmgb_annotations_*.csv'))
        ev_files = list(self.pharmgkb_dir.glob('pharmgkb_evidence_*.csv'))
        alleles_files = list(self.pharmgkb_dir.glob('pharmgkb_alleles_*.csv'))

        if not all(ann_files, ev_files, alleles_files):
            self._download_data()

    def _download_data(self):
        """Retrieve PharmGKB data from remote host."""
        raise NotImplementedError

    def _get_all_variants():
        raise NotImplementedError

    def _get_all_annotations():
        raise NotImplementedError
