"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
from metakb.normalizers import Normalizers
import pprint
import re


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
        self.normalizers = Normalizers()

    def _extract(self):
        """Extract the CIViC composite JSON file."""
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _create_json(self, transformations):
        civic_dir = PROJECT_ROOT / 'data' / 'civic' / 'transform'
        civic_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{civic_dir}/civic_cdm.json", 'w+') as f:
            json.dump(transformations, f)

    def transform(self):
        """Transform CIViC harvested json to common data model."""
        pp = pprint.PrettyPrinter(sort_dicts=False)
        data = self._extract()
        responses = list()
        evidence_items = data['evidence']
        variants = data['variants']
        genes = data['genes']
        i = 1
        for evidence in evidence_items:
            evidence_id = f"{schemas.NamespacePrefix.CIVIC.value}" \
                          f":{evidence['name']}"
            if evidence_id == 'civic:EID2997':
                response = {
                    'evidence': self._add_evidence(evidence, i),
                    'propositions': self._add_propositions(evidence, i),
                    'variation_descriptors': self._add_variation_descriptors(
                        self._get_record(evidence['variant_id'], variants)),
                    'gene_descriptors': self._add_gene_descriptors(
                        self._get_record(evidence['gene_id'], genes)),
                    'therapies': self._add_therapies(evidence['drugs']),
                    'diseases': self._add_diseases(evidence['disease']),
                    'evidence_sources': self._add_evidence_sources(evidence)
                }

                for variation_descriptor in response['variation_descriptors']:
                    for proposition in response['propositions']:
                        if variation_descriptor['id'] ==\
                                proposition['variation_descriptor']:
                            proposition['has_originating_context'] = \
                                variation_descriptor['value_id']

                # TODO: Fix for when there's multiple diseases and propositions
                for disease in response['diseases']:
                    for proposition in response['propositions']:
                        ncit_id = ([other_id for other_id in disease['xrefs']
                                    if other_id.startswith('ncit:C')] or [None])[0]  # noqa: E501
                        proposition['disease_context'] = ncit_id

                responses.append(response)
                pp.pprint(response)
                i += 1
                break
        return responses

    def _add_diseases(self, disease):
        disesase_norm_resp = \
            self.normalizers.normalize('disease', f"DOID:{disease['doid']}")
        d = {
            'id': f"civic:did{disease['id']}",
            'label': disease['display_name']
        }

        if disesase_norm_resp['record']:
            d['xrefs'] = disesase_norm_resp['record']['concept_ids'] + disesase_norm_resp['record']['xrefs']  # noqa: E501
            d['alternate_labels'] = disesase_norm_resp['record']['aliases']
            d['extensions'] = [
                {
                    'type': 'Extension',
                    'name': 'pediatric_disease',
                    'value': disesase_norm_resp['record']['pediatric_disease']
                }
            ]

        else:
            d['xrefs'] = [f"DOID:{disease['doid']}"]
            d['alternate_labels'] = []
        return [d]

    def _add_therapies(self, drugs):
        """Return therapies."""
        therapies = []
        for drug in drugs:
            therapy_norm_resp = \
                self.normalizers.normalize('therapy', drug['name'])

            therapy = {
                'id': f"civic:tid{drug['id']}",
                'type': 'Therapy',
                'label': drug['name'],
                'xrefs': self._get_therapy_xrefs(therapy_norm_resp, drug),
                'alternate_labels': therapy_norm_resp['record']['aliases'] if 'record' in therapy_norm_resp else [],  # noqa: E501
                'trade_names': therapy_norm_resp['record']['trade_names'] if 'record' in therapy_norm_resp else []  # noqa: E501
            }
            therapies.append(therapy)

        return therapies

    def _get_therapy_xrefs(self, response, drug):
        """Return therapy xrefs."""
        xrefs = []
        concept_ids = []
        if response['record']:
            xrefs = response['record']['xrefs']
            concept_ids = response['record']['concept_ids']

        if drug['ncit_id'] not in xrefs:
            xrefs.append(drug['ncit_id'])

        return xrefs + concept_ids

    def _add_evidence(self, evidence, i):
        """Add evidence to therapeutic response.

        :param dict evidence: Harvested CIViC evidence item records
        """
        evidence = {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:"
                  f"{evidence['name'].lower()}",
            'type': 'EvidenceLine',
            'supported_by': [
                {
                    'type': 'StudyResult',
                    'description': evidence['description'],
                    'confidence':
                        f"civic.trust_rating:{evidence['rating']}_star"
                }
            ],
            'description': evidence['description'],
            'direction':
                self._get_evidence_direction(evidence['evidence_direction']),
            'evidence_level': f"civic.evidence_level:"
                              f"{evidence['evidence_level']}",
            'proposition': f"proposition:{i:03}",  # TODO
            'evidence_sources': [],  # TODO
            # 'contributions': [],  # TODO: After MetaKB first pass
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

    def _add_propositions(self, evidence, i):
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
                '_id': f'proposition:{i:03}',  # TODO
                'type': 'therapeutic_response_proposition',
                'variation_descriptor': f"civic:vid{evidence['variant_id']}",
                'has_originating_context': None,
                'therapy': f"ncit:{drug['ncit_id']}",
                'disease_context': None,
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
        # TODO: Shouldn't hardcode this. We should implement root_concept
        #       in civicpy
        structural_type = None
        molecule_context = None
        if len(variant['variant_types']) == 1:
            so_id = variant['variant_types'][0]['so_id']
            if so_id == 'SO:0001583':
                structural_type = 'SO:0001060'
                molecule_context = 'protein'

        variation_descriptor = {
            'id': f"civic:vid{variant['id']}",
            'type': 'AlleleDescriptor',
            'label': variant['name'],
            'description': variant['description'],
            'value_id': None,
            'value_obj': {},
            'gene_context': f"civic:gid{variant['gene_id']}",
            'molecule_context': molecule_context,
            'structural_type': structural_type,
            'ref_allele_seq': re.split(r'\d+', variant['name'])[0],
            'expressions': self._add_hgvs_expr(variant),
            'xrefs': self._add_variant_xrefs(variant),
            'alternate_labels': [v_alias for v_alias in
                                 variant['variant_aliases'] if not
                                 v_alias.startswith('RS')],
            'extensions': [
                {
                    'type': 'Extension',
                    'name': 'representative_variation_descriptor',
                    'value': f"civic:vid{variant['id']}.rep"
                },
                {
                    'type': 'Extension',
                    'name': 'civic_actionability_score',
                    'value': variant['civic_actionability_score']
                },
                {
                    'type': 'Extension',
                    'name': 'variant_groups',
                    'value': variant['variant_groups']
                }
            ]
        }

        hgvs_protein_exprs = [expr['value'] for expr in
                              variation_descriptor['expressions'] if ':p.'
                              in expr['value']]

        for hgvs_protein_expr in hgvs_protein_exprs:
            # TODO: Switch to using variant /normalize
            response = self.normalizers.tovrs(hgvs_protein_expr)
            if response['variants']:
                variant = response['variants'][0]
                variation_descriptor['value_id'] = variant['_id']
                variation_descriptor['value_obj'] = variant
                break

        return [variation_descriptor]

    def _add_gene_descriptors(self, gene):
        """Return gene descriptors"""
        gene_normalizer_resp = \
            self.normalizers.search('gene', gene['name'], incl='hgnc')
        value_objs = self._get_gene_value_obj(gene_normalizer_resp)
        gene_descriptor = {
            'id': f"civic:gid{gene['id']}",
            'type': 'GeneDescriptor',
            'label': gene['name'],
            'description': gene['description'],
            'value_id': value_objs[0],
            'value_obj': value_objs[1],
            'alternate_labels':
                self._get_search_list(gene_normalizer_resp, 'aliases',
                                      records=gene['aliases']),
            'xrefs': self._get_gene_normalizer_xrefs(gene_normalizer_resp),
            'extensions': [
                {
                    'type': 'Extension',
                    'name': 'previous_labels',
                    'value': self._get_search_list(gene_normalizer_resp,
                                                   'previous_symbols')
                },
                {
                    'type': 'Extension',
                    'name': 'strand',
                    'value': self._get_search_val(gene_normalizer_resp,
                                                  'strand')
                }
            ]
        }
        return [gene_descriptor]

    def _get_search_val(self, response, label):
        for source_match in response['source_matches']:
            for record in source_match['records']:
                if record[label]:
                    return record[label]
        return None

    def _get_search_list(self, response, label, records=None):
        """Return list of records for a given label from search endpoint."""
        if records is None:
            records = []
        for source_match in response['source_matches']:
            for record in source_match['records']:
                if record[label]:
                    records += record[label]

        if not records:
            return []

        return list(set(records))

    def _get_gene_value_obj(self, response):
        """Return VRS _id and location object."""
        value_obj = None
        value_obj_id = None
        for source_match in response['source_matches']:
            for record in source_match['records']:
                for location in record['locations']:
                    value_obj = location
                    value_obj_id = location['_id']
                    break
        return (value_obj_id, value_obj)

    def _get_gene_normalizer_xrefs(self, response):
        """Return xrefs from gene normalization."""
        xrefs = []
        source_matches = response['source_matches']
        for source in source_matches:
            for record in source['records']:
                xrefs.append(record['concept_id'])
                for xref in record['xrefs']:
                    xrefs.append(xref)
        return xrefs

    def _add_hgvs_expr(self, variant):
        """Return a list of hgvs expressions"""
        hgvs_expressions = list()
        for hgvs_expr in variant['hgvs_expressions']:
            if ':g.' in hgvs_expr:
                syntax = 'hgvs:genomic'
            elif ':c.' in hgvs_expr:
                syntax = 'hgvs:transcript'
            else:
                syntax = 'hgvs:protein'
            hgvs_expressions.append(
                {
                    'type': 'Expression',
                    'syntax': syntax,
                    'value': hgvs_expr
                }
            )
        return hgvs_expressions

    def _add_evidence_sources(self, evidence):
        """Add evidence source to response.

        :param dict evidence: A CIViC evidence item record
        """
        source_type = evidence['source']['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value

        source = {
            'id': f"{prefix}:{evidence['source']['citation_id']}",
            'label': evidence['source']['citation'],
            'description': evidence['source']['name'],
            'xrefs': []
        }
        return [source]

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
                    xrefs.append(f"{schemas.XrefSystem.CLINVAR.value}:"
                                 f"{clinvar_entry}")

            elif xref == 'allele_registry_id':
                xrefs.append(f"{schemas.XrefSystem.CLINGEN.value}:"
                             f"{v['allele_registry_id']}")
            elif xref == 'variant_aliases':
                dbsnp_xrefs = [item for item in v['variant_aliases']
                               if item.startswith('RS')]
                for dbsnp_xref in dbsnp_xrefs:
                    xrefs.append(f"{schemas.XrefSystem.DB_SNP.value}:"
                                 f"{dbsnp_xref.split('RS')[-1]}")
        return xrefs


civic = CIViCTransform()
transformation = civic.transform()
civic._create_json(transformation)
