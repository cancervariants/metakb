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

    def harvest(self):
        """Retrieve and store records from CIViC."""
        self.harvest_gene()

    def harvest_gene(self):
        """Harvest gene information."""
        start = timer()
        self._get_gene_information()
        end = timer()
        print(end-start)
        return True

    def _get_gene_information(self):
        r = requests.get(self.genes_url)
        r_json = r.json()
        next_link = r_json['_meta']['links']['next']
        all_links = [self.genes_url]
        records_json = list()

        while next_link:
            all_links.append(next_link)
            r = requests.get(next_link)
            r_json = r.json()
            next_link = r_json['_meta']['links']['next']

        for link in all_links:
            r = requests.get(link)
            r_json = r.json()
            records = r_json['records']
            for record in records:
                gene_url = f"{self.genes_url}/{record['name']}" \
                           f"?identifier_type=entrez_symbol"
                r = requests.get(gene_url)
                gene = r.json()

                records_json.append({
                    'id': gene['id'],
                    'name': gene['name'],
                    'entrez_id': gene['entrez_id'],
                    'description': gene['description'],
                    'variants': gene['variants'],
                    'aliases': gene['aliases'],
                    'type': gene['type'],
                    'lifecycle_actions': gene['lifecycle_actions'],
                    'sources': gene['sources'],
                    'provisional_values': gene['provisional_values'],
                    'errors': gene['errors']
                })

        with open(f"{self.project_root}/data/civic/gene.json", 'w+') as f:
            f.write(json.dumps(records_json))
            f.close()


civic = CIViC()
civic.harvest()
