"""A module for the CIViC harvester."""
from civicpy import civic
import json
from pathlib import Path
from timeit import default_timer as timer


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]

    def harvest(self):
        """Retrieve and store records from CIViC."""
        genes_list = self.harvest_gene()


    def harvest_gene(self):
        """Harvest gene information."""
        genes = civic.get_all_genes()
        genes_list = list()
        for gene in genes:
            g = {
                'id': gene.id,
                'name': gene.name,
                'entrez_id': gene.entrez_id,
                'description': gene.description,
                'variants': [
                    {
                        'name': variant.name,
                        'id': variant.id,
                        'evidence_items_temp': [
                            e.status for e in variant.evidence_items
                        ]
                    }
                    for variant in gene.variants
                ],
                'aliases': gene.aliases,
                # TODO: Add sources
                'type': gene.type
            }

            # Update evidence_items
            for v in g['variants']:
                evidence_items = {
                    'accepted_count': 0,
                    'rejected_count': 0,
                    'submitted_count': 0
                }
                for e in v['evidence_items_temp']:
                    if e == 'accepted':
                        evidence_items['accepted_count'] = \
                            evidence_items['accepted_count'] + 1
                    elif e == 'submitted':
                        evidence_items['submitted_count'] = \
                            evidence_items['submitted_count'] + 1
                    elif e == 'rejected':
                        evidence_items['rejected_count'] = \
                            evidence_items['rejected_count'] + 1
                del v['evidence_items_temp']
                v['evidence_items'] = evidence_items
            genes_list.append(g)
        return genes_list

    def create_json(self, genes_list):
        """Create comprehensive json file containing gene,
        evidence, and variant data.
        """
        pass


c = CIViC()
c.harvest()
