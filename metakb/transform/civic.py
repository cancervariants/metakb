"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
import pprint


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CIViCTransform:
    """A class for transforming CIViC to the common data model."""

    def __init__(self,
                 file_path=f"{PROJECT_ROOT}/data/civic/civic_harvester.json"):
        """Initialize CIViCTransform class.

        :param str file_path: The file path to the composite JSON to transform.
        """
        self._file_path = file_path

    def _extract(self):
        """Extract the CIViC composite JSON file."""
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def transform(self):
        """Transform CIViC harvested json to common data model."""
        pp = pprint.PrettyPrinter(sort_dicts=False)
        data = self._extract()
        responses = list()
        evidence_items = data['evidence']
        variants = data['variants']
        for evidence in evidence_items:
            response = dict()
            evidence_id = f"{schemas.NamespacePrefix.CIVIC.value}" \
                          f":{evidence['name']}"
            if evidence_id == 'civic:EID2997':
                response['evidence'] = self._add_evidence(evidence)
                response['propositions'] = self._add_propositions(evidence)
                response['variation_descriptors'] = \
                    self._add_variation_descriptors(
                        self._get_record(evidence['variant_id'], variants))
                response['vrsatile_descriptors'] = \
                    self._add_vrsatile_descriptors(evidence)
                # response['therapies'] = self._add_therapies()
                response['evidence_sources'] = \
                    self._add_evidence_sources(evidence)

                responses.append(response)
                pp.pprint(response)
                break
        return responses

    def _add_evidence(self, evidence):
        """Add evidence to therapeutic response.

        :param dict evidence: Harvested CIViC evidence item records
        """
        evidence = {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:"
                  f"{evidence['name'].lower()}",
            'type': 'evidence',
            'description': evidence['description'],
            'direction':
                self._get_evidence_direction(evidence['evidence_direction']),
            'evidence_level': f"civic.evidence_level:"
                              f"{evidence['evidence_level']}",
            'proposition': "proposition:",  # TODO
            'evidence_sources': [],  # TODO
            'contributions': [],  # TODO
            'strength': f"civic.trust_rating:{evidence['rating']}_star"
        }
        return [evidence]

    def _get_evidence_direction(self, direction) -> str:
        """Return the evidence direction.

        :param str direction: The civic evidence_direction value
        :return: `supports` or `does_not_support`
        """
        if direction == 'Supports':
            return schemas.Direction.SUPPORTS.value
        else:
            return schemas.Direction.SUPPORTS.value

    def _add_propositions(self, evidence):
        """Add proposition to response.

        :param dict evidence: CIViC evidence item record
        """
        propositions = list()
        for drug in evidence['drugs']:
            predicate = None
            if evidence['evidence_type'] == 'Predictive':
                if evidence['clinical_significance'] == 'Sensitivity/Response':
                    predicate = 'predicts_sensitivity_to'
            proposition = {
                '_id': 'proposition:',  # TODO
                'type': 'therapeutic_response_proposition',
                'vrsatile_descriptor': f"civic:vid{evidence['variant_id']}",
                'therapy': f"ncit:{drug['ncit_id']}",
                'disease_context': '',  # TODO
                'predicate': predicate,
                'variant_origin': evidence['variant_origin'].lower()
            }
            propositions.append(proposition)

        return propositions

    def _add_variation_descriptors(self, variant):
        """Add variation descriptors to response.

        :param dict variant: A CIViC variant record
        :return:
        """
        variation_descriptor = {
            'id': f"civic:vid{variant['id']}",
            'label': variant['name'],
            'description': variant['description'],
            'type': 'AlleleDescriptor',
            'value_id': 'ga4gh:',  # TODO
            'associated_gene_symbol': variant['entrez_name'],  # TODO: Check
            'associated_gene_descriptor': f"civic:gid{variant['gene_id']}"
        }
        return [variation_descriptor]

    def _add_evidence_sources(self, evidence):
        """Add evidence source to response.

        :param dict evidence: A CIViC evidence item record
        """
        source_type = evidence['source']['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
        else:
            prefix = ''
        source = {
            'id': f"{prefix}:{evidence['source']['citation_id']}",
            'label': evidence['source']['citation'],
            'description': evidence['source']['name'],
            'xrefs': []
        }
        return [source]

    def _add_disease_context(self, evidence):
        """Return disease context.

        :param dict evidence: Harvested CIViC evidence item records
        :return: A dictionary containing the disease context
        """
        return {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:"
                  f"DiseaseID{evidence['disease']['id']}",
            'label': evidence['disease']['name'],
            'xrefs': [self._add_xref(schemas.XrefSystem.DISEASE_ONTOLOGY.value,
                                     evidence['disease']['doid'])]
        }

    def _add_vrsatile_descriptors(self, evidence):
        return [
            {
                'id': f"civic:{evidence['variant_id']}"
            }
        ]

    def _add_therapy_profile(self, evidence):
        """Return therapy profile.

        :param dict evidence: Harvested CIViC evidence item records
        :return: A dictionary containing the therapy profile
        """
        therapy_profile = {
            'label': None,
            'drugs': [self._add_drug(drug) for drug in evidence['drugs']],
            'drug_interaction_type': evidence['drug_interaction_type']
        }
        drug_labels = [drug['label'] for drug in therapy_profile['drugs']]
        if drug_labels:
            if len(drug_labels) == 1:
                therapy_profile['label'] = drug_labels[0]
            elif len(drug_labels) == 2:
                therapy_profile['label'] = \
                    f"{drug_labels[0]} and {drug_labels[1]} " \
                    f"{therapy_profile['drug_interaction_type']} Therapy"
        return therapy_profile

    def _add_clinical_significance(self, e):
        """Return clinical significance for a given evidence item.

        :param dict e: Harvested CIViC evidence item records
        :return: A string giving the clinical significance for an evidence item
        """
        clin_sig = None
        if 'clinical_significance' in e and e['clinical_significance']:
            clin_sig = e['clinical_significance']
        return clin_sig

    def _add_drug(self, drug):
        """Return drug data.

        :param dict drug: A CIViC drug record
        """
        return {
            'id': f"{schemas.NamespacePrefix.NCIT.value}:{drug['id']}",
            'label': drug['name'],
            'xrefs': [self._add_xref('ncit', drug['ncit_id'])],
            'aliases': drug['aliases']
        }

    def _add_variant(self, variants, variant_id):
        """Add variant data to the response.

        :param dict variants: Harvested CIViC variants
        :param str variant_id: The variant's ID
        :return: A dictionary containing variant data
        """
        v = self._get_record(variant_id, variants)
        return {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:VID{v['id']}",
            'type': 'variant',  # Should this be AlleleDescriptor?
            'label': f"{v['entrez_name']} {v['name']}",
            'gene': f"{schemas.NamespacePrefix.CIVIC.value}:GID{v['gene_id']}",
            'hgvs_descriptions': v['hgvs_expressions'],
            'xrefs': self._add_variant_xrefs(v),
            'aliases': [alias for alias in v['variant_aliases']
                        if not alias.startswith('RS')]
        }

    def _get_record(self, record_id, records):
        """Get a CIViC record by ID.

        :param str record_id: The ID of the record we are searching for
        :param dict records: A dict of records for a given CIViC record type
        """
        for r in records:
            if r['id'] == record_id:
                return r

    def _add_variant_xrefs(self, v):
        """Get a list of xrefs for a variant.

        :param dict v: A CIViC variant record
        :return: A dictionary of xrefs
        """
        xrefs = []
        for xref in ['clinvar_entries', 'allele_registry_id',
                     'variant_aliases']:
            if xref == 'clinvar_entries':
                for clinvar_entry in v['clinvar_entries']:
                    xrefs.append(self._add_xref(
                        schemas.XrefSystem.CLINVAR.value, clinvar_entry,
                        xref_type='variation'))

            elif xref == 'allele_registry_id':
                xrefs.append(self._add_xref(schemas.XrefSystem.CLINGEN.value,
                                            v['allele_registry_id']))
            elif xref == 'variant_aliases':
                dbsnp_xrefs = [item for item in v['variant_aliases']
                               if item.startswith('RS')]
                for dbsnp_xref in dbsnp_xrefs:
                    xrefs.append(self._add_xref(
                        schemas.XrefSystem.DB_SNP.value,
                        dbsnp_xref.split('RS')[-1],
                        xref_type='rs'))
        return xrefs

    def _add_xref(self, system, system_id, xref_type=None):
        """Return xref data.

        :param str system: The name of the system
        :param str system_id: The system's ID for the concept
        :param str xref_type: The type of the xref
        """
        xref = {
            'system': system,
            'id': system_id
        }
        if xref_type:
            xref['type'] = xref_type
        return xref


# CIViCTransform().transform()
