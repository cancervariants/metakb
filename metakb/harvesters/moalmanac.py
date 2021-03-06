"""A module for the Molecular Oncology Almanac harvester"""
from .base import Harvester
from metakb import PROJECT_ROOT
import requests
import requests_cache
import json
import logging


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class MOAlmanac(Harvester):
    """A class for the Molecular Oncology Almanac harvester."""

    def harvest(self, fn='moa_harvester.json'):
        """
        Retrieve and store sources, variants, and assertions
        records from MOAlmanac in composite and individual JSON files.

        :param: file name of composite json
        :return:'True' if successfully retreived, 'False' otherwise
        :rtype: bool
        """
        try:
            assertion_resp = self._get_all_assertions()
            sources = self._harvest_sources(assertion_resp)
            variants, variants_list = self._harvest_variants()
            assertions = self._harvest_assertions(assertion_resp, variants_list)  # noqa: E501
            self._create_json(assertions, sources, variants, fn)
            logger.info('MOAlmanac harvester was successful.')
            return True
        except:  # noqa: E722 # TODO: Add specific exception error
            logger.error('MOAlmanac Harvester was not successful.')
            return False

    def _create_json(self, assertions, sources, variants, fn):
        """
        Create a composite JSON file containing assertions,
        sources, and variants
        and individual JSON files for each level of MOA record.

        :param: A list of MOA assertions
        :param: A list of MOA sources
        :param: A list of MOA variants
        :param: File name of the harvester
        """
        composite_dict = {
            'assertions': assertions,
            'sources': sources,
            'variants': variants,
        }

        # Create composite json
        moa_dir = PROJECT_ROOT / 'data' / 'moa'
        moa_dir.mkdir(exist_ok=True, parents=True)

        with open(f'{PROJECT_ROOT}/data/moa/{fn}', 'w+') as f:
            json.dump(composite_dict, f)
            f.close()

        # Create individual json for assertions, sources, variants
        data = ['assertions', 'sources', 'variants']
        for d in data:
            with open(f'{PROJECT_ROOT}/data/moa/{d}.json', 'w+') as f:
                f.write(json.dumps(composite_dict[d]))
                f.close()

    def _harvest_sources(self, assertion_resp):
        """
        Harvest all MOA sources

        :param: A list of MOA assertion records
        :return: A list of sources
        :rtype: list
        """
        sources = []

        for assertion in assertion_resp:
            source = assertion['sources'][0]
            s = self._source_item(source)
            if s not in sources:
                sources.append(s)

        return sources

    def _harvest_variants(self):
        """
        Harvest all MOA variants

        :return: A list of variants
        :rtype: list
        """
        variants_list = self._get_all_variants()
        variants = []

        for variant in variants_list:
            v = self._harvest_variant(variant)
            variants.append(v)

        return variants, variants_list

    def _harvest_assertions(self, assertion_resp, variants_list):
        """
        Harvest all MOA assertions

        :param: A list of MOA assertion records
        :param: A list of MOA variant records
        :return: A list of assertions
        :rtype: list
        """
        assertions = []
        for assertion in assertion_resp:
            a = self._harvest_assertion(assertion, variants_list)
            assertions.append(a)

        return assertions

    def _get_all_assertions(self):
        """
        Return all assertion records.

        :return: All moa assertion records
        """
        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/assertions')
            assertions = r.json()

        return assertions

    def _get_all_variants(self):
        """
        Return all variant records

        :return: All moa variant records
        """
        with requests_cache.disabled():
            r = requests.get('https://moalmanac.org/api/features')
            variants = r.json()

        return variants

    def _source_item(self, source):
        """
        Harvest an individual MOA source of evidence

        :param: source record of each assertion record
        :return: a dictionary containing MOA source of evidence data
        :rtype: dict
        """
        source_record = {
            'id': source['source_id'],
            'type': source['source_type'],
            'doi': source['doi'],
            'nct': source['nct'],
            'pmid': source['pmid'],
            'url': source['url'],
            'citation': source['citation']
        }
        return source_record

    def _harvest_variant(self, variant):
        """
        Harvest an individual MOA variant record.

        :param: A MOA variant record
        :return: A dictionary containing MOA variant data
        :rtype: dict
        """
        variant_record = {
            'id': variant['feature_id']
        }

        variant_record.update({k: v for k, v in variant['attributes'][0].items()})  # noqa: E501
        variant_record.update(self._get_feature(variant_record))

        return variant_record

    def _harvest_assertion(self, assertion, variants_list):
        """
        Harvest an individual MOA assertion record

        :param: a MOA assertion record
        :param: a list of MOA variant records
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
            'favorable_prognosis': assertion['favorable_prognosis'],
            'created_on': assertion['created_on'],
            'last_updated': assertion['last_updated'],
            'submitted_by': assertion['submitted_by'],
            'validated': assertion['validated'],
            'source_ids': assertion['sources'][0]['source_id']
        }

        for v in variants_list:
            if v['attributes'][0] == assertion['features'][0]['attributes'][0]:
                assertion_record.update({'variant': self._harvest_variant(v)})

        return assertion_record

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
            feature = '{}'.format(v.get('status'))
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
