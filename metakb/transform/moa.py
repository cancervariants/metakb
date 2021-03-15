"""A module to convert MOA resources to common data model"""
from metakb import PROJECT_ROOT
import os
import json
import logging
import pprint
import metakb.schemas as schemas
from gene.query import QueryHandler as GeneQueryHandler
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler

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
        self.g_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()
        self.d_handler = DiseaseQueryHandler()
        self.t_handler = TherapyQueryHandler()

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
        sources = data['sources']
        variant = data['variants']  # noqa: F841
        proposition_index = 1
        source_index = 1
        pp = pprint.PrettyPrinter(sort_dicts=False)

        for evidence in evidence_items:
            if evidence['id'] == 69:  # somatic, ABL1 p.T315I (Missense)
                gene_descriptors = \
                    self._get_gene_descriptors(evidence['variant'])
                variation_descriptors = \
                    self._get_variation_descriptors(evidence, gene_descriptors)
                disease_descriptors = \
                    self._get_disease_descriptors(evidence)
                therapy_descriptors = \
                    self._get_therapy_descriptors(evidence)
                evidence_sources = \
                    self._get_evidence_sources(sources[68], source_index)
                response = {
                    'evidence': self._get_evidence(evidence, proposition_index,
                                                   gene_descriptors,
                                                   disease_descriptors,
                                                   therapy_descriptors,
                                                   evidence_sources),
                    'propositions': self._get_propositions(evidence,
                                                           proposition_index,
                                                           gene_descriptors,
                                                           variation_descriptors,  # noqa: E501
                                                           disease_descriptors,
                                                           therapy_descriptors),  # noqa: E501
                    'variation_descriptors': variation_descriptors,
                    'gene_descriptors': gene_descriptors,
                    'therapy_descriptors': therapy_descriptors,
                    'disease_descriptors': disease_descriptors,
                    'evidence_sources': evidence_sources
                }

                responses.append(response)
                pp.pprint(response)
                proposition_index += 1
                source_index += 1
                break

        return responses

    def _get_evidence(self, evidence, proposition_index, gene_descriptors,
                      disease_descriptors, therapy_descriptors,
                      evidence_sources):
        """Add evidence to therapeutic response.

        :param: single evidence(assertion) record from MOA
        :return: list of evidence
        """
        evidence = schemas.Evidence(
            id=f"{schemas.NamespacePrefix.MOA.value}:"
               f"{evidence['id']}",
            description=evidence['description'],
            direction=None,
            evidence_level=f"moa.evidence_level:"
                           f"{evidence['predictive_implication']}",
            supported_by=[
                {
                    'type': 'StudyResult',
                    'description': evidence['description'],
                    'confidence': None
                }
            ],
            proposition=f"proposition:{proposition_index:03}",
            variation_descriptor=f"moa:vid{evidence['variant']['id']}",
            gene_descriptor=gene_descriptors[0]['id'],
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            evidence_sources=[evidence_sources[0]['id']]
        )

        return [evidence.dict()]

    def _get_propositions(self, evidence, proposition_index, gene_descriptors,
                          variation_descriptors, disease_descriptors,
                          therapy_descriptors):
        """Add proposition to therapeutic response

        :param: single evidence(assertion) record from MOA
        :return: list of proposition
        """
        proposition = schemas.TherapeuticResponseProposition(
            _id=f"proposition:{proposition_index:03}",
            type="therapeutic_response_proposition",
            predicate=self._get_predicate(evidence['clinical_significance']),
            variant_origin=self._get_variation_origin(evidence['variant']),
            variation_descriptor=f"moa:vid{evidence['variant']['id']}",
            has_originating_context=variation_descriptors[0]['value_id'],
            gene=gene_descriptors[0]['value']['gene_id'],
            disease_context=disease_descriptors[0]['value']['disease_id'],
            therapy=therapy_descriptors[0]['value']['therapy_id']
        )

        return [proposition.dict()]

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

    def _get_variation_origin(self, variant):
        """Get variation origin"""
        if variant['feature_type'] == 'somatic_variant':
            origin = schemas.VariationOrigin.SOMATIC.value
        elif variant['feature_type'] == 'germline_variant':
            origin = schemas.VariationOrigin.COMMON_GERMLINE.value
        else:
            origin = None

        return origin

    def _get_variation_descriptors(self, evidence, g_descriptors):
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
            gene_context=f"moa:{[g_des['id'] for g_des in g_descriptors]}",
            molecule_context=molecule_context,
            structural_type=structural_type,
            ref_allele_seq=ref_allele_seq,
            expressions=[],
            # xrefs=d_norm_resp.concept_ids
            # alternate_labels=d_norm_resp.aliases
            extensions=[]
        )

        return [variation_descriptor.dict()]

    def _get_gene_descriptors(self, variant):
        """Create gene descriptors"""
        genes = [value for key, value in variant.items()
                 if key.startswith('gene')]

        gene_descriptors = []
        if genes:
            for gene in genes:
                g_handler_resp = \
                    self.g_handler.search_sources(gene, incl='HGNC')
                g_handler_resp = \
                    g_handler_resp['source_matches'][0]
                if 'records' in g_handler_resp and \
                        g_handler_resp['records']:
                    g_handler_resp = g_handler_resp['records'][0]
                else:
                    return []

                gene_descriptor = schemas.GeneDescriptor(
                    id=f'normalize:{gene}',  # TODO
                    label=gene,
                    description='description',  # TODO
                    value=schemas.Gene(gene_id=g_handler_resp.concept_id),
                    alternate_labels=self._get_search_list(g_handler_resp,
                                                           'aliases',
                                                           records=None),
                    xrefs=g_handler_resp.other_identifiers,
                    extensions=self._get_gene_ext(g_handler_resp)
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

    def _get_therapy_descriptors(self, evidence):
        """Add therapies"""
        therapy = evidence['therapy_name']
        t_handler_resp = self.t_handler.search_groups(therapy)
        t_handler_vod = t_handler_resp['value_object_descriptor']

        therapy_descriptor = schemas.ValueObjectDescriptor(
            id=f"normalize:{evidence['therapy_name']}",
            type="TherapyDescriptor",
            label=evidence['therapy_name'],
            value=t_handler_vod['value'],
            xrefs=t_handler_vod['xrefs'],
            alternate_labels=t_handler_vod['alternate_labels'],
            extensions=t_handler_vod['extensions'],
        )

        return [therapy_descriptor.dict()]

    def _get_disease_descriptors(self, evidence):
        """Add disease"""
        ot_code = evidence['disease']['oncotree_code']
        disease_name = evidence['disease']['name']
        d_handler_resp = self.d_handler.search_groups(ot_code)
        d_handler_vod = d_handler_resp['value_object_descriptor']

        disease_descriptor = schemas.ValueObjectDescriptor(
            id=f"normalize:{ot_code}",
            type="DiseaseDescriptor",
            label=disease_name,
            value=d_handler_vod['value'],
            xrefs=d_handler_vod['xrefs'],
            alternate_labels=d_handler_vod['alternate_labels'],
            extensions=d_handler_vod['extensions']
        )

        return [disease_descriptor.dict()]

    def _get_evidence_sources(self, source, source_index):
        """Add evidence source"""
        source = schemas.EvidenceSource(
            id=f"source:{source_index:03}",
            source_id=f"pmid:{source['pmid']}"
                      if source['pmid']
                      else f"normalize:{source['doi']}",
            label=source['citation'],
            description=None,
            doi=source['doi'],
            nct=source['nct'],
            xrefs=[]
        )

        return [source.dict()]


moa = MOATransform()
responses = moa.transform()
# moa._create_json(responses)

# g = GeneQueryHandler()
# print(g.search_sources('ABL1', incl='HGNC'))
# tovars = ToVRS()
# aac = AminoAcidCache()
# validations = tovars.get_validations('ABL1 T315I')
# v = VariantNormalizer()
# print(v.normalize('ABL1 T315I', validations, aac))
# d = DiseaseQueryHandler()
# print(d.search_groups("CML"))
# t = TherapyQueryHandler()
# print(t.search_groups("Imatinib"))
