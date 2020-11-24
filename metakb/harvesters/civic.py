"""A module for the CIViC harvester."""
import requests
import json
from pathlib import Path
from timeit import default_timer as timer
from civicpy import civic


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.civic_api_url = 'https://civicdb.org/api/'

    def other_harvest(self):
        civic.load_cache(on_stale='ignore')
        evidence_classes = civic.get_all_evidence()
        evidence_statements = []

        for ev in evidence_classes:
            ev_record = {
                "id": ev.id,
                "name": ev.name,
                "description": ev.description,
                "disease": {
                    "id": ev.disease.id,
                    "name": ev.disease.name,
                    "display_name": ev.disease.display_name,
                    "doid": ev.disease.doid,
                    "url": ev.disease.url
                },
                "drugs": [
                    {"id": drug.id,
                    "name": drug.name,
                    "ncit_id": drug.ncit_id,
                    "aliases": drug.aliases}
                    for drug in ev.drugs
                ],
                "rating": ev.rating,
                "evidence_level": ev.evidence_level,
                "evidence_type": ev.evidence_type,
                "clinical_significance": ev.clinical_significance,
                "evidence_direction": ev.evidence_direction,
                "variant_origin": ev.variant_origin,
                "drug_interaction_type": ev.drug_interaction_type,
                "status": ev.status,
                "type": ev.type,
                "source": {
                    "id": ev.source.id,
                    "name": ev.source.name,
                    "citation": ev.source.citation,
                    "citation_id": ev.source.citation_id,
                    "source_type": ev.source.source_type,
                    "asco_abstract_id": ev.source.asco_abstract_id,
                    "source_url": ev.source.source_url,
                    "open_access": ev.source.open_access,
                    "pmc_id": ev.source.pmc_id,
                    "publication_date": ev.source.publication_date,
                    "journal": ev.source.journal,
                    "full_journal_title": ev.source.full_journal_title,
                    "status": ev.source.status,
                    "is_review": ev.source.is_review,
                    "clinical trials": ev.source.clinical_trials
                },
                "variant_id": ev.variant_id,
                "phenotypes": ev.phenotypes,
                "assertions": ev.assertions,
                "lifecycle_actions": ev.lifecycle_actions,
                "gene_id": ev.gene_id
            }
            evidence_statements.append(ev_record)

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
