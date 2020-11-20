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
        self.evidence_url = 'https://civicdb.org/api/evidence_items'

    def harvest(self):
        """Retrieve and store records from CIViC."""
        self.harvest_gene()
        self.harvest_evidence()

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


    def harvest_evidence(self):
        """Harvest evidence data"""
        start = timer()
        self._get_evidence_information()
        end = timer()
        print(f"Harvested evidence in {start - end}")
        return True


    def _get_evidence_information(self):
        r = requests.get(self.evidence_url)
        r_json = r.json()
        next_link = r_json['_meta']['links']['next']
        all_links = [self.evidence_url]
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
                gene_url = f"{self.evidence_url}/{record['id']}"
                r = requests.get(gene_url)
                gene = r.json()

                records_json.append({
                    'id': evidence['id'],
                    'name': evidence['name'],
                    'description': evidence['description'],
                    'disease': evidence['disease'],
                    'drugs': evidence['drugs'],
                    'rating': evidence['rating'],
                    'evidence_level': evidence['evidence_level'],
                    'evidence_type': evidence['evidence_type'],
                    'clinical_significance': evidence['clinical_significance'],
                    'evidence_direction': evidence['evidence_direction'],
                    'variant_origin': evidence['variant_origin'],
                    'drug_interaction_type': evidence['drug_interaction_type'],
                    'status': evidence['status'],
                    'open_change_count': evidence['open_change_count'],
                    'type': evidence['type'],
                    'source': evidence['source'],
                    'variant_id': evidence['variant_id'],
                    'phenotypes': evidence['phenotypes'],
                    'assertions': evidence['assertions'],
                    'errors': evidence['errors'],
                    'lifecycle_actions': evidence['lifecycle_actions'],
                    'fields_with_pending_changes': evidence['fields_with_pending_changes'],
                    'gene_id': evidence['gene_id']
                })

        with open(f"{self.project_root}/data/civic/evidence.json", 'w+') as f:
            f.write(json.dumps(records_json))
            f.close()


civic = CIViC()
civic.harvest()
