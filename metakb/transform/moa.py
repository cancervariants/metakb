"""A module to convert MOA resources to common data model"""
from typing import Optional
import logging
from urllib.parse import quote

from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor,\
    Extension, GeneDescriptor, ValueObjectDescriptor

import metakb.schemas as schemas
from metakb.transform.base import Transform

logger = logging.getLogger('metakb.transform.moa')
logger.setLevel(logging.DEBUG)


class MOATransform(Transform):
    """A class for transforming MOA resources to common data model."""

    def transform(self):
        """Transform MOA harvested JSON to common date model.
        Saves output in MOA transform directory.
        """
        data = self.extract_harvester()
        cdm_assertions = {}  # assertions that have been transformed to CDM

        assertions = data['assertions']
        sources = data['sources']
        variants = data['variants']

        # Transform MOA assertions
        self._transform_statements(assertions, variants, sources,
                                   cdm_assertions)

    def _transform_statements(self, records, variants, sources,
                              cdm_assertions):
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
                                          therapy_descriptors)

            # We only want therapeutic response for now
            if not propositions:
                continue

            documents = self._get_documents(
                self._get_record(record['source_ids'], sources))

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
            ).dict(by_alias=True, exclude_none=True)

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
        len_td = len(therapy_descriptors)
        if len_td != 1:
            logger.warning(f"Expected 1 therapy_descriptor for"
                           f" {record['therapy_name']} but found {len_td}")
            return None

        variation_descriptors = self._get_variation_descriptors(
            self._get_record(record['variant']['id'], variants),
            gene_descriptors)
        len_vd = len(variation_descriptors)
        if len_vd != 1:
            logger.warning(f"Expected 1 variation descriptor for"
                           f" {record['variant']} but found {len_vd}")
            return None

        disease_descriptors = self._get_disease_descriptors(record)
        len_dd = len(disease_descriptors)
        if len_dd != 1:
            logger.warning(f"Expected 1 disease descriptor for"
                           f" {record['disease']} but found {len_dd}")
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
            id=f"{schemas.SourceName.MOA.value}.assertion:{record['id']}",
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
                             disease_descriptors, therapy_descriptors):
        """Return a list of propositions.

        :param: MOA assertion
        :param: A list of Variation Descriptors
        :param: A list of Disease Descriptors
        :param: A list of therapy_descriptors
        :return: A list of therapeutic propositions.
        """
        predicate = self._get_predicate(record['clinical_significance'])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return []

        params = {
            'id': '',
            'type': schemas.PropositionType.PREDICTIVE,
            'predicate': predicate,
            'subject': variation_descriptors[0]['variation_id'],
            'object_qualifier': disease_descriptors[0]['disease_id'],
            'object': therapy_descriptors[0]['therapy_id']
        }

        # Get corresponding id for proposition
        params["id"] = self._get_proposition_id(
            params["type"],
            params["predicate"],
            variation_ids=[params["subject"]],
            disease_ids=[params["object_qualifier"]],
            therapy_ids=[params["object"]]
        )
        proposition = schemas.TherapeuticResponseProposition(
            **params).dict(exclude_none=True)
        return [proposition]

    def _get_predicate(self,
                       clin_sig) -> Optional[schemas.PredictivePredicate]:
        """Get the predicate of this record

        :param: clinical significance of the assertion
        :return: predicate if valid, None otherwise
        """
        if not clin_sig:
            return None
        try:
            return schemas.PredictivePredicate[clin_sig.upper()]
        except KeyError:
            return None

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
        vrs_ref_allele_seq = variant['protein_change'][2] \
            if 'protein_change' in variant and variant['protein_change'] else None  # noqa: E501

        v_norm_resp = None
        # For now, the normalizer only support a.a substitution
        if g_descriptors and 'protein_change' in variant and variant['protein_change']:  # noqa: E501
            gene = g_descriptors[0]['label']
            query = f"{gene} {variant['protein_change'][2:]}"
            v_norm_resp = self.vicc_normalizers.normalize_variation([query])

            if not v_norm_resp:
                logger.warning(f"Variant Normalizer unable to normalize: "
                               f"moa.variant:{variant['id']}.")
                return []
        else:
            logger.warning(f"Variation Normalizer does not support "
                           f"moa.variant:{variant['id']}: {variant}")
            return []

        gene_context = g_descriptors[0]['id'] if g_descriptors else None

        variation_descriptor = VariationDescriptor(
            id=f"moa.variant:{variant['id']}",
            label=variant['feature'],
            variation_id=v_norm_resp.variation_id,
            variation=v_norm_resp.variation,
            gene_context=gene_context,
            vrs_ref_allele_seq=vrs_ref_allele_seq,
            extensions=self._get_variant_extensions(variant)
        ).dict(by_alias=True, exclude_none=True)
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
            Extension(
                name='moa_representative_coordinate',
                value={c: variant[c] for c in coordinate}
            ).dict(exclude_none=True)
        ]

        if variant['rsid']:
            extensions.append(
                Extension(
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
                _, normalized_gene_id = \
                    self.vicc_normalizers.normalize_gene([gene])
                if normalized_gene_id:
                    gene_descriptor = GeneDescriptor(
                        id=f"{schemas.SourceName.MOA.value}.normalize."
                           f"{schemas.NormalizerPrefix.GENE.value}:{quote(gene)}",  # noqa: E501
                        label=gene,
                        gene_id=normalized_gene_id,
                    ).dict(exclude_none=True)
                else:
                    logger.warning(f"Gene Normalizer unable to "
                                   f"normalize: {gene}")
                    gene_descriptor = {}

                gene_descriptors.append(gene_descriptor)

        return gene_descriptors

    def _get_documents(self, source):
        """Get an assertion's documents.

        :param: An evidence source
        :param: Keeps track of proposition and documents indexes
        """
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
               f'{schemas.MethodID.MOA_ASSERTION_BIORXIV}',
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

        therapy_norm_resp, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy([label])

        if not normalized_therapy_id:
            logger.warning(f"Therapy Normalizer unable to normalize: {label}")
            return []

        if normalized_therapy_id:
            therapy_descriptor = ValueObjectDescriptor(
                id=f"{schemas.SourceName.MOA.value}."
                   f"{therapy_norm_resp.therapy_descriptor.id}",
                type="TherapyDescriptor",
                label=label,
                therapy_id=normalized_therapy_id
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
        if ot_code:
            ot_code = f"oncotree:{ot_code}"
        disease_name = assertion['disease']['name']

        disease_norm_resp, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease([ot_code, disease_name])

        if not normalized_disease_id:
            logger.warning(f"Disease Normalize unable to normalize: "
                           f"{ot_code} and {disease_name}")
            return []

        disease_descriptor = ValueObjectDescriptor(
            id=f"{schemas.SourceName.MOA.value}."
               f"{disease_norm_resp.disease_descriptor.id}",
            type="DiseaseDescriptor",
            label=disease_name,
            disease_id=normalized_disease_id,
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
