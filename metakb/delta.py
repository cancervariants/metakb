"""A module for computing deltas."""
from metakb import APP_ROOT
import json
import logging
from jsondiff import diff
from datetime import date
from metakb.harvesters import CIViCHarvester, MOAHarvester
HARVESTER_CLASS = {
    'civic': CIViCHarvester,
    'moa': MOAHarvester
}
logger = logging.getLogger('metakb.delta')
logger.setLevel(logging.DEBUG)


class Delta:
    """A class for computing deltas."""

    def __init__(self, main_json, src, *args, **kwargs):
        """Initialize the Delta class.

        :param str main_json: The path to the main composite json file.
        :param str src: The source to compute the delta on
        """
        self._src = src.lower()
        assert self._src in HARVESTER_CLASS.keys()
        self._main_json = main_json
        if '_updated_json' in kwargs:
            # The path to the updated harvester composite json file.
            self._updated_json = kwargs['_updated_json']
        else:
            self._updated_json = None

    def compute_delta(self):
        """Compute delta for store computed delta in a JSON file.

        :return: A dictionary of ids to delete, update, or insert to the main
                 harvester.
        """
        # Main harvester
        with open(self._main_json, 'r') as f:
            main_json = json.load(f)

        current_date = date.today().strftime('%Y%m%d')

        # updated harvester
        if self._updated_json:
            # Updated harvester file already exists
            with open(self._updated_json, 'r') as f:
                updated_json = json.load(f)
        else:
            # Want to create updated harvester file
            fn = f"{self._src}_harvester_{current_date}.json"
            HARVESTER_CLASS[self._src]().harvest(filename=fn)
            with open(f"{APP_ROOT}/data/{self._src}/harvester/{fn}", 'r') as f:
                updated_json = json.load(f)

        delta = {
            '_meta': {
                'metakb_version': '1.0.1',
                'date_harvested': current_date
            }
        }

        if self._src == 'civic':
            delta['_meta']['civicpy_version'] = '1.1.2'
        elif self._src == 'moa':
            delta['_meta']['moa_api_version'] = '0.2'

        for record_type in main_json.keys():
            delta[record_type] = {
                'DELETE': [],
                'INSERT': [],
                'UPDATE': []
            }
            updated = updated_json[record_type]
            main = main_json[record_type]
            updated_ids = self._get_ids(updated)
            main_ids = self._get_ids(main)

            additional_ids = list(set(updated_ids) - set(main_ids))
            self._ins_del_delta(delta, record_type, 'INSERT', additional_ids,
                                updated)
            remove_ids = list(set(main_ids) - set(updated_ids))
            self._ins_del_delta(delta, record_type, 'DELETE', remove_ids,
                                main)

            self._update_delta(delta, record_type, updated, main)

        self._create_json(delta, current_date)
        return delta

    def _ins_del_delta(self, delta, record_type, key, ids_list, data):
        """Store records that will be deleted or inserted.

        :param dict delta: The deltas
        :param str record_type: The type of record
        :param str key: 'INSERT' or 'DELETE'
        :param list ids_list: A list of ids
        :param dict data: Harvester data
        """
        for record in data:
            if record['id'] in ids_list:
                delta[record_type][key].append(record)

    def _update_delta(self, delta, record_type, updated, main):
        """Store deltas.

        :param dict delta: The deltas
        :param str record_type: The type of record
        :param dict updated: updated harvester data
        :param dict main: Main harvester data
        """
        for updated_record in updated:
            for main_record in main:
                if main_record['id'] == updated_record['id']:
                    if updated_record != main_record:
                        delta[record_type]['UPDATE'].append({
                            str(main_record['id']):
                                diff(main_record, updated_record, marshal=True)
                        })
                    break

    def _get_ids(self, records):
        """Return list of ids from data.

        :param dict records: A dictionary of records
        :return: A list of ids
        """
        ids = list()
        for r in records:
            r_id = r['id']
            if r_id not in ids:
                ids.append(r_id)
        return ids

    def _create_json(self, delta, current_date):
        """Create a JSON of deltas.

        :param dict delta: A dictionary containing deltas.
        :param str current_date: The current date
        """
        src_dir = APP_ROOT / 'data' / self._src / 'delta'
        src_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{src_dir}/{self._src}_deltas_{current_date}.json",
                  'w+') as f:
            json.dump(delta, f, indent=4)
