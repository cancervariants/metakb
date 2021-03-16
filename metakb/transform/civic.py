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
        assertions = data['assertions']
        variants = data['variants']
        genes = data['genes']
        cdm_evidence_items = dict()
        props_and_assert_methods_ix = {
            'source_index': 1,  # Keep track of source index value
            'sources': dict(),  # {source_id: source_index}
            'proposition_index': 1,  # Keep track of proposition index value
            'propositions': dict()  # {tuple: proposition_index}
        }
        self._transform_evidence(responses, evidence_items, variants, genes,
                                 props_and_assert_methods_ix,
                                 cdm_evidence_items)
        self._transform_assertions(responses, assertions, cdm_evidence_items)

        return responses

    def _transform_evidence(self, responses, evidence_items, variants, genes,
                            props_and_assert_methods_ix, cdm_evidence_items):
        """Transform CIViC Evidence Items to CDM."""
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

            disease_descriptors = \
                self._get_disease_descriptors(evidence['disease'])
            if len(disease_descriptors) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one disease.")
                continue

            if len(evidence['drugs']) != 1:
                logger.warning(f"eid{evidence['id']} does not have exactly "
                               f"one therapy.")
                continue
            else:
                therapy_descriptors = self._get_therapy_descriptors(
                    evidence['drugs'][0])

            # TODO: Check if this should be coming from CIViC evidence or
            #  assertions. Right now using evidence.
            assertion_methods = self._get_assertion_method(evidence['source'],
                                                           props_and_assert_methods_ix)  # noqa: E501

            propositions = self._get_propositions(evidence,
                                                  variation_descriptors,
                                                  disease_descriptors,
                                                  therapy_descriptors,
                                                  props_and_assert_methods_ix)

            # We only want therapeutic response for now
            if not propositions:
                continue

            response = {
                'evidence': self._get_evidence(evidence,
                                               propositions,
                                               therapy_descriptors,
                                               disease_descriptors,
                                               assertion_methods),
                'propositions': propositions,
                'variation_descriptors': variation_descriptors,
                'therapy_descriptors': therapy_descriptors,
                'disease_descriptors': disease_descriptors,
                'assertion_methods': assertion_methods
            }
            cdm_evidence_items[f"{schemas.NamespacePrefix.CIVIC.value}:"
                               f"{evidence['name'].lower()}"] = response
            responses.append(response)

    def _transform_assertions(self, responses, assertions, cdm_evidence_items):
        """Transform CIViC Assertion records to CDM."""
        for assertion in assertions:
            eids = [f"{schemas.NamespacePrefix.CIVIC.value}:"
                    f"{evidence['name'].lower()}" for evidence in
                    assertion['evidence_items']]

            propositions = list()
            variation_descriptors = list()
            therapy_descriptors = list()
            disease_descriptors = list()

            for eid in eids:
                if not cdm_evidence_items.get(eid):
                    continue
                cdm_eid = cdm_evidence_items[eid]
                p = cdm_eid['propositions'][0]
                if p not in propositions:
                    propositions.append(p)
                v = cdm_eid['variation_descriptors'][0]
                if v not in variation_descriptors:
                    variation_descriptors.append(v)
                t = cdm_eid['therapy_descriptors'][0]
                if t not in therapy_descriptors:
                    therapy_descriptors.append(t)
                d = cdm_eid['disease_descriptors'][0]
                if d not in disease_descriptors:
                    disease_descriptors.append(d)

            if not (propositions and variation_descriptors and therapy_descriptors and disease_descriptors):  # noqa: E501
                continue

            responses.append({
                'assertion': self._get_assertion(assertion, propositions,
                                                 variation_descriptors,
                                                 therapy_descriptors,
                                                 disease_descriptors),
                'propositions': propositions,
                'variation_descriptors': variation_descriptors,
                'therapy_descriptors': therapy_descriptors,
                'disease_descriptors': disease_descriptors,
                'assertion_methods': []
            })

    def _get_assertion(self, assertion, propositions, variation_descriptors,
                       therapy_descriptors, disease_descriptors):
        """Return a list of assertions.

        :param dict assertion: Harvested CIViC assertion item record
        :param list propositions: A dict containing indexes for
            propositions and assertion methods
        :param list therapy_descriptors: A list of Therapy Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :return: A list of Assertions
        """
        evidence_level = None
        if assertion['amp_level']:
            evidence_level = f"civic.amp_level:"\
                             f"{'_'.join(assertion['amp_level'].lower().split())}"  # noqa: E501

        assertion = schemas.Assertion(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{assertion['name'].lower()}",
            description=assertion['description'],
            direction=self._get_evidence_direction(assertion['evidence_direction']),  # noqa: E501
            evidence_level=evidence_level,
            propositions=list({p['_id'] for p in propositions}),
            variation_descriptors=list({v['id'] for v in variation_descriptors}),  # noqa: E501
            therapy_descriptors=list({t['id'] for t in therapy_descriptors}),
            disease_descriptors=list({d['id'] for d in disease_descriptors}),
            assertion_methods=list()
        ).dict()
        return [assertion]

    def _get_evidence(self, evidence, propositions,
                      therapy_descriptors, disease_descriptors,
                      assertion_methods):
        """Return a list of evidence.

        :param dict evidence: Harvested CIViC evidence item record
        :param list propositions: A list of propositions
        :param list therapy_descriptors: A list of Therapy Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list assertion_methods: A list of assertion methods for the
            evidence
        :return: A list of Evidence
        """
        if assertion_methods:
            assertion_methods = [source['id'] for source in assertion_methods]
        else:
            assertion_methods = []

        evidence = schemas.Evidence(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{evidence['name'].lower()}",
            description=evidence['description'],
            direction=self._get_evidence_direction(evidence['evidence_direction']),  # noqa: E501
            evidence_level=f"civic.evidence_level:"
                           f"{evidence['evidence_level']}",
            proposition=propositions[0]['_id'],
            variation_descriptor=f"civic:vid{evidence['variant_id']}",
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            assertion_methods=assertion_methods
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
                          disease_descriptors, therapy_descriptors,
                          props_and_assert_methods_ix):
        """Return a list of propositions.

        :param dict evidence: CIViC evidence item record
        :param list variation_descriptors: A list of Variation Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list therapy_descriptors: A list of therapy_descriptors
        :param dict props_and_assert_methods_ix: A dict containing indexes for
            propositions and assertion methods
        :return: A list of propositions.
        """
        proposition_type = \
            self._get_proposition_type(evidence['evidence_type'])

        # Only want TR for now
        if proposition_type != schemas.PropositionType.PREDICTIVE.value:
            return []

        proposition = schemas.TherapeuticResponseProposition(
            _id="",
            type=proposition_type,
            predicate=self._get_predicate(proposition_type,
                                          evidence['clinical_significance']),
            variation_origin=self._get_variation_origin(evidence['variant_origin']),  # noqa: E501
            has_originating_context=variation_descriptors[0]['value_id'],
            disease_context=disease_descriptors[0]['value']['disease_id'],
            therapy=therapy_descriptors[0]['value']['therapy_id']
        ).dict(by_alias=True)

        key = (proposition['type'], proposition['predicate'],
               proposition['variation_origin'],
               proposition['has_originating_context'],
               proposition['disease_context'], proposition['therapy'])

        if props_and_assert_methods_ix['propositions'].get(key):
            proposition_index = \
                props_and_assert_methods_ix['propositions'].get(key)
        else:
            proposition_index = \
                props_and_assert_methods_ix.get('proposition_index')
            props_and_assert_methods_ix['propositions'][key] = \
                proposition_index
            props_and_assert_methods_ix['proposition_index'] += 1

        proposition['_id'] = f"proposition:{proposition_index:03}"

        return [proposition]

    def _get_proposition_type(self, evidence_type):
        """Return proposition type for a given evidence_item.

        :param str evidence_type: CIViC evidence type
        :return: A string representation of the proposition type
        """
        if evidence_type.upper() in schemas.PropositionType.__members__.keys():
            return schemas.PropositionType[evidence_type.upper()].value
        else:
            raise KeyError(f"Proposition Type {evidence_type} not found in "
                           f"schemas.PropositionType")

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

    def _get_predicate(self, proposition_type, clin_sig):
        """Return predicate for an evidence item.

        :param str proposition_type: The proposition type
        :param str clin_sig: The evidence item's clinical significance
        :return: A string representation for predicate
        """
        if clin_sig is None:
            return None
        else:
            if clin_sig == 'N/A':
                return None  # TODO: Or should we return N/A?
            clin_sig = '_'.join(clin_sig.upper().split())
            predicate = None

        if proposition_type == schemas.PropositionType.PREDICTIVE.value:
            if clin_sig == 'SENSITIVITY/RESPONSE':
                predicate = schemas.PredictivePredicate.SENSITIVITY.value
            else:
                predicate = schemas.PredictivePredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.DIAGNOSTIC.value:
            predicate = schemas.DiagnosticPredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.PROGNOSTIC.value:
            predicate = schemas.PrognosticPredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.PREDISPOSING.value:
            predicate = schemas.PredisposingPredicate.NOT_APPLICAPLE.value
        elif proposition_type == schemas.PropositionType.FUNCTIONAL.value:
            predicate = schemas.FunctionalPredicate[clin_sig].value
        else:
            logger.warning(f"{proposition_type} not supported in Predicate "
                           f"schemas.")
        return predicate

    def _get_variation_descriptors(self, variant, gene):
        """Return a list of Variation Descriptors.

        :param dict variant: A CIViC variant record
        :param dict gene: A CIViC gene record
        :return: A list of Variation Descriptors
        """
        structural_type = None
        molecule_context = None
        if len(variant['variant_types']) == 1:
            # TODO: Go through SO to find the molecule_context
            #  Is there a better way to do this?
            so_id = variant['variant_types'][0]['so_id']
            if so_id in ['SO:0001583', 'SO:0001818']:
                structural_type = 'SO:0001060'
                molecule_context = 'protein'
            elif so_id in ['SO:0001886', 'SO:0001576', 'SO:0001889']:
                structural_type = 'SO:0001060'
                molecule_context = 'transcript'
            else:
                # TODO: Genomic
                pass

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
            logger.warning("Could not find NCIt ID using Disease Normalization"
                           f" for {doid} and {display_name}.")
            return []

        return [disease_descriptor]

    def _get_therapy_descriptors(self, drug):
        """Return a list of Therapy Descriptors.
        :param dict drugs: Drugs for a given evidence_item
        :return: A list of Therapy Descriptors
        """
        therapies = schemas.ValueObjectDescriptor(
            id=f"civic:tid{drug['id']}",
            type="TherapyDescriptor",
            label=drug['name'],
            value=schemas.Therapy(therapy_id=f"ncit:{drug['ncit_id']}"),
            alternate_labels=drug['aliases']
        ).dict()
        return [therapies]

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
            if hgvs_expr != 'N/A':
                hgvs_expressions.append(
                    schemas.Expression(syntax=syntax, value=hgvs_expr)
                )
        return hgvs_expressions

    def _get_assertion_method(self, source, props_and_assert_methods_ix):
        """Return a list of Assertion Methods for an evidence_item.

        :param dict source: An evidence_item's source
        :param dict props_and_assert_methods_ix: A dict containing indexes for
            propositions and assertion methods
        :return: A list of sources
        """
        source_type = source['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
            source_id = f"{prefix}:{source['citation_id']}"

            if props_and_assert_methods_ix['sources'].get(source_id):
                source_index = \
                    props_and_assert_methods_ix['sources'].get(source_id)
            else:
                source_index = props_and_assert_methods_ix.get('source_index')
                props_and_assert_methods_ix['sources'][source_id] = \
                    source_index
                props_and_assert_methods_ix['source_index'] += 1

            source = [schemas.AssertionMethod(
                id=f"assertion_method:{source_index:03}",
                label=source['name'],
                url=source['source_url'],
                version=source['publication_date'],
                reference=source['citation']
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
