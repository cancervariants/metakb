"""A module for the CIViC harvester."""
from civicpy import civic
import json  # noqa: F401
from pathlib import Path


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        """Initialize CIViC object."""
        self.project_root = Path(__file__).resolve().parents[2]

    def harvest(self):
        """Retrieve and store records from CIViC."""
        # genes_list = self.harvest_gene()  # noqa: F841
        # variants_list = self.harvest_variants()  # noqa: F841

    def harvest_variants(self):
        """Harvest variant data."""
        variants = civic.get_all_variants()
        variants_list = list()

        for variant in variants:
            v = {
                'id': variant.id,
                'entrez_name': variant.entrez_name,
                'entrez_id': variant.entrez_id,
                'name': variant.name,
                'description': variant.description,
                'gene_id': variant.gene_id,
                'type': variant.type,
                'variant_types': [
                    self._variant_types(variant_type)
                    for variant_type in variant.variant_types
                ],
                'civic_actionability_score':
                    variant.civic_actionability_score,
                'coordinates': self._variant_coordinates(variant),
                'evidence_items': [
                    {
                        'id': evidence_item.id,
                        'name': evidence_item.name,
                        'description': evidence_item.description,
                        'disease': {
                            'id': evidence_item.disease.id,
                            'name': evidence_item.disease.name,
                            'display_name':
                                evidence_item.disease.display_name,
                            'doid': evidence_item.disease.doid,
                            'url': evidence_item.disease.url
                        },
                        'drugs': [
                            {
                                'id': drug.id,
                                'name': drug.name,
                                'ncit_id': drug.ncit_id,
                                'aliases': drug.aliases
                            }
                            for drug in evidence_item.drugs
                        ],
                        'rating': evidence_item.rating,
                        'evidence_level': evidence_item.evidence_level,
                        'evidence_type': evidence_item.evidence_type,
                        'clinical_significance':
                            evidence_item.clinical_significance,
                        'evidence_direction':
                            evidence_item.evidence_direction,
                        'variant_origin': evidence_item.variant_origin,
                        'drug_interaction_type':
                            evidence_item.drug_interaction_type,
                        'status': evidence_item.status,
                        # TODO: Add open_change_count ?
                        # 'open_change_count':
                        #     evidence_item.open_change_count,
                        'type': evidence_item.type,
                        'source': {
                            'id': evidence_item.source.id,
                            'name': evidence_item.source.name,
                            'citation': evidence_item.source.citation,
                            'citation_id':
                                evidence_item.source.citation_id,
                            'source_type':
                                evidence_item.source.source_type,
                            'asco_abstract_id':
                                evidence_item.source.asco_abstract_id,
                            'source_url': evidence_item.source.source_url,
                            'open_access':
                                evidence_item.source.open_access,
                            'pmc_id': evidence_item.source.pmc_id,
                            'publication_date':
                                evidence_item.source.publication_date,
                            'journal': evidence_item.source.journal,
                            'full_journal_title':
                                evidence_item.source.full_journal_title,
                            'status': evidence_item.source.status,
                            'is_review': evidence_item.source.is_review,
                            'clinical_trials': [
                                ct
                                for ct in evidence_item.source.clinical_trials
                            ]
                        },
                        'variant_id': evidence_item.variant_id,
                        # TODO: Find variant w phenotypes
                        'phenotypes': []

                    }
                    for evidence_item in variant.evidence_items
                ],
                'variant_groups': [
                    {
                        'id': variant_group.id,
                        'name': variant_group.name,
                        'description': variant_group.description,
                        'variants': [
                            {
                                'id': variant.id,
                                'entrez_name': variant.entrez_name,
                                'entrez_id': variant.entrez_id,
                                'name': variant.name,
                                'gene_id': variant.gene_id,
                                'type': variant.type,
                                'variant_types': [
                                    self._variant_types(variant_type)
                                    for variant_type in variant.variant_types
                                ],
                                'civic_actionability_score':
                                    variant.civic_actionability_score,
                                'coordinates':
                                    self._variant_coordinates(variant)
                            }
                            for variant in variant_group.variants
                        ]
                    }
                    for variant_group in variant.variant_groups
                ],
                'assertions': variant.assertions,
                'variant_aliases': variant.variant_aliases,
                'hgvs_expressions': variant.hgvs_expressions,
                'clinvar_entries': variant.clinvar_entries,
                # TODO: Add lifecycle_actions
                'allele_registry_id': variant.allele_registry_id,
                # TODO: Add allele_registry_hgvs
                # 'allele_registry_hgvs': variant.allele_registry_hgvs

            }
            variants_list.append(v)
        return variants_list

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
                # TODO: Add lifecycle_actions, sources
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

    def _variant_coordinates(self, variant):
        """Return a variant's coordinates."""
        return {
            'chromosome': variant.coordinates.chromosome,
            'start': variant.coordinates.start,
            'stop': variant.coordinates.stop,
            'reference_bases': variant.coordinates.reference_bases,
            'variant_bases': variant.coordinates.variant_bases,
            'representative_transcript':
                variant.coordinates.representative_transcript,
            'chromosome2': variant.coordinates.chromosome2,
            'start2': variant.coordinates.start2,
            'stop2': variant.coordinates.stop2,
            'representative_transcript2':
                variant.coordinates.representative_transcript2,
            'ensembl_version': variant.coordinates.ensembl_version,
            'reference_build': variant.coordinates.reference_build
        }

    def _variant_types(self, variant_type):
        return {
            'id': variant_type.id,
            'name': variant_type.name,
            'display_name': variant_type.display_name,
            'so_id': variant_type.so_id,
            'description': variant_type.description,
            'url': variant_type.url
        }

    def create_json(self, genes_list):
        """Create composite json file containing gene,
        evidence, and variant data.
        """
        pass


c = CIViC()
c.harvest()
