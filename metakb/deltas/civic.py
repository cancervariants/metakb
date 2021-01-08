"""A module for computing CIViC deltas."""
from metakb import PROJECT_ROOT
import json
import logging
from jsondiff import diff
from datetime import date
import pkg_resources
from metakb.harvesters import CIViC

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CIVICDelta:
    """A class for computing CIViC deltas."""

    def __init__(self, main_json, *args, **kwargs):
        """Initialize the CIVICDelta class.

        :param str main_json: The path to the main CIViC composite json file.
        """
        self._main_json = main_json
        if '_new_json' in kwargs:
            self._new_json = kwargs['_new_json']
        else:
            self._new_json = None

    def compute_delta(self):
        """Compute delta for CIViC and store computed delta in a JSON file.

        :return: A dictionary of ids to delete, update, or insert to the main
                 harvester.
        """
        # Main harvester
        with open(self._main_json, 'r') as f:
            main_civic = json.load(f)

        current_date = date.today().strftime('%Y%m%d')

        # New harvester
        if self._new_json:
            with open(self._new_json, 'r') as f:
                new_civic = json.load(f)
        else:
            fn = f"civic_harvester_{current_date}.json"
            c = CIViC()
            c.harvest(fn=fn)

            with open(f"{PROJECT_ROOT}/data/civic/{fn}", 'r') as f:
                new_civic = json.load(f)

        delta = {
            '_meta': {
                'civicpy_version':
                    pkg_resources.get_distribution("civicpy").version,
                # TODO: Might change. Assuming we harvest when computing delta
                'date_harvested': current_date
            }
        }
        civic_records = ['evidence', 'genes', 'variants', 'assertions']

        for civic_record in civic_records:
            delta[civic_record] = {
                'DELETE': [],
                'INSERT': [],
                'UPDATE': []
            }
            new = new_civic[civic_record]
            main = main_civic[civic_record]
            new_ids = self._get_ids(new)
            main_ids = self._get_ids(main)

            additional_ids = list(set(new_ids) - set(main_ids))
            self._ins_del_delta(delta, civic_record, 'INSERT', additional_ids,
                                new)
            remove_ids = list(set(main_ids) - set(new_ids))
            self._ins_del_delta(delta, civic_record, 'DELETE', remove_ids,
                                main)

            self._update_delta(delta, civic_record, new, main)

        self._create_json(delta, current_date)
        return delta

    def _ins_del_delta(self, delta, civic_record, key, ids_list, data):
        """Store records that will be deleted or inserted.

        :param dict delta: The CIViC deltas
        :param str civic_record: The type of CIViC record
        :param str key: 'INSERT' or 'DELETE'
        :param list ids_list: A list of ids
        :param dict data: CIViC harvester data
        """
        for record in data:
            if record['id'] in ids_list:
                delta[civic_record][key].append(record)

    def _update_delta(self, delta, civic_record, new, main):
        """Store CIViC deltas.

        :param dict delta: The CIViC deltas
        :param str civic_record: The type of CIViC record
        :param dict new: New harvester data
        :param dict main: Main harvester data
        """
        for new_record in new:
            for main_record in main:
                if main_record['id'] == new_record['id']:
                    if new_record != main_record:
                        delta[civic_record]['UPDATE'].append({
                            str(main_record['id']):
                                diff(main_record, new_record, marshal=True)
                        })
                    break

    def _get_ids(self, records):
        """Return list of ids from data.

        :param dict records: A dictionary of CIViC records
        :return: A list of ids
        """
        ids = list()
        for r in records:
            r_id = r['id']
            if r_id not in ids:
                ids.append(r_id)
        return ids

    def _create_json(self, delta, current_date):
        """Create a JSON of CIViC deltas.

        :param dict delta: A dictionary containing CIViC deltas.
        :param str current_date: The current date
        """
        civic_dir = PROJECT_ROOT / 'data' / 'civic'
        civic_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{civic_dir}/civic_deltas_{current_date}.json", 'w+') as f:
            json.dump(delta, f)
