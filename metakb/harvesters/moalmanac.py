"""A module for the Molecular Oncology Almanac harvester"""

import requests
import requests_cache
import json
import logging


class MOAlamanc:
	"""A class for the Molecular Oncology Almanac harvester."""

	def harvest(self):
		""" 
		Get data from MOA

		:return:'True' if successfully retreived, 'False' otherwise
		:rtype: bool
		 """
		try: 

			assertions = self._harvest_assertions()
			variants = self._harvest_variants()
			genes = self._harvest_genes(variants)
			self._create_json(genes, assertions, variants)
			logging.info('MOAlamanc harvester was successful.')
			return True
		except:
			logging.info('MOAlamanc harvester was not successful.')
			return False

	def _create_json(self, genes, assertions, variants):
		"""
		Create a composite JSON file containing genes, assertions and variants
		and individual JSON files for each MOA record.

		:param: A list of MOA genes
		:param: A list of MOA assertions
		:param: A list of MOA variants
		"""
		composite_dict = {
			'assertions': assertions,
			'genes': genes,
			'variants': variants,
		}

		#with open(f'{PROJECT_ROOT}/data/civic/civic_harvester.json', 'w+') as f:
		with open(f'./data/moa_harvester.json', 'w+') as f:
			json.dump(composite_dict, f)
			f.close()

		data = ['assertions', 'genes', 'variants']
		for d in data:
			#with open(f'{PROJECT_ROOT}/data/civic/{d}.json', 'w+') as f:
			with open(f'./data/{d}.json', 'w+') as f:
				f.write(json.dumps(composite_dict[d]))
				f.close()

	def _harvest_genes(self, variants):
		"""
		Harvest all MOA genes

		:return: A list of genes
		:rtype: list
		"""
		with requests_cache.disabled():
			r = requests.get('https://moalmanac.org/api/genes')
			genes = r.json()
			genes_list = []
			for gene in genes:
				g = self._harvest_gene(gene, variants)
				genes_list.append(g)
			return genes_list

	def _harvest_assertions(self):
		"""
		Harvest all MOA assertions

		:return: A list of assertions
		:rtype: list
		"""
		with requests_cache.disabled():
			r = requests.get('https://moalmanac.org/api/assertions')
			assertions = r.json()
			assertions_list = []
			for assertion in assertions:
				a = self._harvest_assertion(assertion)
				assertions_list.append(a)

		return assertions_list

	def _harvest_variants(self):
		"""
		Harvest all MOA variants

		:return: A list of variants
		:rtype: list
		"""

		with requests_cache.disabled():
			r = requests.get('https://moalmanac.org/api/attribute_definitions')
			attr_def = r.json()
			attr_def = self._get_attr_def(attr_def)

		with requests_cache.disabled():
			r = requests.get('https://moalmanac.org/api/attributes')
			variants = r.json()
			variants_list = []

			temp = 1
			feature_type = self._get_feature_type(variants[0]['attribute_definition'])
			variant_record = {
				'feature_type': feature_type
			}


			for variant in variants:			
				if variant['feature'] == temp:
					v = self._harvest_variant(variant, variant_record, attr_def)
					continue
				else:
					v.update(self._get_feature(v))
					variants_list.append(v)
					feature_type = self._get_feature_type(variant['attribute_definition'])
					variant_record = {
						'feature_type': feature_type
					}
					v = self._harvest_variant(variant, variant_record, attr_def)
					temp = variant['feature']

		return variants_list

	def _harvest_gene(self, gene, variants):
		"""
		Harvest an individual MOA gene record

		:param: a MOA gene associated with assertions
		:return: A dictionary containing MOA gene data
		:rtype: dict
		"""
		gene_record = {
			'name': gene,
			'variants': self._get_variant(gene, variants)
			# TODO: add other details for each indivicual MOA gene
			# entrez_id, description, aliases, etc

		}
		return gene_record

	def _harvest_assertion(self, assertion):
		"""
		Harvest an individual MOA assertion record

		:param: a MOA assertion record 
		:return: A dictionary containing MOA assertion data
		:rtype: dict
		"""
		assertion_record = {
			'id': assertion['assertion_id'],
			'context': assertion['context'],
			'description': assertion['description'],
			'disease': {
				'oncotree_code': assertion['oncotree_code'],
				'oncotree_term': assertion['oncotree_term']
			},
			'therapy_name': assertion['therapy_name'],
			'therapy_type': assertion['therapy_type'],
			'clinical_significance': 
				self._get_therapy(assertion['therapy_resistance'],
			 	assertion['therapy_sensitivity']), # key matched with civic
			 'predictive_implication': assertion["predictive_implication"],
			 'feature_ids': assertion['features'],
			 'source_ids': assertion['sources']
		}
		return assertion_record

	def _harvest_variant(self, variant, variant_record, attr_def):
		"""
		Harvest an individual MOA variant record.

		:param: A MOA variant record
		:return: A dictionary containing MOA variant data
		:rtype: dict
		"""
		variant_record.update({attr_def[variant['attribute_definition']]: variant['value']})

		return variant_record


	def _get_attr_def(self, attr_def):
		"""
		"""
		mapping = {}
		for att in attr_def:
			attr_def_id = att['attribute_def_id']
			attr_name = att['name']
			mapping.update({attr_def_id: attr_name})

		return mapping
	
	def _get_therapy(self, resistance, sensitivity):
		"""
		Get therapy data.

		:param: therapy_resistance, therapy_sensitivity
		:return: whether the therapy response is resistance or sensitivity
		:rtype: str
		"""
		if resistance:
			return "resistance"
		elif sensitivity:
			return "sensitivity"
		else:
			return

	def _get_feature_type(self, attr_def_id): #, feat_def_id):
		"""
		Map the attribute definition ids and feature definition ids with 
		feature_type = [rearrangement, somatic_variant, germline_variant,
		copy_number, microsatellite_stability, mutational_signature, 
		mutational_burden, newantigen_burden, knockdown, silencing, aneuploidy]

		:param: attribute definition id, feature definition id
		:return: mapped feature type
		:rtype: str
		"""
		attr_def_ids = {
			'rearrangement': [1, 2, 3, 4],
			'somatic_variant': [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
			'germline_variant': [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
			'copy_number': [28, 29, 30],
			'microsatellite_stability': [31],
			'mutational_signature': [32],
			'mutational_burden': [33, 34, 35],
			'neoantigen_burden': [36, 37],
			'knockdown': [38, 39],
			'silencing': [40, 41],
			'aneuploidy': [42]
		}

		feat_def_ids = {
			'rearrangement': 1,
			'somatic_variant': 2,
			'germline_variant': 3,
			'copy_number': 4,
			'microsatellite_stability': 5,
			'mutational_signature': 6,
			'mutational_burden': 7,
			'neoantigen_burden': 8,
			'knockdown': 9,
			'silencing': 10,
			'aneuploidy': 11
		}

		attr_key_list = list(attr_def_ids.keys())
		attr_val_list = list(attr_def_ids.values())
		for k, v in attr_def_ids.items():
			if attr_def_id in attr_def_ids[k]:
				feature_type = k
		return feature_type

	def _get_feature(self, v):
		"""
		"""
		feature_type = v['feature_type']
		if feature_type == 'rearrangement':
			feature = '{}--{} {}'.format(v['gene1'], v['gene2'], v['rearrangement_type'])
		elif feature_type == 'somatic_variant':
			feature = '{} {} ({})'.format(v['gene'], v['protein_change'], v['variant_annotation'])
		elif feature_type == 'germline_variant':
			feature = '{} ({})'.format(v['gene'], 'pathogenic' if v['pathogenic'] == 1 else '')
		elif feature_type == 'copy_number':
			feature = '{} {}'.format(v['gene'], v['direction'])
		elif feature_type == 'microsatellite_stability':
			feature = '{}'.format(v['status'])
		elif feature_type == 'mutational_signature':
			feature = 'COSMIC Signature {}'.format(v['cosmic_signature_number'])
		elif feature_type == 'mutational_burden':
			feature = '{} (>= {} mutations)'.format(v['classification'], v['minimum_mutations'])
		elif feature_type == 'neoantigen_burden':
			feature = '{}'.format(v['classification'])
		elif feature_type == 'knockdown':
			feature = '{} ({})'.format(v['gene'], v['technique'])
		elif feature_type == 'silencing':
			feature = '{} ({})'.format(v['gene'], v['technique'])
		else:
			feature = '{}'.format(v['event'])

		return {'feature': feature}
		

	def _get_variant(self, gene, variants):
		"""
		Get the variants information of a given MOA gene

		:param: an MOA gene
		:param: a list of all MOA variants
		:return: a list of all MOA variants of the given MOA gene
		:rtype: list
		"""
		v = []
		feature = []
		for variant in variants:
			if gene in variant.values():
				if variant['feature'] not in feature:
					feature.append(variant['feature'])
					v.append(variant)
				else:
					continue
		return v





a = MOAlamanc()
a.harvest()

