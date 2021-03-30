"""A module to convert MOA resources to common data model"""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
from gene.query import QueryHandler as GeneQueryHandler
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler
from urllib.parse import quote

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class MOATransform:
    """A class for transforming MOA resources to common data model."""

    def __init__(self,
                 file_path=f"{PROJECT_ROOT}/data/moa/moa_harvester.json"):
        """
        Initialize MOATransform class

        :param: The file path to the harvested json to transform
        """
        self.file_path = file_path
        self.gene_query_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()

    def _extract(self):
        """Extract the MOA harvested data file."""
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _create_json(self, transformations):
        """Create a JSON for the transformed MOA data."""
        moa_dir = PROJECT_ROOT / 'data' / 'moa' / 'transform'
        moa_dir.mkdir(exist_ok=True, parents=True)

        with open(f"{moa_dir}/moa_cdm.json", 'w+') as f:
            json.dump(transformations, f)

    def transform(self):
        """Transform MOA harvested JSON to common date model

        :return: A list of dictinaries containing transformations to CDM.
        """
        data = self._extract()
        responses = []
        cdm_assertions = {}  # assertions that have been transformed to CDM

        assertions = data['assertions']
        sources = data['sources']
        variants = data['variants']
        propositions_support_evidence_ix = {
            # Keep track of support_evidence index value
            'support_evidence_index': 1,
            # {support_evidence_id: support_evidence_index}
            'support_evidence': dict(),
            # Keep track of proposition index value
            'proposition_index': 1,
            # {tuple: proposition_index}
            'propositions': dict()
        }

        # Transform MOA assertions
        self._transform_statements(responses, assertions, variants,
                                   sources, propositions_support_evidence_ix,
                                   cdm_assertions)

        return responses

    def _transform_statements(self, responses, records, variants,
                              sources, propositions_support_evidence_ix,
                              cdm_assertions):
        """Add transformed assertions to the response list.

        :param: A list of dicts containing assertions
        :param: A list of MOA assertion records
        :param: A dict of MOA variant records
        :param: A dict of MOA source records
        :param: Keeps track of proposition and support_evidence indexes
        :param: A dict containing assertions that have been
            transformed to the CDM
        """
        for record in records:
            gene_descriptors = self._get_gene_descriptors(
                self._get_record(record['variant']['id'], variants))
            descriptors = \
                self._get_descriptors(record, variants, gene_descriptors)
            if not descriptors:
                continue
            else:
                therapy_descriptors, variation_descriptors, disease_descriptors = descriptors  # noqa: E501

            propositions = \
                self._get_tr_propositions(record, variation_descriptors,
                                          disease_descriptors,
                                          therapy_descriptors,
                                          propositions_support_evidence_ix)

            # We only want therapeutic response for now
            if not propositions:
                continue

            support_evidence = self._get_support_evidence(
                self._get_record(record['source_ids'][0], sources),
                propositions_support_evidence_ix)

            methods = self._get_method()
            statements = self._get_statement(record, propositions,
                                             variation_descriptors,
                                             therapy_descriptors,
                                             disease_descriptors,
                                             methods, support_evidence)

            response = schemas.Response(
                statements=statements,
                propositions=propositions,
                variation_descriptors=variation_descriptors,
                gene_descriptors=gene_descriptors,
                therapy_descriptors=therapy_descriptors,
                disease_descriptors=disease_descriptors,
                methods=methods,
                support_evidence=support_evidence
            ).dict(by_alias=True)

            cdm_assertions[f"assertion_{record['id']}"] = response
            responses.append(response)

    def _get_descriptors(self, record, variants, gene_descriptors):
        """Return tuple of descriptors if one exists for each type.

        :param: A MOA assertion
        :param: MOA variant records
        :param: The corresponding gene descriptors
        :return: Descriptors
        """
        therapy_descriptors = self._get_therapy_descriptors(record)
        variation_descriptors = self._get_variation_descriptors(
            self._get_record(record['variant']['id'], variants),
            gene_descriptors)
        disease_descriptors = \
            self._get_disease_descriptors(record)

        if len(therapy_descriptors) != 1:
            logger.warning(f"Therapy {record['therapy_name']} "
                           f"could not be found in therapy normalizer.")
            return None

        if len(variation_descriptors) != 1:
            logger.warning(f"Variant {record['variant']['feature']} "
                           f"could not be found in variant normalizer.")
            return None

        if len(disease_descriptors) != 1:
            logger.warning(f"Disease {record['disease']['name']}"
                           f" could not be found in disease normalizer.")
            return None

        return therapy_descriptors, variation_descriptors, disease_descriptors

    def _get_statement(self, record, propositions, variant_descriptors,
                       therapy_descriptors, disease_descriptors,
                       methods, support_evidence):
        """Get a statement for an assertion.
        :param dict record: A MOA assertion record
        :param list propositions: Propositions for the record
        :param list variant_descriptors: Variant Descriptors for the record
        :param list therapy_descriptors: Therapy Descriptors for the record
        :param list disease_descriptors: Disease Descriptors for the record
        :param list methods: Assertion methods for the record
        :param list support_evidence: Supporting evidence for the rcord
        :return: A list of statement
        """
        therapy_descriptor = therapy_descriptors[0]['id'] \
            if therapy_descriptors else None
        disease_descriptor = disease_descriptors[0]['id'] \
            if disease_descriptors else None

        statement = schemas.Statement(
            id=f"{schemas.NamespacePrefix.MOA.value}:"
               f"{record['id']}",
            description=record['description'],
            evidence_level=f"moa.evidence_level:"
                           f"{record['predictive_implication']}",
            proposition=propositions[0]['_id'],
            variation_descriptor=variant_descriptors[0]['id'],
            therapy_descriptor=therapy_descriptor,
            disease_descriptor=disease_descriptor,
            method=methods[0]['id'],
            support_evidence=[se['id'] for se in support_evidence]
        ).dict()

        return [statement]

    def _get_tr_propositions(self, record, variation_descriptors,
                             disease_descriptors, therapy_descriptors,
                             propositions_support_evidence_ix):
        """Return a list of propositions.

        :param: MOA assertion
        :param: A list of Variation Descriptors
        :param: A list of Disease Descriptors
        :param: A list of therapy_descriptors
        :param: Keeps track of proposition and support_evidence indexes
        :return: A list of therapeutic propositions.
        """
        object_qualifier = disease_descriptors[0]['value']['disease_id'] \
            if disease_descriptors else None
        therapy = therapy_descriptors[0]['value']['therapy_id'] \
            if therapy_descriptors else None
        predicate = self._get_predicate(record['clinical_significance'])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return []

        proposition = schemas.TherapeuticResponseProposition(
            _id="",
            type="therapeutic_response_proposition",
            predicate=predicate,
            variant_origin=self._get_variation_origin(record['variant']),
            subject=variation_descriptors[0]['value_id'],
            object_qualifier=object_qualifier,
            object=therapy
        ).dict(by_alias=True)

        # Get corresponding id for proposition
        key = (proposition['type'],
               proposition['predicate'],
               proposition['variation_origin'],
               proposition['subject'],
               proposition['object_qualifier'],
               proposition['object'])

        proposition_index = self._set_ix(propositions_support_evidence_ix,
                                         'propositions', key)
        proposition['_id'] = f"proposition:{proposition_index:03}"

        return [proposition]

    def _get_predicate(self, clin_sig):
        """Get the predicate of this record

        :param: clinical significance of the assertion
        :return: predicate
        """
        predicate = None
        if not clin_sig:
            return None
        if clin_sig.upper() in schemas.PredictivePredicate.__members__.keys():
            predicate = schemas.PredictivePredicate[clin_sig.upper()].value

        return predicate

    def _get_variation_origin(self, variant):
        """Return variant origin.

        :param: A MOA variant record
        :return: A str representation of variation origin
        """
        if variant['feature_type'] == 'somatic_variant':
            origin = schemas.VariationOrigin.SOMATIC.value
        elif variant['feature_type'] == 'germline_variant':
            origin = schemas.VariationOrigin.GERMLINE.value
        else:
            origin = None

        return origin

    def _get_variation_descriptors(self, variant, g_descriptors):
        """Add variation descriptor to therapeutic response

        :param: single assertion record from MOA
        :return: list of variation descriptor
        """
        ref_allele_seq = variant['protein_change'][2] \
            if 'protein_change' in variant and variant['protein_change'] else None  # noqa: E501

        structural_type, molecule_context = None, None
        if 'variant_annotation' in variant:
            if variant['variant_annotation'] == 'Missense':
                structural_type = "SO:0001606"
                molecule_context = 'protein'

        v_norm_resp = None
        # For now, the normalizer only support a.a substitution
        if g_descriptors and 'protein_change' in variant and variant['protein_change']:  # noqa: E501
            gene = g_descriptors[0]['label']
            query = f"{gene} {variant['protein_change'][2:]}"
            try:
                validations = self.variant_to_vrs.get_validations(query)
                v_norm_resp = \
                    self.variant_normalizer.normalize(query,
                                                      validations,
                                                      self.amino_acid_cache)
            except:  # noqa: E722
                logger.warning(f"{query} not supported in variant-normalizer.")

        if not v_norm_resp:
            logger.warn(f"variant-normalizer does not support "
                        f"moa:vid{variant['id']}.")
            return []

        gene_context = g_descriptors[0]['id'] if g_descriptors else None

        variation_descriptor = schemas.VariationDescriptor(
            id=f"moa:vid{variant['id']}",
            label=variant['feature'],
            value_id=v_norm_resp.value_id,
            value=v_norm_resp.value,
            gene_context=gene_context,
            molecule_context=molecule_context,
            structural_type=structural_type,
            ref_allele_seq=ref_allele_seq,
        ).dict()

        return [variation_descriptor]

    def _get_gene_descriptors(self, variant):
        """Return a Gene Descriptor.

        :param: A MOA variant record
        :return: A Gene Descriptor
        """
        genes = [value for key, value in variant.items()
                 if key.startswith('gene')]
        genes = list(filter(None, genes))

        gene_descriptors = []  # for fusion protein, we would include both genes  # noqa: E501
        if genes:
            for gene in genes:
                found_match = False
                gene_norm_resp = \
                    self.gene_query_handler.search_sources(gene, incl='HGNC')
                if gene_norm_resp['source_matches']:
                    if gene_norm_resp['source_matches'][0]['match_type'] != 0:
                        found_match = True
                gene_norm_resp = gene_norm_resp['source_matches'][0]

                if found_match:
                    gene_descriptor = schemas.GeneDescriptor(
                        id=f"normalize.{schemas.NormalizerPrefix.GENE.value}."
                           f"{schemas.NamespacePrefix.MOA.value}:{quote(gene)}",  # noqa: E501
                        label=gene,
                        value=schemas.Gene(gene_id=gene_norm_resp['records'][0].concept_id),  # noqa: E501
                    ).dict()
                else:
                    gene_descriptor = {}

                gene_descriptors.append(gene_descriptor)

        return gene_descriptors

    def _get_support_evidence(self, source, propositions_support_evidence_ix):
        """Get an assertion's support evidence.

        :param: An evidence source
        :param: Keeps track of proposition and support_evidence indexes
        """
        support_evidence = None
        if source['pmid']:
            support_evidence_id = f"pmid:{source['pmid']}"
        else:
            support_evidence_id = source['url']

        support_evidence_ix = self._set_ix(propositions_support_evidence_ix,
                                           'support_evidence',
                                           support_evidence_id)

        support_evidence = schemas.SupportEvidence(
            id=f"support_evidence:{support_evidence_ix:03}",
            support_evidence_id=support_evidence_id,
            label=source['citation']
        ).dict()

        return [support_evidence]

    def _get_method(self):
        """Get methods for a given record.

        :return: A list of methods
        """
        methods = [schemas.Method(
            id=f'method:'
               f'{schemas.MethodID.MOA_ASSERTION_BIORXIV:03}',
            label='Clinical interpretation of integrative molecular profiles to guide precision cancer medicine',  # noqa:E501
            url='https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1',  # noqa:E501
            version=schemas.Date(year=2020, month=9, day=22),
            reference='Reardon, B., Moore, N.D., Moore, N. et al.'
        ).dict()]

        return methods

    def _get_therapy_descriptors(self, assertion):
        """Return a list of Therapy Descriptors.

        :param: an MOA assertion record
        :return: A list of Therapy Descriptors
        """
        therapy = assertion['therapy_name']
        t_handler_resp = None

        if not therapy:
            return []
        t_handler_resp = self.therapy_query_handler.search_groups(therapy)

        if not t_handler_resp or t_handler_resp['match_type'] == 0:
            logger.warning(f"{therapy} not found in Therapy "
                           f"Normalization normalize.")
            return []

        t_handler_resp = t_handler_resp['value_object_descriptor']

        therapy_norm_id = \
            t_handler_resp['value']['therapy_id']

        # TODO: RxNorm is highest priority, but in example listed NCIt?
        if not therapy_norm_id.startswith('ncit'):
            therapy_norm_id = None
            if 'xrefs' in t_handler_resp:
                for other_id in t_handler_resp['xrefs']:
                    if other_id.startswith('ncit:'):
                        therapy_norm_id = other_id

        if therapy_norm_id:
            therapy_descriptor = schemas.ValueObjectDescriptor(
                id=t_handler_resp['id'],
                type="TherapyDescriptor",
                label=therapy,
                value=schemas.Therapy(therapy_id=therapy_norm_id)
            ).dict()
        else:
            return []

        return [therapy_descriptor]

    def _get_disease_descriptors(self, assertion):
        """Return A list of Disease Descriptors.

        :param: an MOA assertion record
        :return: A list of Therapy Descriptors
        """
        ot_code = assertion['disease']['oncotree_code']
        disease_name = assertion['disease']['name']
        d_handler_resp = None

        for query in [ot_code, disease_name]:
            if not query:
                continue

            d_handler_resp = self.disease_query_handler.search_groups(query)
            if d_handler_resp['match_type'] != 0:
                break

        if not d_handler_resp or d_handler_resp['match_type'] == 0:
            logger.warning(f"{ot_code} and {disease_name} not found in "
                           f"Disease Normalization normalize.")
            return []

        d_handler_resp = d_handler_resp['value_object_descriptor']
        disease_norm_id = d_handler_resp['value']['disease_id']

        if disease_norm_id.startswith('ncit:'):
            disease_descriptor = schemas.ValueObjectDescriptor(
                id=d_handler_resp['id'],
                type="DiseaseDescriptor",
                label=disease_name,
                value=schemas.Disease(disease_id=disease_norm_id),
            ).dict()
        else:
            # TODO: Should we accept other disease_ids other than NCIt?
            logger.warning("Could not find NCIt ID using Disease Normalization"
                           f" for {ot_code} and {disease_name}.")
            return []

        return [disease_descriptor]

    def _get_record(self, record_id, records):
        """Get a MOA record by ID.

        :param: The ID of the record we are searching for
        :param: A dict of records for a given MOA record type
        """
        for r in records:
            if r['id'] == record_id:
                return r

    def _set_ix(self, propositions_support_evidence_ix, dict_key, search_key):
        """Set indexes for support_evidence or propositions.

        :param dict propositions_support_evidence_ix: Keeps track of
            proposition and support_evidence indexes
        :param str dict_key: 'sources' or 'propositions'
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        if dict_key == 'support_evidence':
            dict_key_ix = 'support_evidence_index'
        elif dict_key == 'propositions':
            dict_key_ix = 'proposition_index'
        else:
            raise KeyError("dict_key can only be `support_evidence` or "
                           "`propositions`.")
        if propositions_support_evidence_ix[dict_key].get(search_key):
            index = propositions_support_evidence_ix[dict_key].get(search_key)
        else:
            index = propositions_support_evidence_ix.get(dict_key_ix)
            propositions_support_evidence_ix[dict_key][search_key] = index
            propositions_support_evidence_ix[dict_key_ix] += 1
        return index
