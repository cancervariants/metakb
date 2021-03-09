"""A module to convert MOA resources to common data model"""
from metakb import PROJECT_ROOT
import os
import json
import logging
import pprint
import metakb.schemas as schemas
from gene.query import Normalizer as GeneNormalizer
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
# from disease.normalize import Normalize as DiseaseNormalizer

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
        self.variant_normalizer = VariantNormalizer()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()
        # self.d_norm = DiseaseNormalizer()

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
        pp = pprint.PrettyPrinter(sort_dicts=False)
        for evidence in evidence_items:
            if evidence['id'] == 69:  # somatic, ABL1 p.T315I (Missense)
                response = {}
                response['evidence'] = self._add_evidence(evidence)
                response['propositions'] = self._add_propositions(evidence)
                response['variation_descriptors'] = \
                    self._add_variation_descriptors(evidence)
                response['gene_descriptor'] = \
                    self._add_gene_descriptors(evidence['variant'])
                response['therapy'] = self._add_therapies(evidence)
                response['disease'] = self._add_disease(evidence)

                responses.append(response)
                pp.pprint(response)
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

        variant_query = f"{variant['gene']} {variant['protein_change'][2:]}"
        validations = self.variant_to_vrs.get_validations(variant_query)
        v_norm_resp = \
            self.variant_normalizer.normalize(variant_query,
                                              validations,
                                              self.amino_acid_cache)

        # disease_name = evidence['disease']['oncotree_term']
        # d_norm_resp = self.disease_normalizer.normalize(disease_name)

        variation_descriptor = schemas.VariationDescriptor(
            id=f"moa:vid{variant['id']}",
            label=variant['feature'],
            description=None,
            value_id=v_norm_resp.value_id,
            value=v_norm_resp.value,
            gene_context="gene_descriptor_id",  # get from gene norm
            molecule_context=molecule_context,
            structural_type=structural_type,
            ref_allele_seq=ref_allele_seq,
            expressions=[],
            # xrefs=d_norm_resp.concept_ids
            # alternate_labels=d_norm_resp.aliases
            extensions=[]
        )

        return [variation_descriptor.dict()]

    def _add_gene_descriptors(self, variant):
        """Create gene descriptors"""
        genes = [value for key, value in variant.items()
                 if key.startswith('gene')]

        gene_descriptors = []
        if genes:
            for gene in genes:
                g_norm_resp = \
                    self.g_norm.normalize(gene, incl='HGNC')
                g_norm_resp = \
                    g_norm_resp['source_matches'][0]
                if 'records' in g_norm_resp and \
                        g_norm_resp['records']:
                    g_norm_resp = g_norm_resp['records'][0]
                else:
                    return []

                gene_descriptor = schemas.GeneDescriptor(
                    id=f'normalize:{gene}',  # TODO
                    label=gene,
                    description='description',  # TODO
                    value=schemas.Gene(gene_id=g_norm_resp.concept_id),
                    alternate_labels=self._get_search_list(g_norm_resp,
                                                           'aliases',
                                                           records=None),
                    xrefs=g_norm_resp.other_identifiers,
                    extensions=self._get_gene_ext(g_norm_resp)
                )
                gene_descriptors.append(gene_descriptor.dict())

        return gene_descriptors

    def _get_gene_ext(self, gene_normalizer_resp):
        """Get gene extensions"""
        ext = []
        for key in ['strand', 'previous_labels', 'xrefs',
                    'locations']:
            value = self._get_search_list(gene_normalizer_resp, key)
            if value:
                if key == 'xrefs':
                    key = 'associated_with'
                if key == 'locations':
                    key = 'chromosome_location'
                ext.append(schemas.Extension(name=key, value=value))

        return ext

    def _get_search_list(self, response, key, records=None):
        """Get search list by keyword"""
        if hasattr(response, key):
            if getattr(response, key):
                records = getattr(response, key)
        if key == 'locations':
            for location in records:
                records = [location.dict(by_alias=True)]
        if not records:
            return []

        return records

    def _add_therapies(self, evidence):
        """Add therapies"""
        therapy = [{
            'id': f"normalize:{evidence['therapy_name']}",
            'label': evidence['therapy_name'],
            'xrefs': [],  # TODO
            'alternate_labels': [],  # TODO
            'trade_names': [],  # TODO
        }]

        return therapy

    def _add_disease(self, evidence):
        """Add disease"""
        disease = [{
            'id': f"normalize:{evidence['disease']['oncotree_term']}",
            'label': evidence['disease'],
            'xrefs': [],  # TODO
            'alternate_labels': [],  # TODO
            'extensions': [],  # TODO
        }]

        return disease


moa = MOATransform()
responses = moa.transform()
# moa._create_json(responses)

# g = GeneNormalizer()
# print(g.normalize('ABL1', incl='HGNC'))
# tovars = ToVRS()
# aac = AminoAcidCache()
# validations = tovars.get_validations('ABL1 T315I')
# v = VariantNormalizer()
# print(v.normalize('ABL1 T315I', validations, aac))
