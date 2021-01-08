"""A module for the Molecular Oncology Almanac harvester"""
from .base import Harvester
from metakb import PROJECT_ROOT
import requests
import requests_cache
import json
import logging


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class MOAlmanac(Harvester):
    """A class for the Molecular Oncology Almanac harvester."""

    def harvest(self):
        """
        Retrieve and store source of evidence, gene, variants, and assertion
        records from MOAlmanac in composite and individual JSON files.

        :return:'True' if successfully retreived, 'False' otherwise
        :rtype: bool
        """
        try:
            sourceOfevidence = self._harvest_sourceOfevidence()
            variants = self._harvest_variants()
            genes = self._harvest_genes(variants)
            assertions = self._harvest_assertions(variants)
            self._create_json(assertions, sourceOfevidence, variants, genes)
            logger.info('MOAlamanc harvester was successful.')
            return True
        except:  # noqa: E722 # TODO: add details of exception error
            logger.info('MOAlamanc harvester was not successful.')
            return False

    def _create_json(self, assertions, sourceOfevidence, variants, genes):
        """
        Create a composite JSON file containing assertions, source of
        of evidence, genes, and variants
        and individual JSON files for each level of MOA record.

        :param: A list of MOA assertions
        :param: A list of MOA source_of_evidence
        :param: A list of MOA variants
        :param: A list of MOA genes
        """
        composite_dict = {
            'assertions': assertions,
            'sourceOfevidence': sourceOfevidence,
            'variants': variants,
            'genes': genes
        }

        # Create composite json
        moa_dir = PROJECT_ROOT / 'data' / 'moa'
        moa_dir.mkdir(exist_ok=True, parents=True)
        with open(f'{PROJECT_ROOT}/data/moa/moa_harvester.json',
                  'w+') as f:
            json.dump(composite_dict, f)
            f.close()

        # Create individual json for assertions, source of evidence,
        # variants and genes
        data = ['assertions', 'sourceOfevidence', 'variants', 'genes']
        for d in data:
            with open(f'{PROJECT_ROOT}/data/moa/{d}.json', 'w+') as f:
                f.write(json.dumps(composite_dict[d]))
                f.close()

    def _harvest_sourceOfevidence(self):
        """
        Harvest all MOA source of evidences

        :return: A list of source of evidence
        :rtype: list
        """
        sourceOfevidence_list = []
        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/sources')
            sources = r.json()
            for source in sources:
                e = self._source_item(source)
                sourceOfevidence_list.append(e)
        return sourceOfevidence_list

    def _harvest_variants(self):
        """
        Harvest all MOA variants

        :return: A list of variants
        :rtype: list
        """
        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/attribute_definitions')
            attr_def = r.json()
            attr_def_idToname = self._get_attr_def(attr_def)

        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/feature_definitions')
            feat_defs = r.json()
            feat_def_nameToattr_def_id = self._get_feat_def(feat_defs)

        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/attributes')
            variants = r.json()
            variants_list = []

            temp = 1  # as a key to compare with feature id
            feature_type = self._get_feature_type(
                variants[0]['attribute_definition'],
                feat_def_nameToattr_def_id)
            variant_record = {
                'feature_type': feature_type,
                'feature_id': variants[0]['feature']
            }
            for variant in variants:
                if variant['feature'] == temp:
                    v = self._harvest_variant(
                        variant, variant_record, attr_def_idToname)
                    continue
                else:
                    v.update(self._get_feature(v))
                    variants_list.append(v)
                    feature_type = self._get_feature_type(
                        variant['attribute_definition'],
                        feat_def_nameToattr_def_id)
                    variant_record = {
                        'feature_type': feature_type,
                        'feature_id': variant['feature']
                    }
                    v = self._harvest_variant(
                        variant, variant_record, attr_def_idToname)
                    temp = variant['feature']
            variants_list.append(v)
        return variants_list

    def _harvest_genes(self, variants):
        """
        Harvest all MOA genes

        :param: A list of harvested MOA variants
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

    def _harvest_assertions(self, variants):
        """
        Harvest all MOA assertions

        :param: A list of harvested MOA variants
        :return: A list of assertions
        :rtype: list
        """
        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/assertions')
            assertions = r.json()
            assertions_list = []
            for assertion in assertions:
                a = self._harvest_assertion(assertion, variants)
                assertions_list.append(a)

        return assertions_list

    def _source_item(self, source):
        """
        Harvest an individual MOA source of evidence

        :param: source record of each assertion record
        :return: a dictionary containing MOA source of evidence data
        :rtype: dict
        """
        s = {
            'id': source['source_id'],
            'type': source['source_type'],
            'assertion_id': source['assertions'],
            'doi': source['doi'],
            'nct': source['nct'],
            'pmid': source['pmid'],
            'url': source['url'],
            'citation': source['citation']
        }
        return s

    def _harvest_variant(self, variant, variant_record, attr_def):
        """
        Harvest an individual MOA variant record.

        :param: A MOA variant record
        :param: a dictionry of pre-constructed variant_record
        :param: a dictionry of attribute definition
        :return: A dictionary containing MOA variant data
        :rtype: dict
        """
        variant_record.update(
            {attr_def[variant['attribute_definition']]: variant['value']})
        # TODO: add other details for each variants
        # allele_registrey, hgvs, transcript, etc

        return variant_record

    def _harvest_gene(self, gene, variants):
        """
        Harvest an individual MOA gene record

        :param: a MOA gene record
        :param: a list of harvested MOA variants
        :return: A dictionary containing MOA gene data
        :rtype: dict
        """
        gene_record = {
            'name': gene,
            'variants': self._get_variant(gene, variants)
            # TODO: add other details for each indivicual MOA gene
            # entrez_id, description, aliases, etc.

        }
        return gene_record

    def _harvest_assertion(self, assertion, variants):
        """
        Harvest an individual MOA assertion record

        :param: a MOA assertion record
        :param: a list of harvested MOA variants
        :return: A dictionary containing MOA assertion data
        :rtype: dict
        """
        assertion_record = {
            'id': assertion['assertion_id'],
            'context': assertion['context'],
            'description': assertion['description'],
            'disease': {
                'name': assertion['disease'],
                'oncotree_code': assertion['oncotree_code'],
                'oncotree_term': assertion['oncotree_term']
            },
            'therapy_name': assertion['therapy_name'],
            'therapy_type': assertion['therapy_type'],
            'clinical_significance': self._get_therapy(
                assertion['therapy_resistance'],
                assertion['therapy_sensitivity']),
            'predictive_implication': assertion["predictive_implication"],
            'feature_ids': assertion['features'],
            'favorable_prognosis': assertion['favorable_prognosis'],
            'created_on': assertion['created_on'],
            'last_updated': assertion['last_updated'],
            'submitted_by': assertion['submitted_by'],
            'validated': assertion['validated'],
            'source_ids': assertion['sources']
        }

        for v in variants:
            if v['feature_id'] == assertion['features'][0]:
                assertion_record.update({'variant': v})

        return assertion_record

    def _get_attr_def(self, attr_def):
        """
        Get the attribute definition mapping data

        :param: MOA attribute definitions json data
        :return: a dictionary maps attribute definition id
                 to attribute definition name
        :rtype: dict
        """
        mapping = {}
        for attr in attr_def:
            mapping[attr['attribute_def_id']] = attr['name']

        return mapping

    def _get_feat_def(self, feat_defs):
        """
        Get the feature definition mapping data

        :param: MOA feature definition json data
        :return: a dictionary maps feature definition name
                 to attribute definition ids
        :rtype: dict
        """
        mapping = {}
        for feat_def in feat_defs:
            mapping[feat_def['name']] = feat_def['attribute_definitions']

        return mapping

    def _get_therapy(self, resistance, sensitivity):
        """
        Get therapy response data.

        :param: therapy_resistance
        :param: therapy_sensitivity
        :return: whether the therapy response is resistance or sensitivity
        :rtype: str
        """
        if resistance:
            return "resistance"
        elif sensitivity:
            return "sensitivity"
        else:
            return

    def _get_feature_type(self, attr_def_id, feat_def_nameToattr_def_id):
        """
        Map the attribute definition id with its corresponding feature_type

        :param: attribute definition id of a MOA variant record,
        :param: dictionary of feature definition name map to its corresponding
                attribute definition ids
        :return: mapped feature type
        :rtype: str
        """
        return ([k for k, v in feat_def_nameToattr_def_id.items()
                if attr_def_id in v] or [None])[0]

    def _get_feature(self, v):
        """
        Get feature name from the harvested variants

        :param: harvested MOA variant
        :return: feature name same format as displayed in moalmanac.org
        :rtype: dict
        """
        feature_type = v['feature_type']
        if feature_type == 'rearrangement':
            feature = '{}{}{}'.format(v['gene1'],
                                      f"--{v['gene2']}" if v['gene2'] else '',
                                      f" {v['rearrangement_type']}"
                                      if v['rearrangement_type'] else '')
        elif feature_type == 'somatic_variant':
            feature = '{}{}{}'.format(v['gene'],
                                      f" {v['protein_change']}"
                                      if v['protein_change'] else '',
                                      f" ({v['variant_annotation']})"
                                      if v['variant_annotation'] else '')
        elif feature_type == 'germline_variant':
            feature = '{}{}'.format(v['gene'], ' (Pathogenic)'
                                    if v['pathogenic'] == '1.0' else '')
        elif feature_type == 'copy_number':
            feature = '{} {}'.format(v['gene'], v['direction'])
        elif feature_type == 'microsatellite_stability':
            feature = '{}'.format(v['status'])
        elif feature_type == 'mutational_signature':
            csn = v['cosmic_signature_number']
            feature = 'COSMIC Signature {}'.format(csn)
        elif feature_type == 'mutational_burden':
            clss = v['classification']
            min_mut = v['minimum_mutations']
            mut_per_mb = v['mutations_per_mb']
            feature = '{}{}'.format(clss,
                                    f" (>= {min_mut} mutations)" if min_mut
                                    else (f" (>= {mut_per_mb} mutations/Mb)"
                                          if mut_per_mb else ''))
        elif feature_type == 'neoantigen_burden':
            feature = '{}'.format(v['classification'])
        elif feature_type == 'knockdown' or feature_type == 'silencing':
            feature = '{}{}'.format(v['gene'], f" ({v['technique']})"
                                    if v['technique'] else '')
        else:
            feature = '{}'.format(v['event'])

        return {'feature': feature.strip()}

    def _get_variant(self, gene, variants):
        """
        Get the variants information of a given MOA gene

        :param: an MOA gene
        :param: a list of harvested MOA variants
        :return: a list of all MOA variants associated with the given MOA gene
        :rtype: list
        """
        v = []
        feature = []
        for variant in variants:
            if gene in variant.values():
                if variant['feature'] not in feature:
                    feature.append(variant['feature'])
                    v.append(variant)
        return v
