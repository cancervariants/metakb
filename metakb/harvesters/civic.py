"""A module for the CIViC harvester."""
import requests
import json
from pathlib import Path
from timeit import default_timer as timer


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.civic_api_url = 'https://civicdb.org/api/'

    def harvest(self):
        """Retrieve and store records from CIViC."""
        start = timer()
        self.harvest_type('genes')
        end = timer()
        print(f"Finished Genes in {end - start}s.")

        start = timer()
        self.harvest_type('variants')
        end = timer()
        print(f"Finished Variants in {end - start}s.")

        start = timer()
        self.harvest_type('evidence_items')
        end = timer()
        print(f"Finished Evidence Items in {end - start}s.")

    def harvest_type(self, obj_type):
        main_url = f"{self.civic_api_url}{obj_type}"
        r_json = self._get_json(main_url)
        next_link = r_json['_meta']['links']['next']
        all_links = [main_url]
        records_json = list()

        self._get_links(all_links, next_link)

        for link in all_links:
            r_json = self._get_json(link)
            records = r_json['records']
            for record in records:
                record_url = f"{main_url}/{record['id']}"
                record_obj = self._get_json(record_url)
                records_json.append(record_obj)

        with open(f"{self.project_root}/data/civic/{obj_type}.json", 'w+') as f:
            f.write(json.dumps(records_json))
            f.close()

    def _get_links(self, all_links, next_link):
        while next_link:
            all_links.append(next_link)
            r = requests.get(next_link)
            r_json = r.json()
            next_link = r_json['_meta']['links']['next']

    def _get_json(self, url):
        r = requests.get(url)
        return r.json()


civic = CIViC()
civic.harvest()
