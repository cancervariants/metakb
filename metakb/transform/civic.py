"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
from metakb.normalizers import Normalizers
import pprint
import re
import os
from gene.query import Normalizer as GeneNormalizer
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
# import therapy

os.environ['GENE_NORM_DB_URL'] = "http://localhost:8000"


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
        self.gene_normalizer = GeneNormalizer()
        self.variant_normalizer = VariantNormalizer()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()

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
                        self._get_record(evidence['variant_id'], variants),
                        self._get_record(evidence['gene_id'], genes)),
                    'gene_descriptors': self._add_gene_descriptors(
                        self._get_record(evidence['gene_id'], genes)),
                    'therapies': self._add_therapies(evidence['drugs']),
                    'diseases': self._add_diseases(evidence['disease']),
                    'evidence_sources': self._add_evidence_sources(evidence)
                }

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

    def _add_variation_descriptors(self, variant, gene):
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

        variant_query = f"{gene['name']} {variant['name']}"
        validations = self.variant_to_vrs.get_validations(variant_query)
        normalized_resp = \
            self.variant_normalizer.normalize(variant_query,
                                              validations,
                                              self.amino_acid_cache)

        variation_descriptor = schemas.VariationDescriptor(
            id=f"civic:vid{variant['id']}",
            label=variant['name'],
            description=variant['description'],
            value_id=normalized_resp.value_id,
            value=normalized_resp.value,
            gene_context=f"civic:gid{variant['gene_id']}",
            molecule_context=molecule_context,
            structural_type=structural_type,
            ref_allele_seq=re.split(r'\d+', variant['name'])[0],
            expressions=self._add_hgvs_expr(variant),
            xrefs=self._add_variant_xrefs(variant),
            alternate_labels=[v_alias for v_alias in
                              variant['variant_aliases'] if not
                              v_alias.startswith('RS')],
            extensions=[
                schemas.Extension(
                    name='representative_variation_descriptor',
                    value=[f"civic:vid{variant['id']}.rep"]
                ),
                schemas.Extension(
                    name='civic_actionability_score',
                    value=[variant['civic_actionability_score']]
                ),
                schemas.Extension(
                    name='variant_groups',
                    value=variant['variant_groups']
                )
            ]
        )

        return [variation_descriptor.dict()]

    def _add_gene_descriptors(self, gene):
        """Return gene descriptors"""
        gene_normalizer_resp = self.gene_normalizer.normalize(gene['name'],
                                                              incl='hgnc')
        gene_normalizer_resp = gene_normalizer_resp['source_matches'][0]
        if 'records' in gene_normalizer_resp and \
                gene_normalizer_resp['records']:
            gene_normalizer_resp = gene_normalizer_resp['records'][0]
        else:
            return []

        gene_descriptor = schemas.GeneDescriptor(
            id=f"civic:gid{gene['id']}",
            label=gene['name'],
            description=gene['description'],
            value=schemas.Gene(gene_id=gene_normalizer_resp.concept_id),
            alternate_labels=gene_normalizer_resp.aliases + [gene_normalizer_resp.label],  # noqa: E501
            xrefs=gene_normalizer_resp.other_identifiers,
            extensions=[]
        )

        if gene_normalizer_resp.strand:
            gene_descriptor.extensions.append(
                schemas.Extension(name='strand',
                                  value=[gene_normalizer_resp.strand]))
        if gene_normalizer_resp.previous_symbols:
            gene_descriptor.extensions.append(
                schemas.Extension(name='previous_symbols',
                                  value=gene_normalizer_resp.previous_symbols))
        if gene_normalizer_resp.xrefs:
            gene_descriptor.extensions.append(
                schemas.Extension(name='associated_with',
                                  value=gene_normalizer_resp.xrefs))
        if gene_normalizer_resp.locations:
            loc = None
            for location in gene_normalizer_resp.locations:
                loc = location.dict(by_alias=True)
                break
            gene_descriptor.extensions.append(
                schemas.Extension(name='chromosome_location',
                                  value=[loc]))
        return [gene_descriptor.dict()]

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
                schemas.Expression(syntax=syntax, value=hgvs_expr)
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


# civic = CIViCTransform()
# transformation = civic.transform()
# civic._create_json(transformation)
