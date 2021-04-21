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
        Initialize VICC normalizers and class attributes

        :param: The file path to the harvested json to transform
        """
        self.file_path = file_path
        self.gene_query_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()
        self.statements = list()
        self.propositions = list()
        self.variation_descriptors = list()
        self.gene_descriptors = list()
        self.therapy_descriptors = list()
        self.disease_descriptors = list()
        self.methods = list()
        self.documents = list()

    def _extract(self):
        """Extract the MOA harvested data file."""
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _create_json(self,
                     moa_dir=PROJECT_ROOT / 'data' / 'moa' / 'transform',
                     fn='moa_cdm.json'):
        """Create a composite JSON for the transformed MOA data.

        :param path moa_dir: The moa transform data directory
        :param str fn: The file name for the transformed data
        """
        moa_dir.mkdir(exist_ok=True, parents=True)

        composite_dict = {
            'statements': self.statements,
            'propositions': self.propositions,
            'variation_descriptors': self.variation_descriptors,
            'gene_descriptors': self.gene_descriptors,
            'therapy_descriptors': self.therapy_descriptors,
            'disease_descriptors': self.disease_descriptors,
            'methods': self.methods,
            'documents': self.documents
        }

        with open(f"{moa_dir}/{fn}", 'w+') as f:
            json.dump(composite_dict, f)

    def transform(self, propositions_ix=None):
        """Transform MOA harvested JSON to common date model.

        :param Dict propositions_ix: tracking data to properly
            index SupportEvidence
        :return: An updated propositions_ix object
        """
        data = self._extract()
        cdm_assertions = {}  # assertions that have been transformed to CDM

        assertions = data['assertions']
        sources = data['sources']
        variants = data['variants']
        if not propositions_ix:
            propositions_ix = {
                # Keep track of proposition index value
                'proposition_index': 1,
                # {tuple: proposition_index}
                'propositions': dict()
            }

        # Transform MOA assertions
        self._transform_statements(assertions, variants, sources,
                                   propositions_ix, cdm_assertions)
        return propositions_ix

    def _transform_statements(self, records, variants, sources,
                              propositions_ix, cdm_assertions):
        """Add transformed assertions to the response list.

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
                                          propositions_ix)

            # We only want therapeutic response for now
            if not propositions:
                continue

            documents = self._get_documents(
                self._get_record(record['source_ids'][0], sources))

            methods = self._get_method()
            statements = self._get_statement(record, propositions,
                                             variation_descriptors,
                                             therapy_descriptors,
                                             disease_descriptors,
                                             methods, documents)

            response = schemas.Response(
                statements=statements,
                propositions=propositions,
                variation_descriptors=variation_descriptors,
                gene_descriptors=gene_descriptors,
                therapy_descriptors=therapy_descriptors,
                disease_descriptors=disease_descriptors,
                methods=methods,
                documents=documents
            ).dict(exclude_none=True)

            cdm_assertions[f"moa:assertion_{record['id']}"] = response

            for field in ['statements', 'propositions',
                          'variation_descriptors', 'gene_descriptors',
                          'therapy_descriptors', 'disease_descriptors',
                          'methods', 'documents']:
                attr = getattr(self, field)
                var = response[field]
                for el in var:
                    if el not in attr:
                        attr.append(el)

    def _get_descriptors(self, record, variants, gene_descriptors):
        """Return tuple of descriptors if one exists for each type.

        :param: A MOA assertion record
        :param: MOA variant records
        :param: The corresponding gene descriptors
        :return: a tuple Descriptors
        """
        therapy_descriptors = self._get_therapy_descriptors(record)
        if len(therapy_descriptors) != 1:
            logger.warning(f"Therapy {record['therapy_name']} "
                           f"could not be found in therapy normalizer.")
            return None

        variation_descriptors = self._get_variation_descriptors(
            self._get_record(record['variant']['id'], variants),
            gene_descriptors)
        if len(variation_descriptors) != 1:
            logger.warning(f"Variant {record['variant']['feature']} "
                           f"could not be found in variant normalizer.")
            return None

        disease_descriptors = self._get_disease_descriptors(record)
        if len(disease_descriptors) != 1:
            logger.warning(f"Disease {record['disease']['name']}"
                           f" could not be found in disease normalizer.")
            return None

        return therapy_descriptors, variation_descriptors, disease_descriptors

    def _get_statement(self, record, propositions, variant_descriptors,
                       therapy_descriptors, disease_descriptors,
                       methods, documents):
        """Get a statement for an assertion.

        :param dict record: A MOA assertion record
        :param list propositions: Propositions for the record
        :param list variant_descriptors: Variant Descriptors for the record
        :param list therapy_descriptors: Therapy Descriptors for the record
        :param list disease_descriptors: Disease Descriptors for the record
        :param list methods: Assertion methods for the record
        :param list documents: Supporting evidence for the rcord
        :return: A list of statement
        """
        evidence_level = record['predictive_implication'].strip().replace(' ', '_')  # noqa: E501

        statement = schemas.Statement(
            id=f"{schemas.NamespacePrefix.MOA.value}:aid{record['id']}",
            description=record['description'],
            evidence_level=f"moa.evidence_level:"
                           f"{evidence_level}",
            proposition=propositions[0]['id'],
            variation_origin=self._get_variation_origin(record['variant']),
            variation_descriptor=variant_descriptors[0]['id'],
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            method=methods[0]['id'],
            supported_by=[se['id'] for se in documents]
        ).dict(exclude_none=True)

        return [statement]

    def _get_tr_propositions(self, record, variation_descriptors,
                             disease_descriptors, therapy_descriptors,
                             propositions_ix):
        """Return a list of propositions.

        :param: MOA assertion
        :param: A list of Variation Descriptors
        :param: A list of Disease Descriptors
        :param: A list of therapy_descriptors
        :param: Keeps track of proposition and support_evidence indexes
        :return: A list of therapeutic propositions.
        """
        predicate = self._get_predicate(record['clinical_significance'])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return []

        proposition = schemas.TherapeuticResponseProposition(
            id="",
            type="therapeutic_response_proposition",
            predicate=predicate,
            subject=variation_descriptors[0]['value_id'],
            object_qualifier=disease_descriptors[0]['value']['id'],
            object=therapy_descriptors[0]['value']['id']
        ).dict(exclude_none=True)

        # Get corresponding id for proposition
        key = (proposition['type'],
               proposition['predicate'],
               proposition['subject'],
               proposition['object_qualifier'],
               proposition['object'])

        proposition_index = self._set_ix(propositions_ix,
                                         'propositions', key)
        proposition['id'] = f"proposition:{proposition_index:03}"

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
            extensions=self._get_variant_extensions(variant)
        ).dict(exclude_none=True)

        return [variation_descriptor]

    def _get_variant_extensions(self, variant):
        """Return a list of extensions for a variant.

        :param dict variant: A MOA variant record
        :return: A list of extensions
        """
        coordinate = ['chromosome', 'start_position', 'end_position',
                      'reference_allele', 'alternate_allele',
                      'cdna_change', 'protein_change', 'exon']

        extensions = [
            schemas.Extension(
                name='moa_representative_coordinate',
                value={c: variant[c] for c in coordinate}
            ).dict(exclude_none=True)
        ]

        if variant['rsid']:
            extensions.append(
                schemas.Extension(
                    name='moa_rsid',
                    value=variant['rsid']
                ).dict(exclude_none=True)
            )
        return extensions

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
                        id=f"{schemas.NamespacePrefix.MOA.value}.normalize."
                           f"{schemas.NormalizerPrefix.GENE.value}:{quote(gene)}",  # noqa: E501
                        label=gene,
                        value=schemas.Gene(id=gene_norm_resp['records'][0].concept_id),  # noqa: E501
                    ).dict(exclude_none=True)
                else:
                    logger.warning(f"{gene} not found in Gene "
                                   f"Normalization normalize.")
                    gene_descriptor = {}

                gene_descriptors.append(gene_descriptor)

        return gene_descriptors

    def _get_documents(self, source):
        """Get an assertion's documents.

        :param: An evidence source
        :param: Keeps track of proposition and documents indexes
        """
        documents = None
        if source['pmid'] != "None":
            documents_id = f"pmid:{source['pmid']}"
        else:
            documents_id = source['url']

        xrefs = []
        if source['doi']:
            xrefs.append(f"doi:{source['doi']}")
        if source['nct'] != "None":
            xrefs.append(f"nct:{source['nct']}")

        documents = schemas.Document(
            id=documents_id,
            label=source['citation'],
            xrefs=xrefs if xrefs else None
        ).dict(exclude_none=True)

        return [documents]

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
            authors='Reardon, B., Moore, N.D., Moore, N. et al.'
        ).dict()]

        return methods

    def _get_therapy_descriptors(self, assertion):
        """Return a list of Therapy Descriptors.

        :param: an MOA assertion record
        :return: A list of Therapy Descriptors
        """
        label = assertion['therapy_name']

        if not label:
            return []
        therapy_norm_resp = self.therapy_query_handler.search_groups(label)

        if therapy_norm_resp['match_type'] == 0:
            logger.warning(f"{label} not found in Therapy "
                           f"Normalization normalize.")
            return []

        therapy_norm_resp = therapy_norm_resp['value_object_descriptor']

        normalized_therapy_id = \
            therapy_norm_resp['value']['id']

        if normalized_therapy_id:
            therapy_descriptor = schemas.ValueObjectDescriptor(
                id=f"{schemas.NamespacePrefix.MOA.value}."
                   f"{therapy_norm_resp['id']}",
                type="TherapyDescriptor",
                label=label,
                value=schemas.Drug(id=normalized_therapy_id)
            ).dict(exclude_none=True)
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
        highest_match = 0
        disease_norm_resp = None

        for query in [ot_code, disease_name]:
            if not query:
                continue

            disease_norm_resp_cand = self.disease_query_handler.search_groups(query)  # noqa: E501
            if disease_norm_resp_cand['match_type'] > highest_match:
                disease_norm_resp = disease_norm_resp_cand
                highest_match = disease_norm_resp['match_type']
                normalized_disease_id = \
                    disease_norm_resp['value_object_descriptor']['value']['disease_id']  # noqa: E501
                if highest_match == 100:
                    break

        if highest_match == 0:
            logger.warning(f"{ot_code} and {disease_name} not found in "
                           f"Disease Normalization normalize.")
            return []

        disease_descriptor = schemas.ValueObjectDescriptor(
            id=f"{schemas.NamespacePrefix.MOA.value}."
               f"{disease_norm_resp['value_object_descriptor']['id']}",
            type="DiseaseDescriptor",
            label=disease_name,
            value=schemas.Disease(id=normalized_disease_id),
        ).dict(exclude_none=True)

        return [disease_descriptor]

    def _get_record(self, record_id, records):
        """Get a MOA record by ID.

        :param: The ID of the record we are searching for
        :param: A dict of records for a given MOA record type
        """
        for r in records:
            if r['id'] == record_id:
                return r

    def _set_ix(self, propositions_ix, dict_key, search_key):
        """Set indexes for propositions.

        :param dict propositions_ix: Keeps track of proposition indexes
        :param str dict_key: 'propositions'
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        dict_key_ix = 'proposition_index'
        if propositions_ix[dict_key].get(search_key):
            index = propositions_ix[dict_key].get(search_key)
        else:
            index = propositions_ix.get(dict_key_ix)
            propositions_ix[dict_key][search_key] = index
            propositions_ix[dict_key_ix] += 1
        return index
