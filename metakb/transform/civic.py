"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CIViCTransform:
    """A class for transforming CIViC to the common data model."""

    def __init__(self, fn='civic_harvester.json'):
        """Initialize CIViCTransform class.

        :param str fn: The file name of the composite JSON to transform.
        """
        self._fn = fn

    def _extract(self):
        """Extract the CIViC composite JSON file."""
        with open(f"{PROJECT_ROOT}/data/civic/{self._fn}", 'r') as f:
            return json.load(f)

    def tranform(self):
        """Transform CIViC harvested json to common data model."""
        data = self._extract()
        response = dict()
        response['response'] = {'statements': list()}
        evidence = data['evidence']
        for e in evidence:
            self._add_statement(e, response)
            self._add_gks_descriptors(e, response)
            self.add_value_objects(e, response)
            break
        print(response)

    def _add_statement(self, e, response):
        statement = {
            'id': f"civic:{e['name']}",
            'type': 'GksTherapeuticResponse',
            # Is this variant_id?
            'molecular_profile': f"civic:VID{e['variant_id']}",
            'therapeutic_intervention': 'therapeutic_intervention:',   # TODO
            'disease': f"civic:DiseaseID{e['disease']['id']}",
            'variant_origin': e['variant_origin'],
            'clinical_significance': e['clinical_significance'],
            'evidence_level': e['evidence_level'],
            'provenance': None,  # TODO
        }
        response['response']['statements'].append(statement)

    def _add_gks_descriptors(self, e, response):
        gks_descriptors = []  # noqa: F841
        gks_descriptor = {
            'id': "therapeutic_intervention:",   # TODO
            'type': 'GksTherapeuticIntervention',
            'label': None,
            'components': [],

        }
        response['response']['gks_descriptors'].append(gks_descriptor)

    def _add_value_objects(self, e, response):
        pass

    def _add_variant(self, v, response):
        variant = {  # noqa: F841
            'id': f"civic:VID{v['id']}",
            'type': 'AlleleDescriptor',  # Is this always AlleleDescriptor?
            'label': f"{v['entrez_name']} {v['name']}",
            'value_id': None,  # TODO
            'expansion_set': 'variation_set:',  # TODO
            'gene': f"civic:GID{v['gene_id']}",
            'xref': [],  # TODO
            'alias': None
        }

    def _add_gene(self, g, response):
        gene = {  # noqa: F841
            'id': g['id'],
            'type': 'GeneDescriptor',
            'label': g['name'],
            'description': g['description'],
            'value_id': None,  # TODO
            'xref': [
                {'system': 'ncbigene', 'id': g['entrez_id']}
            ],
            'alias': g['aliases'],
            'provenance': None  # TODO
        }


CIViCTransform().tranform()
