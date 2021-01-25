"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
from metakb.models.common import VariantOrigin, ClinicalSignificance, \
    DrugInteractionType, GKSDescriptorType, XrefSystem
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
        genes = data['genes']
        variants = data['variants']
        for e in evidence:
            if e['id'] == 3017:
                self._add_statement(e, response)
                self._add_gks_descriptors(e, genes, variants, response)
                # self.add_value_objects(e, response)
                break
        print(response)

    def _add_statement(self, e, response):

        clin_sig = None
        if 'clinical_significance' in e and e['clinical_significance']:
            clin_sig = e['clinical_significance']
            if clin_sig == 'Sensitivity/Response':
                clin_sig = ClinicalSignificance.SENSITIVITY.value

        statement = {
            'id': f"civic:{e['name']}",
            'type': 'GksTherapeuticResponse',
            # Is this variant_id?
            'molecular_profile': f"civic:VID{e['variant_id']}",
            'therapeutic_intervention': 'therapeutic_intervention:',   # TODO
            'disease': f"civic:DiseaseID{e['disease']['id']}",
            'variant_origin': VariantOrigin[e['variant_origin'].upper()].value,
            'clinical_significance': clin_sig,
            'evidence_level': e['evidence_level'],
            'provenance': None,  # TODO
        }
        response['response']['statements'].append(statement)

    def _add_gks_descriptors(self, e, genes, variants, response):
        gks_descriptors = []  # noqa: F841

        components = [self._add_component(drug) for drug in e['drugs']]
        drug_interaction_type = \
            DrugInteractionType[e['drug_interaction_type'].upper()].value

        # Is components always len == 2?
        label = '{} and {} {} Therapy'.format(components[0]['label'],
                                              components[1]['label'],
                                              drug_interaction_type.capitalize())  # noqa: E501

        gks_descriptor = {
            'id': "therapeutic_intervention:",   # TODO
            'type': 'GksTherapeuticIntervention',
            'label': label,
            'components': components,
            'drug_interaction_type': drug_interaction_type


        }
        gks_descriptors.append(gks_descriptor)
        gks_descriptors.append(self._add_gene(e, genes, variants))
        self._add_allele_descriptors(gks_descriptors, e['variant_id'],
                                     variants, e['gene_id'])
        response['response']['gks_descriptors'] = gks_descriptors

    def _add_component(self, drug):
        return {
            'id': f"ncit:{drug['id']}",
            'label': drug['name']
        }

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

    def _get_record(self, record_id, record_list):
        for r in record_list:
            if r['id'] == record_id:
                return r

    def _add_gene(self, e, genes, variants):
        g = self._get_record(e['gene_id'], genes)

        return {  # noqa: F841
            'id': f"civic:GID{g['id']}",
            'type': 'GeneDescriptor',
            'label': g['name'],
            # 'description': g['description'],
            'value_id': "hgnc:",  # TODO: Where do we get this value?
            'xref': [
                {'system': 'ncbigene', 'id': g['entrez_id']}
            ],
            'alias': g['aliases'],
            'provenance': None  # TODO
        }

    def _add_allele_descriptors(self, gks_descriptors, v_id, variants, g_id):
        v = self._get_record(v_id, variants)
        xrefs = self._add_xrefs(v)

        obj = {
            'id': f"civic:VID{v['id']}",
            'type': GKSDescriptorType.ALLELE_DESCRIPTOR.value,
            'label': f"{v['entrez_name']} {v['name']}",
            'value_id': None,  # TODO
            'expansion_set': None,  # TODO
            'gene': f"civic:GID{g_id}",
            'xrefs': xrefs,
            'aliases': v['variant_aliases'],  # TODO
        }
        gks_descriptors.append(obj)

        for hgvs_expression in v['hgvs_expressions']:
            gks_descriptors.append({
                'id': "hgvs:",  # TODO
                'type': GKSDescriptorType.ALLELE_DESCRIPTOR.value,
                'label': hgvs_expression,
                'value_id': None,  # TODO
            })

    def _add_xrefs(self, v):
        xrefs = []
        if 'clinvar_entries' in v:
            for clinvar_entry in v['clinvar_entries']:
                xrefs.append({
                    'system': XrefSystem.CLINVAR.value,
                    'id': clinvar_entry,
                    'type': 'variation'
                })
        if 'allele_registry_id' in v:
            xrefs.append({
                'system': XrefSystem.CLINVAR.value,
                'id': v['allele_registry_id']
            })

        # TODO: Add dbSNP

        return xrefs


CIViCTransform().tranform()
