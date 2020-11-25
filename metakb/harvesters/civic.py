"""A module for the CIViC harvester."""
from civicpy import civic
import json
from pathlib import Path


class CIViC:
    """A class for the CIViC harvester."""

    def __init__(self):
        """Initialize CIViC object."""
        self.project_root = Path(__file__).resolve().parents[2]

    def harvest(self):
        """Retrieve and store records from CIViC."""
        genes_list = self.harvest_gene()
        variants_list = self.harvest_variants()
        assertions_list = self.harvest_assertions()
        self._create_composite_json(genes_list, variants_list, assertions_list)

    def _create_composite_json(self, genes_list, variants_list,
                               assertions_list):
        """Create composite json file containing gene,
        evidence, variant, and assertion data.
        """
        composite_dict = {
            'GENES': genes_list,
            'VARIANTS': variants_list,
            'ASSERTIONS': assertions_list
        }

        with open(f'{self.project_root}/data/civic/civic_harvester.json',
                  'w+') as f:
            json.dump(composite_dict, f)

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
                    self._evidence_item(evidence_item)
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
                # TODO: FIX
                'assertions': [
                    self._assertions(assertion)
                    for assertion in variant.assertions
                ],
                'variant_aliases': variant.variant_aliases,
                'hgvs_expressions': variant.hgvs_expressions,
                'clinvar_entries': variant.clinvar_entries,
                # TODO: Add lifecycle_actions
                'allele_registry_id': variant.allele_registry_id,
                # TODO: Add allele_registry_hgvs
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

    def harvest_assertions(self):
        """Harvest assertion data."""
        assertions = civic.get_all_assertions()
        assertions_list = list()

        for assertion in assertions:
            a = {
                'id': assertion.id,
                'type': assertion.type,
                'name': assertion.name,
                'summary': assertion.summary,
                'description': assertion.description,
                'gene': {
                    'name': assertion.gene.name,
                    'id': assertion.gene.id
                },
                'variant': {
                    'name': assertion.variant.name,
                    'id': assertion.variant.id
                },
                'disease': {
                    'id': assertion.disease.id,
                    'name': assertion.disease.name,
                    'display_name': assertion.disease.display_name,
                    'doid': assertion.disease.doid,
                    'url': assertion.disease.url
                },
                'drugs': [
                    {
                        'id': drug.id,
                        'name': drug.name,
                        'ncit_id': drug.ncit_id,
                        'aliases': drug.aliases
                    }
                    for drug in assertion.drugs
                ],
                'evidence_type': assertion.evidence_type,
                'evidence_direction': assertion.evidence_direction,
                'clinical_significance': assertion.clinical_significance,
                # TODO: Add evidence_item_count
                'fda_regulatory_approval': assertion.fda_regulatory_approval,
                'status': assertion.status,
                # TODO: Add open_change_count, pending_evidence_count
                'nccn_guideline': assertion.nccn_guideline,
                'nccn_guideline_version': assertion.nccn_guideline_version,
                'amp_level': assertion.amp_level,
                'evidence_items': [
                    self._evidence_item(evidence_item, is_assertion=True)
                    for evidence_item in assertion.evidence_items
                ],
                'acmg_codes': assertion.acmg_codes,
                'drug_interaction_type': assertion.drug_interaction_type,
                'fda_companion_test': assertion.fda_companion_test,
                'allele_registry_id': assertion.allele_registry_id,
                'phenotypes': assertion.phenotypes,
                'variant_origin': assertion.variant_origin
                # TODO: Add lifecycle_actions
            }
            assertions_list.append(a)
        return assertions_list

    def _evidence_item(self, evidence_item, is_assertion=False):
        e = {
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
            # TODO: Add open_change_count
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
        if is_assertion:
            e['assertions'] = [
                self._assertions(assertion)
                for assertion in evidence_item.assertions
            ]
            # TODO: Add lifecycle_actions, fields_with_pending_changes
            e['gene_id'] = evidence_item.gene_id,
            # TODO: Add state_params

        return e

    def _assertions(self, assertion):
        return {
            'id': assertion.id,
            'type': assertion.type,
            'name': assertion.name,
            'summary': assertion.summary,
            'description': assertion.description,
            'gene': {
                'name': assertion.gene.name,
                'id': assertion.gene.id
            },
            'variant': {
                'name': assertion.variant.name,
                'id': assertion.variant.id
            },
            'disease': {
                'id': assertion.disease.id,
                'name': assertion.disease.name,
                'display_name': assertion.disease.display_name,
                'doid': assertion.disease.doid,
                'url': assertion.disease.url
            },
            'drugs': [
                {
                    'id': drug.id,
                    'name': drug.name,
                    'ncit_id': drug.ncit_id,
                    'aliases': drug.aliases
                }
                for drug in assertion.drugs
            ],
            'evidence_type': assertion.evidence_type,
            'evidence_direction': assertion.evidence_direction,
            'clinical_significance': assertion.clinical_significance,
            # TODO: Add evidence_item_count
            'fda_regulatory_approval':
                assertion.fda_regulatory_approval,
            'status': assertion.status,
            # TODO: Add open_change_count, pending_evidence_count
        }

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


c = CIViC()
c.harvest()
