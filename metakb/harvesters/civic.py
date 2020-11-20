"""A module for the CIViC harvester."""
import requests
import json
from pathlib import Path
from timeit import default_timer as timer


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.genes_url = 'https://civicdb.org/api/genes'
        self.variants_url = 'https://civicdb.org/api/variants'

    def harvest(self):
        """Retrieve and store records from CIViC."""
        start = timer()
        #self.harvest_gene()
        self.harvest_type(self.genes_url, 'gene')
        # self.harvest_type(self.variants_url, 'variant')
        end = timer()
        print(end - start)

    def harvest_type(self, main_url, obj_type):
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
