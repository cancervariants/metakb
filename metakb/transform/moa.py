"""A module to convert MOA resources to common data model"""
from metakb import PROJECT_ROOT
import json
import logging

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

    def _extract(self):
        """Extract the MOA composite JSON file."""
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def transform(self):
        """Transform MOA harvested JSON to common date model"""
        data = self._extract()
        responses = []

        evidence_items = data['assertions']

        for evidence in evidence_items:
            response = {}
            response['evidence'] = self._add_evidence(evidence)
            response['propositions'] = self._add_propositions(evidence)
            response['variation_descriptors'] = \
                self._add_variation_descriptors(evidence)

            responses.append(response)

        return responses

    def _add_evidence(self, evidence):
        """Add evidence to therapeutic response.

        :param: single evidence(assertion) record from MOA
        :return: list of evidence
        """
        evidence = [{
            'id': "moa:" f"{evidence['id']}",
            'type': "EvidenceLine",
            'supported_by': [],  # TODO
            'description': evidence['description'],
            'direction': "direction",  # TODO
            'evidence_level': "evidence_level",  # TODO
            'proposition': "proposition",  # TODO
            'evidence_source': "evidence_source",  # TODO
            'contributions': "contributions"  # TODOs
        }]

        return evidence

    def _add_propositions(self, evidence):
        """Add proposition to therapeutic response

        :param: single evidence(assertion) record from MOA
        :return: list of proposition
        """
        proposition = [{
            'id': "id",  # TODO
            'type': "therapeutic_response_proposition",
            'variation_descriptor': f"moa:vid{evidence['variant']['id']}",
            'has_originating_context': "has_originating_context",  # TODO
            'therapy': "therapy",  # TODO
            'disease_context': "disease_context",  # TODO
            'predicate':
                self._get_predicate(evidence['clinical_significance']),
            'variant_origin': evidence['variant']['feature_type']
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

        variation_descriptor = [{
            'id': f"moa:vid{variant['id']}",
            'type': "AlleleDescriptor",
            'label': variant['feature'],
            'description': "description",  # TODO
            'value_id': "value_id",  # TODO
            'gene_descriptor': "gene_descriptor",  # TODO
            'molecule_context': "molecule_context",  # TODO
            'structural_type': "structural_type",  # TODO
            'ref_allele_seq': ref_allele_seq,
            'expressions': [],  # TODO
            'xrefs': [],  # TODO
            'alternate_labels': [],  # TODO
            'extensions': [],  # TODO
        }]

        return variation_descriptor
