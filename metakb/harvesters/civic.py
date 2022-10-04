"""A module for the CIViC harvester."""
import logging
from typing import Optional

from civicpy import civic as civicpy

from metakb.harvesters.base import Harvester

logger = logging.getLogger('metakb.harvesters.civic')
logger.setLevel(logging.DEBUG)


class CIViCHarvester(Harvester):
    """A class for the CIViC harvester."""

    def harvest(self, filename: Optional[str] = None):
        """Retrieve and store evidence, gene, variant, and assertion
        records from CIViC in composite and individual JSON files.

        :param Optional[str] filename: File name for composite json
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        try:
            civicpy.load_cache(on_stale='ignore')
            evidence = self._harvest_evidence()
            genes = self._harvest_genes()
            variants = self._harvest_variants()
            assertions = self._harvest_assertions()
            self.assertions = assertions
            json_created = self.create_json(
                {
                    "evidence": evidence,
                    "genes": genes,
                    "variants": variants,
                    "assertions": assertions
                },
                filename
            )
            if not json_created:
                logger.error('CIViC Harvester was not successful.')
                return False
        except Exception as e:  # noqa: E722
            logger.error(f'CIViC Harvester was not successful: {e}')
            return False
        else:
            logger.info('CIViC Harvester was successful.')
            return True

    def _get_all_evidence(self):
        """Return all evidence item records.

        :return: All civicpy evidence item records
        """
        return civicpy.get_all_evidence()

    def _harvest_evidence(self):
        """Harvest all CIViC evidence item records.

        :return: A list of all CIViC evidence item records.
        """
        evidence_items = self._get_all_evidence()
        evidence = list()

        for ev in evidence_items:
            ev_record = \
                self._evidence_item(self._get_dict(ev), is_evidence=True)
            evidence.append(ev_record)
        return evidence

    def _get_all_genes(self):
        """Return all gene records.

        :return: All civicpy gene records
        """
        return civicpy.get_all_genes()

    def _harvest_genes(self):
        """Harvest all CIViC gene records.

        :return: A list of all CIViC gene records.
        """
        genes = self._get_all_genes()
        genes_list = list()
        for gene in genes:
            g = self._harvest_gene(self._get_dict(gene))
            genes_list.append(g)
        return genes_list

    def _get_all_variants(self):
        """Return all variant records.

        :return: All civicpy variant records
        """
        return civicpy.get_all_variants()

    def _harvest_variants(self):
        """Harvest all CIViC variant records.

        :return: A list of all CIViC variant records.
        """
        variants = self._get_all_variants()
        variants_list = list()

        for variant in variants:
            v = self._harvest_variant(self._get_dict(variant))
            variants_list.append(v)
        return variants_list

    def _get_all_assertions(self):
        """Return all assertion records.

        :return: All civicpy assertion records
        """
        return civicpy.get_all_assertions()

    def _harvest_assertions(self):
        """Harvest all CIViC assertion records.

        :return: A list of all CIViC assertion records.
        """
        assertions = self._get_all_assertions()
        assertions_list = list()

        for assertion in assertions:
            a = self._harvest_assertion(self._get_dict(assertion))
            assertions_list.append(a)
        return assertions_list

    def _harvest_gene(self, gene):
        """Harvest an individual CIViC gene record.

        :param Gene gene: A CIViC gene object
        :return: A dictionary containing CIViC gene data
        """
        g = {
            'id': gene['id'],
            'name': gene['name'],
            'entrez_id': gene['entrez_id'],
            'description': gene['description'],
            'variants': [
                {
                    'name': self._get_dict(variant)['name'],
                    'id': self._get_dict(variant)['id'],
                    'evidence_items':
                        self._get_dict(variant)['_evidence_items']
                }
                for variant in gene['_variants']
            ],
            'aliases': gene['aliases'],
            # TODO: Add lifecycle_actions, sources
            'type': gene['type']
        }

        for v in g['variants']:
            evidence_items = {
                'accepted_count': 0,
                'rejected_count': 0,
                'submitted_count': 0
            }
            for e in v['evidence_items']:
                e = self._get_dict(e)
                if e['status'] == 'submitted':
                    evidence_items['submitted_count'] += 1
                elif e['status'] == 'rejected':
                    evidence_items['rejected_count'] += 1
                elif e['status'] == 'accepted':
                    evidence_items['accepted_count'] += 1
            v['evidence_items'] = evidence_items

        return g

    def _harvest_variant(self, variant):
        """Harvest an individual CIViC variant record.

        :param Gene variant: A CIViC variant object
        :return: A dictionary containing CIViC variant data
        """
        v = self._variant(variant)

        # Add more attributes to variant data
        v_extra = {
            'evidence_items': [
                self._evidence_item(self._get_dict(evidence_item))
                for evidence_item in variant['_evidence_items']
            ],
            'variant_groups': [
                {
                    'id': self._get_dict(variant_group)['id'],
                    'name': self._get_dict(variant_group)['name'],
                    'description':
                        self._get_dict(variant_group)['description'],
                    'variants': [
                        self._variant(self._get_dict(variant))
                        for variant in self._get_dict(variant_group)[
                            'variants']
                    ],
                    'type': self._get_dict(variant_group)['type']
                }
                for variant_group in variant['variant_groups']
            ],
            'assertions': [
                self._assertion(self._get_dict(assertion))
                for assertion in variant['_assertions']
            ],
            'variant_aliases': variant['variant_aliases'],
            'hgvs_expressions': variant['hgvs_expressions'],
            'clinvar_entries': variant['clinvar_entries'],
            # TODO: Add lifecycle_actions
            'allele_registry_id': variant['allele_registry_id'],
            # TODO: Add allele_registry_hgvs
        }
        v.update(v_extra)
        return v

    def _harvest_assertion(self, assertion):
        """Harvest an individual CIViC assertion record.

        :param Gene assertion: A CIViC variant object
        :return: A dictionary containing CIViC assertion data
        """
        a = self._assertion(assertion)

        # Add more attributes to assertion data
        a_extra = {
            'nccn_guideline': assertion['nccn_guideline'],
            'nccn_guideline_version': assertion['nccn_guideline_version'],
            'amp_level': assertion['amp_level'],
            'evidence_items': [
                self._evidence_item(self._get_dict(evidence_item),
                                    is_assertion=True)
                for evidence_item in assertion['evidence_items']
            ],
            'acmg_codes': assertion['acmg_codes'],
            'drug_interaction_type': assertion['drug_interaction_type'],
            'fda_companion_test': assertion['fda_companion_test'],
            'allele_registry_id': assertion['allele_registry_id'],
            'phenotypes': assertion['phenotypes'],
            'variant_origin': assertion['variant_origin']
            # TODO: Add lifecycle_actions
        }
        a.update(a_extra)
        return a

    def _evidence_item(self, evidence_item,
                       is_evidence=False, is_assertion=False):
        """Get evidence item data.

        :param Evidence evidence_item: A CIViC Evidence record
        :param bool is_evidence: Whether or not the evidence item is
                                 being harvested in an evidence record
        :param bool is_assertion: Whether or not the evidence item is
                                  being harvested in an assertion record
        :return: A dictionary containing evidence item data
        """
        e = {
            'id': evidence_item['id'],
            'name': evidence_item['name'],
            'description': evidence_item['description'],
            'disease': self._disease(self._get_dict(evidence_item)),
            'drugs': [
                self._drug(self._get_dict(drug))
                for drug in evidence_item['drugs']
            ],
            'rating': evidence_item['rating'],
            'evidence_level': evidence_item['evidence_level'],
            'evidence_type': evidence_item['evidence_type'],
            'clinical_significance':
                evidence_item['clinical_significance'],
            'evidence_direction':
                evidence_item['evidence_direction'],
            'variant_origin': evidence_item['variant_origin'],
            'drug_interaction_type':
                evidence_item['drug_interaction_type'],
            'status': evidence_item['status'],
            # TODO: Add open_change_count
            'type': evidence_item['type'],
            'source': self._source(evidence_item),
            'variant_id': evidence_item['variant_id'],
            # TODO: Find variant w phenotypes
            'phenotypes': []
        }

        # Assertions and Evidence Items contain more attributes
        if is_assertion or is_evidence:
            e['assertions'] = [
                self._assertion(self._get_dict(assertion))
                for assertion in evidence_item['_assertions']
            ]
            # TODO: Add lifecycle_actions, fields_with_pending_changes
            e['gene_id'] = evidence_item['gene_id']
            if is_assertion:
                # TODO: Add state_params
                pass

        return e

    def _variant(self, variant):
        """Get basic variant data.

        :param Variant variant: A CIViC Variant record
        :return: A dictionary containing variant data
        """
        return {
            'id': variant['id'],
            'entrez_name': variant['entrez_name'],
            'entrez_id': variant['entrez_id'],
            'name': variant['name'],
            'description': variant['description'],
            'gene_id': variant['gene_id'],
            'type': variant['type'],
            'variant_types': [
                self._variant_types(self._get_dict(variant_type))
                for variant_type in variant['variant_types']
            ],
            'civic_actionability_score':
                int(variant['civic_actionability_score']) if int(variant['civic_actionability_score']) == variant['civic_actionability_score'] else variant['civic_actionability_score'],  # noqa: E501
            'coordinates':
                self._variant_coordinates(variant)
        }

    def _assertion(self, assertion):
        """Get assertion data.

        :param Assertion assertion: A CIViC Assertion record
        :return: A dictionary containing assertion data
        """
        disease = self._get_dict(assertion['disease'])
        return {
            'id': assertion['id'],
            'type': assertion['type'],
            'name': assertion['name'],
            'summary': assertion['summary'],
            'description': assertion['description'],
            'gene': self._gene_name_id(assertion),
            'variant': self._variant_name_id(assertion),
            'disease': {
                'id': disease['id'],
                'name': disease['name'],
                'display_name': disease['display_name'],
                'doid': disease['doid'],
                'url': disease['url']
            },
            'drugs': [
                self._drug(self._get_dict(drug))
                for drug in assertion['drugs']
            ],
            'evidence_type': assertion['evidence_type'],
            'evidence_direction': assertion['evidence_direction'],
            'clinical_significance': assertion['clinical_significance'],
            # TODO: Add evidence_item_count
            'fda_regulatory_approval':
                assertion['fda_regulatory_approval'],
            'status': assertion['status'],
            # TODO: Add open_change_count, pending_evidence_count
        }

    def _variant_coordinates(self, variant):
        """Get a variant's coordinates.

        :param Variant variant: A CIViC variant record
        :return: A dictionary containing a variant's coordinates
        """
        coordinates = self._get_dict(variant['coordinates'])
        return {
            'chromosome': coordinates['chromosome'],
            'start': coordinates['start'],
            'stop': coordinates['stop'],
            'reference_bases': coordinates['reference_bases'],
            'variant_bases': coordinates['variant_bases'],
            'representative_transcript':
                coordinates['representative_transcript'],
            'chromosome2': coordinates['chromosome2'],
            'start2': coordinates['start2'],
            'stop2': coordinates['stop2'],
            'representative_transcript2':
                coordinates['representative_transcript2'],
            'ensembl_version': coordinates['ensembl_version'],
            'reference_build': coordinates['reference_build']
        }

    def _variant_types(self, variant_type):
        """Get variant_type data.

        :param CivicAttribute variant_type: A CIViC variant_type record
        :return: A dictionary containing variant_type data
        """
        return {
            'id': variant_type['id'],
            'name': variant_type['name'],
            'display_name': variant_type['display_name'],
            'so_id': variant_type['so_id'],
            'description': variant_type['description'],
            'url': variant_type['url']
        }

    def _source(self, evidence_item):
        """Get an evidence item's source data.

        :param Evidence evidence_item: A CIViC Evidence record
        :return: A dictionary containing source data
        """
        source = self._get_dict(evidence_item['source'])
        return {
            'id': source['id'],
            'name': source['name'],
            'citation': source['citation'],
            'citation_id': source['citation_id'],
            'source_type': source['source_type'],
            'asco_abstract_id': source['asco_abstract_id'],
            'source_url': source['source_url'],
            'open_access': source['open_access'],
            'pmc_id': source['pmc_id'],
            'publication_date': source['publication_date'],
            'journal': source['journal'],
            'full_journal_title': source['full_journal_title'],
            'status': source['status'],
            'is_review': source['is_review'],
            'clinical_trials': [ct for ct in source['clinical_trials']]
        }

    def _disease(self, evidence_item):
        """Get an evidence item's disease data.
        :param Evidence evidence_item: A CIViC Evidence record
        :return: A dictionary containing disease data
        """
        disease = self._get_dict(evidence_item['disease'])
        if not disease:
            return None
        else:
            return {
                'id': disease['id'],
                'name': disease['name'],
                'display_name': disease['display_name'],
                'doid': disease['doid'],
                'url': disease['url']
            }

    def _drug(self, drug):
        """Get drug data.

        :param Drug drug: A CIViC Drug record
        :return: A dictionary containing drug data.
        """
        drug = self._get_dict(drug)
        return {
            "id": drug['id'],
            "name": drug['name'],
            "ncit_id": drug['ncit_id'],
            "aliases": drug['aliases']
        }

    def _gene_name_id(self, assertion):
        """Get gene name and id.

        :param Assertion assertion: A CIViC Assertion record
        :return: A dictionary containing a gene's name and id
        """
        gene = self._get_dict(assertion['gene'])
        return {
            'name': gene['name'],
            'id': gene['id']
        }

    def _variant_name_id(self, assertion):
        """Get variant name and id.

        :param Assertion assertion: A CIViC Assertion record
        :return: A dictionary containing a variant's name and id
        """
        variant = self._get_dict(assertion['variant'])
        return {
            'name': variant['name'],
            'id': variant['id']
        }

    def _get_dict(self, obj):
        """Return the __dict__ attribute for an object.

        :param obj: The civicpy object
        :return: A dictionary for the object
        """
        if isinstance(obj, (civicpy.Drug, civicpy.Disease,
                            civicpy.CivicAttribute, civicpy.Evidence,
                            civicpy.CivicRecord, civicpy.Gene,
                            civicpy.Assertion, civicpy.Variant)):
            return vars(obj)
        else:
            return obj
