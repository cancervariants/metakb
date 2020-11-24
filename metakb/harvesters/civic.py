"""A module for the CIViC harvester."""
import requests
import json
from pathlib import Path
from timeit import default_timer as timer
from civicpy import civic as civicpy


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        # self.civic_api_url = 'https://civicdb.org/api/'

    def harvest(self):
        self.harvest_evidence()

    def harvest_evidence(self):
        civicpy.load_cache(on_stale='ignore')
        evidence_classes = civicpy.get_all_evidence()
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
                "assertions": [
                    {
                        "id": a.id,
                        "type": a.type,
                        "name": a.name,
                        "summary": a.summary,
                        "description": a.description,
                        "gene": {
                            "name": a.gene.name,
                            "id": a.gene.id
                        },
                        "variant": {
                            "name": a.variant.name,
                            "id": a.variant.id
                        },
                        "disease": a.disease,
                        "drugs": a.drugs,
                        "evidence_type": a.evidence_type,
                        "evidence_direction": a.evidence_direction,
                        "clinical_significance": a.clinical_significance,
                        # "evidence_item_count": a.evidence_item_count,
                        "fda_regulatory_approval": a.fda_regulatory_approval,
                        "status": a.status,
                    } for a in ev.assertions
                ],
                "lifecycle_actions": ev.lifecycle_actions,
                "gene_id": ev.gene_id
            }
            evidence_statements.append(ev_record)

        with open(f"{self.project_root}/data/civic/evidence.json", 'w+') as f:
            f.write(json.dumps(evidence_statements))

    # def harvest(self):
    #     """Retrieve and store records from CIViC."""
    #     start = timer()
    #     self.harvest_type('genes')
    #     end = timer()
    #     print(f"Finished Genes in {end - start}s.")

    #     start = timer()
    #     self.harvest_type('variants')
    #     end = timer()
    #     print(f"Finished Variants in {end - start}s.")

    #     start = timer()
    #     self.harvest_type('evidence_items')
    #     end = timer()
    #     print(f"Finished Evidence Items in {end - start}s.")

    # def harvest_type(self, obj_type):
    #     main_url = f"{self.civic_api_url}{obj_type}"
    #     r_json = self._get_json(main_url)
    #     next_link = r_json['_meta']['links']['next']
    #     all_links = [main_url]
    #     records_json = list()

    #     self._get_links(all_links, next_link)

    #     for link in all_links:
    #         r_json = self._get_json(link)
    #         records = r_json['records']
    #         for record in records:
    #             record_url = f"{main_url}/{record['id']}"
    #             record_obj = self._get_json(record_url)
    #             records_json.append(record_obj)

    #     with open(f"{self.project_root}/data/civic/{obj_type}.json", 'w+') as f:
    #         f.write(json.dumps(records_json))
    #         f.close()

    # def _get_links(self, all_links, next_link):
    #     while next_link:
    #         all_links.append(next_link)
    #         r = requests.get(next_link)
    #         r_json = r.json()
    #         next_link = r_json['_meta']['links']['next']

    # def _get_json(self, url):
    #     r = requests.get(url)
    #     return r.json()


civic = CIViC()
civic.harvest()
