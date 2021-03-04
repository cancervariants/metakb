"""A module to convert MOA resources to common data model"""
from metakb import PROJECT_ROOT
import os
import json
import logging
import metakb.schemas as schemas
from gene.query import Normalizer as GeneNormalizer

os.environ['GENE_NORM_DB_URL'] = "http://localhost:8000"

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class MOATransform:
    """A class for transforming MOA resources to common data model"""

    def __init__(self,
                 file_path=f"{PROJECT_ROOT}/data/moa/moa_harvester.json"):
        """
        Initialize MOATransform class

        :param: The file path to the composite JSON file
        """
        self.file_path = file_path
        self.g_norm = GeneNormalizer()

    def _extract(self):
        """Extract the MOA composite JSON file."""
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _create_json(self, transformations):
        """Create json"""
        moa_dir = PROJECT_ROOT / 'data' / 'moa' / 'transform'
        moa_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{moa_dir}/moa_cdm.json", 'w+') as f:
            json.dump(transformations, f)

    def transform(self):
        """Transform MOA harvested JSON to common date model"""
        data = self._extract()
        responses = []

        evidence_items = data['assertions']

        for evidence in evidence_items:
            if evidence['id'] == 69:
                response = {}
                response['evidence'] = self._add_evidence(evidence)
                response['propositions'] = self._add_propositions(evidence)
                response['variation_descriptors'] = \
                    self._add_variation_descriptors(evidence)
                response['gene_descriptor'] = \
                    self._add_gene_descriptors(evidence['variant'])

                responses.append(response)

                break

        return responses

    def _add_evidence(self, evidence):
        """Add evidence to therapeutic response.

        :param: single evidence(assertion) record from MOA
        :return: list of evidence
        """
        evidence = [{
            'id': f"{schemas.NamespacePrefix.MOA.value}:"
                  f"{evidence['id']}",
            'type': "EvidenceLine",
            'supported_by': [
                {
                    'type': 'StudyResult',
                    'description': evidence['description'],
                    'confidence': None
                }
            ],
            'description': evidence['description'],
            'direction': None,
            'evidence_level': None,  # TODO
            'proposition': "proposition",  # TODO
            'evidence_source': ["evidence_source"],  # TODO
            'contributions': ["contributions"]  # TODOs
        }]

        return evidence

    def _add_propositions(self, evidence):
        """Add proposition to therapeutic response

        :param: single evidence(assertion) record from MOA
        :return: list of proposition
        """
        proposition = [{
            '_id': "id",  # TODO
            'type': "therapeutic_response_proposition",
            'variation_descriptor': f"moa:vid{evidence['variant']['id']}",
            'has_originating_context': "has_originating_context",  # TODO
            'therapy': "therapy",  # TODO
            'disease_context': None,  # get from disease norm
            'predicate':
                self._get_predicate(evidence['clinical_significance']),
            'variant_origin': 'somatic'
                if evidence['variant']['feature_type'] == 'somatic_variant'
                else 'N/A'
        }]

        return proposition

    def _get_predicate(self, clinical_significance):
        """Get the predicate of this record

        :param: clinical significance of the assertion
        :return: predicate
        """
        predicate = None
        if clinical_significance == 'sensitivity':
            predicate = 'predicts_sensitivity_to'
        elif clinical_significance == 'resistance':
            predicate = 'predicts_resistance_to'

        return predicate

    def _add_variation_descriptors(self, evidence):
        """Add variation descriptor to therapeutic response

        :param: single evidence(assertion) record from MOA
        :return: list of variation descriptor
        """
        variant = evidence['variant']
        ref_allele_seq = variant['reference_allele'] \
            if 'reference_allele' in variant else None

        structural_type, molecule_context = None, None
        if 'variant_annotation' in variant:
            if variant['variant_annotation'] == 'Missense':
                structural_type = "SO:0001606"
                molecule_context = 'protein'

        variation_descriptor = [{
            'id': f"moa:vid{variant['id']}",
            'type': "AlleleDescriptor",
            'label': variant['feature'],
            'description': "description",  # get from var norm
            'value_id': "value_id",  # get from var norm
            'gene_descriptor': "gene_descriptor_id",  # get from gene norm
            'molecule_context': molecule_context,
            'structural_type': structural_type,
            'ref_allele_seq': ref_allele_seq,
            'expressions': [],
            'xrefs': [],  # get from disease norm
            'alternate_labels': [],  # get from disease norm
            'extensions': [],  # TODO
        }]

        return variation_descriptor

    def _add_gene_descriptors(self, variant):
        """Create gene descriptors"""
        genes = [value for key, value in variant.items()
                 if key.startswith('gene')]

        gene_descriptors = []
        if genes:
            for gene in genes:
                gene_normalizer_resp = \
                    self.g_norm.normalize(gene, incl='HGNC')
                value_objs = self._get_gene_value_obj(gene_normalizer_resp)
                gene_descriptor = {
                    'id': 'id',  # TODO
                    'type': 'GeneDescriptor',
                    'label': gene,
                    'description': 'description',  # TODO
                    'value_id': value_objs[0],
                    'value_obj': value_objs[1],
                    'alternate_labels':
                        self._get_search_list(gene_normalizer_resp, 'aliases',
                                              records=None),
                    'xrefs': \
                        self._get_gene_normalizer_xrefs(gene_normalizer_resp),
                    'extensions': [
                        {
                            'type': 'Extension',
                            'name': 'previous_labels',
                            'value':
                                self._get_search_list(gene_normalizer_resp,
                                                      'previous_symbols')
                        },
                        {
                            'type': 'Extension',
                            'name': 'strand',
                            'value': ''.join(
                                    self._get_search_list(gene_normalizer_resp,
                                                          'strand'))
                        }
                    ]

                }
                gene_descriptors.append(gene_descriptor)

        return gene_descriptors

    def _get_gene_value_obj(self, response):
        """Get gene value object"""
        value_obj = None
        value_obj_id = None
        for source_match in response['source_matches']:
            for record in source_match['records']:
                for location in record.locations:
                    value_obj = location
                    value_obj_id = location.id
                    break
        return (value_obj_id, value_obj)

    def _get_search_list(self, response, key, records=None):
        """Get search list by keyword"""
        if records is None:
            records = []
        for source_match in response['source_matches']:
            for record in source_match['records']:
                if getattr(record, key):
                    records += getattr(record, key)

        if not records:
            return []

        return list(set(records))

    def _get_gene_normalizer_xrefs(self, response):
        """Return xrefs from gene normalization."""
        xrefs = []
        source_matches = response['source_matches']
        for source in source_matches:
            for record in source['records']:
                xrefs.append(record.concept_id)
                for xref in record.xrefs:
                    xrefs.append(xref)

        return xrefs


moa = MOATransform()
responses = moa.transform()
# moa._create_json(responses)

# g = GeneNormalizer()
# print(g.normalize('BRAF', incl='HGNC'))
