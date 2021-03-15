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

        :param str file_path: The file path to the harvested json to transform.
        """
        self._file_path = file_path
        self.gene_query_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()

    def _extract(self):
        """Extract the CIViC harvested data file."""
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _create_json(self, transformations):
        """Create a JSON for the transformed CIViC data."""
        civic_dir = PROJECT_ROOT / 'data' / 'civic' / 'transform'
        civic_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{civic_dir}/civic_cdm.json", 'w+') as f:
            json.dump(transformations, f)

    def transform(self):
        """Transform CIViC harvested json to common data model.

        :return: A list of dictionaries containing transformations to CDM.
        """
        data = self._extract()
        responses = list()
        evidence_items = data['evidence']
        variants = data['variants']
        genes = data['genes']
        proposition_index = 1  # Keep track of proposition index
        sources = {
            'source_index': 1,  # Keep track of source index value
            'sources': dict()  # source_id: source_index
        }

        for evidence in evidence_items:
            # We only want to include evidence_items that have exactly one
            # variation, disease, and therapy
            variation_descriptors = \
                self._get_variation_descriptors(self._get_record(
                    evidence['variant_id'], variants),
                    self._get_record(evidence['gene_id'], genes))

            if len(variation_descriptors) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one variant.")
                continue

            gene_descriptors = self._get_gene_descriptors(
                self._get_record(evidence['gene_id'], genes))
            if len(gene_descriptors) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one gene.")
                continue

            disease_descriptors = \
                self._get_disease_descriptors(evidence['disease'])
            if len(disease_descriptors) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one disease.")
                continue

            therapy_descriptors = self._get_therapy_descriptors(
                evidence['drugs'])
            if len(therapy_descriptors) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one therapy.")
                continue

            evidence_sources = self._get_evidence_sources(evidence,
                                                          sources)

            response = {
                'evidence': self._get_evidence(evidence, proposition_index,
                                               therapy_descriptors,
                                               disease_descriptors,
                                               gene_descriptors,
                                               evidence_sources),
                'propositions': self._get_propositions(evidence,
                                                       variation_descriptors,
                                                       gene_descriptors,
                                                       disease_descriptors,
                                                       therapy_descriptors,
                                                       proposition_index),
                'variation_descriptors': variation_descriptors,
                'gene_descriptors': gene_descriptors,
                'therapy_descriptors': therapy_descriptors,
                'disease_descriptors': disease_descriptors,
                'evidence_sources': evidence_sources
            }

            responses.append(response)
            proposition_index += 1
        return responses

    def _get_evidence(self, evidence, proposition_index, therapy_descriptors,
                      disease_descriptors, gene_descriptors, evidence_sources):
        """Return a list of evidence.

        :param dict evidence: Harvested CIViC evidence item records
        :param int proposition_index: Index for proposition
        :param list therapy_descriptors: A list of Therapy Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list gene_descriptors: A list of Gene Descriptors
        :param list evidence_sources: A list of sources for the evidence
        :return: A list of Evidence
        """
        if evidence_sources:
            evidence_sources = [source['id'] for source in evidence_sources]
        else:
            evidence_sources = []

        evidence = schemas.Evidence(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{evidence['name'].lower()}",
            description=evidence['description'],
            direction=self._get_evidence_direction(evidence['evidence_direction']),  # noqa: E501
            evidence_level=f"civic.evidence_level:"
                           f"{evidence['evidence_level']}",
            proposition=f"proposition:{proposition_index:03}",
            variation_descriptor=f"civic:vid{evidence['variant_id']}",
            gene_descriptor=gene_descriptors[0]['id'],
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            evidence_sources=evidence_sources
        ).dict()
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

    def _get_propositions(self, evidence, variation_descriptors,
                          gene_descriptors, disease_descriptors,
                          therapy_descriptors, proposition_index):
        """Return a list of propositions.

        :param dict evidence: CIViC evidence item record
        :param list variation_descriptors: A list of Variation Descriptors
        :param list gene_descriptors: A list of Gene Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list therapy_descriptors: A list of therapy_descriptors
        :param int proposition_index: The index for the proposition
        :return: A list of propositions.
        """
        proposition = schemas.TherapeuticResponseProposition(
            _id=f'proposition:{proposition_index:03}',
            type='therapeutic_response_proposition',  # TODO: Check
            predicate=self._get_predicate(evidence),
            variation_origin=self._get_variation_origin(evidence['variant_origin']),  # noqa: E501
            has_originating_context=variation_descriptors[0]['value_id'],
            gene=gene_descriptors[0]['value']['gene_id'],
            disease_context=disease_descriptors[0]['value']['disease_id'],
            therapy=therapy_descriptors[0]['value']['therapy_id']
        ).dict()

        return [proposition]

    def _get_variation_origin(self, variant_origin):
        """Return variant origin.

        :param str variant_origin: CIViC variant origin
        :return: A str representation of variation origin
        """
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
        """Return predicate for an evidence item.
        :param dict evidence: A CIViC evidence_item
        :return: A string representation for predicate
        """
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

    def _get_variation_descriptors(self, variant, gene):
        """Return a list of Variation Descriptors.

        :param dict variant: A CIViC variant record
        :param dict gene: A CIViC gene record
        :return: A list of Variation Descriptors
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
            gene_context=f"civic:gid{gene['id']}",
            molecule_context=molecule_context,
            structural_type=structural_type,
            ref_allele_seq=re.split(r'\d+', variant['name'])[0],
            expressions=self._get_hgvs_expr(variant),
            xrefs=self._get_variant_xrefs(variant),
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
        ).dict()
        return [variation_descriptor]

    def _get_variant_xrefs(self, v):
        """Return a list of xrefs for a variant.

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

    def _get_gene_descriptors(self, gene):
        """Return a list of Gene Descriptors.

        :param dict gene: A CIViC gene record
        :return A list of Gene Descriptor
        """
        found_match = False
        for query_str in [f"ncbigene:{gene['entrez_id']}", gene['name']] + gene['aliases']:  # noqa: E501
            gene_norm_resp = \
                self.gene_query_handler.search_sources(query_str, incl="hgnc")
            if gene_norm_resp['source_matches']:
                if gene_norm_resp['source_matches'][0]['match_type'] != 0:
                    found_match = True
                    break

        if found_match:
            gene_descriptor = [schemas.GeneDescriptor(
                id=f"civic:gid{gene['id']}",
                label=gene['name'],
                description=gene['description'] if gene['description'] else None,  # noqa: E501
                value=schemas.Gene(gene_id=gene_norm_resp['source_matches'][0]['records'][0].concept_id),  # noqa: E501
                alternate_labels=gene['aliases']
            ).dict()]
        else:
            gene_descriptor = []

        return gene_descriptor

    def _get_disease_descriptors(self, disease):
        """Return A list of Disease Descriptors.
        :param dict disease: A CIViC disease record
        :return: A list of Disease Descriptors.
        """
        if not disease['doid']:
            logger.warning(f"CIViC {disease['id']} has null DOID.")
            return []

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

        disease_norm_id = \
            disease_norm_resp['value_object_descriptor']['value']['disease_id']

        if disease_norm_id.startswith('ncit:'):
            disease_descriptor = schemas.ValueObjectDescriptor(
                id=f"civic:did{disease['id']}",
                type="DiseaseDescriptor",
                label=display_name,
                value=schemas.Disease(disease_id=disease_norm_id),
            ).dict()
        else:
            # TODO: Should we accept other disease_ids other than NCIt?
            logger.warning("Could not NCIt ID using Disease Normalization "
                           f"for {doid} or {display_name}.")
            return []

        return [disease_descriptor]

    def _get_therapy_descriptors(self, drugs):
        """Return a list of Therapy Descriptors.
        :param dict drugs: Drugs for a given evidence_item
        :return: A list of Therapy Descriptors
        """
        therapies = list()
        if len(drugs) != 1:
            return therapies

        for drug in drugs:
            therapies.append(schemas.ValueObjectDescriptor(
                id=f"civic:tid{drug['id']}",
                type="TherapyDescriptor",
                label=drug['name'],
                value=schemas.Therapy(therapy_id=f"ncit:{drug['ncit_id']}"),
                alternate_labels=drug['aliases']
            ).dict())
        return therapies

    def _get_hgvs_expr(self, variant):
        """Return a list of hgvs expressions for a given variant.

        :param dict variant: A CIViC variant record
        :return a list of hgvs expressions
        """
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

    def _get_evidence_sources(self, evidence, sources):
        """Return a list of sources for a given evidence item.

        :param dict evidence: A CIViC evidence item record
        :param dict sources: A dict containing the source_index and existing
            sources
        :return: A list of sources
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

            source = [schemas.EvidenceSource(
                id=f"source:{source_index:03}",
                source_id=source_id,
                label=evidence['source']['citation'],
                description=evidence['source']['name'],
                xrefs=[]
            ).dict()]
        else:
            source = []
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
