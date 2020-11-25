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
        self.evidence = self.harvest_evidence()


    def harvest_evidence(self):
        civicpy.load_cache(on_stale='ignore')
        evidence_classes = civicpy.get_all_evidence()
        evidence = []

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
                    "clinical_trials": ev.source.clinical_trials
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
                # "lifecycle_actions": ev.lifecycle_actions,
                "gene_id": ev.gene_id
            }
            evidence.append(ev_record)

        with open(f"{self.project_root}/data/civic/evidence.json", 'w+') as f:
            f.write(json.dumps(evidence))
        return evidence


civic = CIViC()
civic.harvest()
