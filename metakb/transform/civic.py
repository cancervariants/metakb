"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
import re
from gene.query import QueryHandler as GeneQueryHandler
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler

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
        self.gene_query_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()
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
        data = self._extract()
        responses = list()
        evidence_items = data['evidence']
        variants = data['variants']
        genes = data['genes']
        proposition_index = 1
        sources = {
            'source_index': 1,
            'sources': dict()
        }
        for evidence in evidence_items:
            variation_descriptors = \
                self._add_variation_descriptors(self._get_record(
                    evidence['variant_id'], variants),
                    self._get_record(evidence['gene_id'], genes))
            disease_descriptors = \
                self._add_disease_descriptor(evidence['disease'])
            evidence_sources = self._add_evidence_sources(evidence,
                                                          sources)

            response = {
                'evidence': self._add_evidence(evidence, proposition_index,
                                               evidence_sources),
                'propositions': self._add_propositions(evidence,
                                                       variation_descriptors,
                                                       disease_descriptors,
                                                       proposition_index),
                'variation_descriptors': variation_descriptors,
                'therapies': self._add_therapy_descriptors(
                    evidence['drugs']),
                'disease_descriptors': disease_descriptors,
                'evidence_sources': evidence_sources
            }

            responses.append(response)
            proposition_index += 1
        return responses

    def _add_evidence(self, evidence, proposition_index, evidence_sources):
        """Add evidence to therapeutic response.

        :param dict evidence: Harvested CIViC evidence item records
        """
        if evidence_sources:
            evidence_sources = [source['_id'] for source in evidence_sources]
        else:
            evidence_sources = []
        evidence = {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:"
                  f"{evidence['name'].lower()}",
            'type': 'EvidenceLine',
            'description': evidence['description'],
            'direction':
                self._get_evidence_direction(evidence['evidence_direction']),
            'evidence_level': f"civic.evidence_level:"
                              f"{evidence['evidence_level']}",
            'proposition': f"proposition:{proposition_index:03}",
            'variation_descriptor': f"civic:vid{evidence['variant_id']}",
            'evidence_sources': evidence_sources,
            # 'contributions': [],  # TODO: After MetaKB first pass
        }
        return [evidence]

    def _get_evidence_direction(self, direction):
        """Return the evidence direction.

        :param str direction: The civic evidence_direction value
        :return: `supports` or `does_not_support` or None
        """
        if direction == 'Supports':
            return schemas.Direction.SUPPORTS.value
        elif direction == 'Does Not Support':
            return schemas.Direction.DOES_NOT_SUPPORT
        else:
            # TODO: Should we support 'N/A'
            return None

    def _add_propositions(self, evidence, variation_descriptors,
                          disease_descriptors, proposition_index):
        """Add proposition to response.

        :param dict evidence: CIViC evidence item record
        """
        variation_id = f"civic:vid{evidence['variant_id']}"
        has_originating_context = None
        for v in variation_descriptors:
            if v['value_id'] and v['id'] == variation_id:
                has_originating_context = v['value_id']

        disease_context = None
        if len(disease_descriptors) > 0:
            disease_context = disease_descriptors[0]['value']['disease_id']

        therapies = []
        for drug in evidence['drugs']:
            if drug['ncit_id']:
                therapies.append(f"ncit:{drug['ncit_id']}")

        proposition = {
            '_id': f'proposition:{proposition_index:03}',
            'type': 'therapeutic_response_proposition' if therapies else None,
            'has_originating_context': has_originating_context,
            'therapies': therapies,
            'disease_context': disease_context,
            'predicate': self._get_predicate(evidence),
            'variant_origin':
                self._get_variant_origin(evidence['variant_origin'])
        }

        return [proposition]

    def _get_variant_origin(self, variant_origin):
        """Return variant origin."""
        if variant_origin == 'Somatic':
            origin = schemas.VariationOrigin.SOMATIC.value
        elif variant_origin == 'Rare Germline':
            origin = schemas.VariationOrigin.RARE_GERMLINE.value
        elif variant_origin == 'Common Germline':
            origin = schemas.VariationOrigin.COMMON_GERMLINE.value
        elif variant_origin == 'N/A':
            origin = schemas.VariationOrigin.NOT_APPLICABLE.value
        elif variant_origin == 'Unknown':
            origin = schemas.VariationOrigin.UNKNOWN.value
        else:
            origin = None
        return origin

    def _get_predicate(self, evidence):
        """Return predicate."""
        predicate = None
        if evidence['evidence_type'] == 'Predictive':
            e_clin_sig = evidence['clinical_significance']
            if e_clin_sig == 'Sensitivity/Response':
                predicate = 'predicts_sensitivity_to'
            elif e_clin_sig == 'Resistance':
                predicate = 'predicts_resistance_to'
            elif e_clin_sig == 'Reduced Sensitivity':
                predicate = 'predicts_reduced_sensitivity_to'
            elif e_clin_sig == 'Adverse Response':
                predicate = 'predicts_adverse_response_to'
            else:
                # TODO: Support for other clinical_significance ?
                #  'Resistance', 'Sensitivity/Response', 'N/A', 'Poor Outcome',
                #  'Positive', 'Better Outcome', 'Adverse Response',
                #  'Uncertain Significance', 'Likely Pathogenic', 'Negative',
                #  'Loss of Function', 'Gain of Function', 'Neomorphic',
                #  'Pathogenic', 'Dominant Negative', 'Unaltered Function',
                #  None, 'Reduced Sensitivity', 'Unknown'
                pass
        else:
            # TODO: Support for other evidence_type values ?
            #  'Prognostic', 'Diagnostic', 'Predisposing', 'Functional'
            pass
        return predicate

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

        try:
            validations = self.variant_to_vrs.get_validations(variant_query)
        except:  # noqa: E722
            logger.error(f"toVRS: {variant_query}")
            return []
        normalized_resp = \
            self.variant_normalizer.normalize(variant_query,
                                              validations,
                                              self.amino_acid_cache)

        if not normalized_resp:
            # TODO: Maybe we can search on the hgvs expression??
            logger.warning(f"{variant_query} is not yet supported in"
                           f" Variant Normalization normalize.")
            return []

        variation_descriptor = schemas.VariationDescriptor(
            id=f"civic:vid{variant['id']}",
            label=variant['name'],
            description=variant['description'],
            value_id=normalized_resp.value_id,
            value=normalized_resp.value,
            gene_context=self._add_gene_descriptor(gene),
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
                    value=f"civic:vid{variant['id']}.rep"
                ),
                schemas.Extension(
                    name='civic_actionability_score',
                    value=variant['civic_actionability_score']
                ),
                schemas.Extension(
                    name='variant_groups',
                    value=variant['variant_groups']
                )
            ]
        )

        return [variation_descriptor.dict()]

    def _add_gene_descriptor(self, gene):
        """Return gene descriptors"""
        gene_descriptor = schemas.GeneDescriptor(
            id=f"civic:gid{gene['id']}",
            label=gene['name'],
            description=gene['description'] if gene['description'] else None,
            value=schemas.Gene(gene_id=f"ncbigene:{gene['entrez_id']}"),
            alternate_labels=gene['aliases']
        )
        return gene_descriptor.dict()

    def _add_disease_descriptor(self, disease):
        """Return disease descriptor."""
        doid = f"doid:{disease['doid']}"
        disease_norm_resp = self.disease_query_handler.search_groups(doid)

        display_name = disease['display_name']
        if disease_norm_resp['match_type'] == 0:
            disease_norm_resp = \
                self.disease_query_handler.search_groups(display_name)

        if disease_norm_resp['match_type'] == 0:
            logger.warning(f"{doid}: {display_name} not found in Disease "
                           f"Normalization normalize.")
            return []

        disease_norm_vod = disease_norm_resp['value_object_descriptor']

        disease_descriptor = schemas.ValueObjectDescriptor(
            id=f"civic:did{disease['id']}",
            type="DiseaseDescriptor",
            label=display_name,
            value=schemas.Disease(disease_id=disease_norm_vod['value']['disease_id']),  # noqa: E501
            xrefs=disease_norm_vod['xrefs'] if 'xrefs' in disease_norm_vod else None,  # noqa: E501
            alternate_labels=disease_norm_vod['alternate_labels'] if 'alternate_labels' in disease_norm_vod else None  # noqa: E501
        )

        return [disease_descriptor.dict()]

    def _add_therapy_descriptors(self, drugs):
        """Return therapy descriptor."""
        therapies = list()
        for drug in drugs:
            found_match = False
            drug_ncit_id = f"ncit:{drug['id']}"
            drug_label = drug['name']
            drug_aliases = drug['aliases']
            xrefs = list()

            # Find highest match from therapy normalizer
            for search_record in [drug_ncit_id, drug_label] + drug_aliases:
                therapy_norm_resp = \
                    self.therapy_query_handler.search_groups(search_record)

                if therapy_norm_resp['match_type'] != 0:
                    found_match = True
                    if 'xrefs' in therapy_norm_resp['value_object_descriptor']:
                        xrefs = [xref for xref in therapy_norm_resp['value_object_descriptor']['xrefs'] if not xref.startswith('ncit')]  # noqa: E501

                    therapy_id = therapy_norm_resp['value_object_descriptor']['value']['therapy_id']  # noqa: E501
                    if not therapy_id.startswith('ncit'):
                        xrefs.append(therapy_id)
                    break

            if found_match:
                therapies.append(schemas.ValueObjectDescriptor(
                    id=f"civic:tid{drug['id']}",
                    type="TherapyDescriptor",
                    label=drug_label,
                    value=schemas.Therapy(therapy_id=drug_ncit_id),
                    alternate_labels=drug_aliases,
                    xrefs=xrefs
                ).dict())
            else:
                logger.warning(f"{drug_ncit_id}: {drug_label} had no match "
                               f"in Therapy Normalizer.")
        return therapies

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

    def _add_evidence_sources(self, evidence, sources):
        """Add evidence source to response.

        :param dict evidence: A CIViC evidence item record
        """
        source_type = evidence['source']['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
            source_id = f"{prefix}:{evidence['source']['citation_id']}"

            if sources['sources'].get(source_id):
                source_index = sources['sources'].get(source_id)
                sources['sources'] = {
                    source_id: source_index
                }
            else:
                source_index = sources.get('source_index') + 1

            source = [{
                '_id': f"source:{source_index:03}",
                'id': source_id,
                'label': evidence['source']['citation'],
                'description': evidence['source']['name'],
                'xrefs': []
            }]
        else:
            source = None
            logger.warning(f"{source_type} not in schemas.SourcePrefix")

        return source

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
