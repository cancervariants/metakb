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
        cdm_evidence_items = dict()  # EIDs that have been transformed to CDM
        propositions_documents_ix = {
            'document_index': 1,  # Keep track of document index value
            'documents': dict(),  # {document_id: document_index}
            'proposition_index': 1,  # Keep track of proposition index value
            'propositions': dict()  # {tuple: proposition_index}
        }
        self._transform_evidence(responses, evidence_items, variants, genes,
                                 propositions_documents_ix,
                                 cdm_evidence_items)
        self._transform_assertions(responses, assertions, variants, genes,
                                   cdm_evidence_items,
                                   propositions_documents_ix)
        return responses

    def _transform_evidence(self, responses, evidence_items, variants, genes,
                            propositions_documents_ix, cdm_evidence_items):
        """Add transformed EIDs to the response list.

        :param list responses: A list of dicts containing CDM data
        :param list evidence_items: A list of CIViC evidence items
        :param dict variants: A dict of CIViC variant records
        :param dict genes: A dict of CIViC gene records
        :param dict propositions_documents_ix: Keeps track of proposition and
            document indexes
        :param dict cdm_evidence_items: A dict containing evidence items that
            have been transformed to the CDM
        """
        for evidence in evidence_items:
            descriptors = self._get_descriptors(evidence, genes, variants)
            if not descriptors:
                continue
            else:
                therapy_descriptors, variation_descriptors, disease_descriptors = descriptors  # noqa: E501

            propositions = \
                self._get_tr_propositions(evidence, variation_descriptors,
                                          disease_descriptors,
                                          therapy_descriptors,
                                          propositions_documents_ix)

            # We only want therapeutic response for now
            if not propositions:
                continue

            documents = self._get_evidence_document(evidence['source'],
                                                    propositions_documents_ix)

            assertion_methods = [schemas.AssertionMethod(
                id='assertion_method:1',
                label='Standard operating procedure for curation and clinical interpretation of variants in cancer',  # noqa: E501
                url='https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x',  # noqa: E501
                version=schemas.Date(year=2019, month=11, day=29),
                reference='Danos, A.M., Krysiak, K., Barnell, E.K. et al.'
            ).dict()]

            response = {
                'evidence': self._get_evidence(evidence,
                                               propositions,
                                               therapy_descriptors,
                                               disease_descriptors,
                                               assertion_methods,
                                               documents),
                'propositions': propositions,
                'variation_descriptors': variation_descriptors,
                'therapy_descriptors': therapy_descriptors,
                'disease_descriptors': disease_descriptors,
                'assertion_methods': assertion_methods,
                'documents': documents
            }
            cdm_evidence_items[evidence['name']] = response
            responses.append(response)

    def _transform_assertions(self, responses, assertions, variants, genes,
                              cdm_evidence_items, propositions_documents_ix):
        """Add transformed CIViC Assertion records to response list.

        :param list responses: A list of dicts containing CDM data
        :param dict assertions: A dict of CIViC assertions
        :param dict cdm_evidence_items: A dict containing evidence items that
            have been transformed to the CDM
        """
        for assertion in assertions:
            # Get list of CIViC EIDs from captured evidence_items
            # that have a TR Proposition
            eids = [f"{schemas.NamespacePrefix.CIVIC.value}:"
                    f"{evidence['name'].lower()}" for evidence in
                    assertion['evidence_items'] if
                    cdm_evidence_items.get(evidence['name'])]

            descriptors = self._get_descriptors(assertion, genes, variants,
                                                is_evidence=False)
            if not descriptors:
                continue
            else:
                therapy_descriptors, variation_descriptors, disease_descriptors = descriptors  # noqa: E501

            propositions = \
                self._get_tr_propositions(assertion, variation_descriptors,
                                          disease_descriptors,
                                          therapy_descriptors,
                                          propositions_documents_ix)

            if not propositions:
                continue

            assertion_methods = [
                schemas.AssertionMethod(
                    id='assertion_method:2',
                    label='Standards and Guidelines for the Interpretation '
                          'and Reporting of Sequence Variants in Cancer: A '
                          'Joint Consensus Recommendation of the Association '
                          'for Molecular Pathology, American Society of '
                          'Clinical Oncology, and College of American '
                          'Pathologists',
                    url='https://pubmed.ncbi.nlm.nih.gov/27993330/',
                    version=schemas.Date(year=2017, month=1),
                    reference='Li MM, Datto M, Duncavage EJ, et al.'
                ).dict(),
                schemas.AssertionMethod(
                    id='assertion_method:3',
                    label='Standards and guidelines for the interpretation of'
                          ' sequence variants: a joint consensus '
                          'recommendation of the American College of Medical '
                          'Genetics and Genomics and the Association for '
                          'Molecular Pathology',
                    url='https://pubmed.ncbi.nlm.nih.gov/25741868/',
                    version=schemas.Date(year=2015, month=5),
                    reference='Richards S, Aziz N, Bale S, et al.'
                ).dict()
            ]

            documents = self._get_assertion_document(assertion,
                                                     propositions_documents_ix)

            responses.append({
                'assertion': self._get_assertion(assertion, propositions,
                                                 eids, assertion_methods,
                                                 documents),
                'propositions': propositions,
                'evidence': eids,
                'assertion_methods': assertion_methods,
                'documents': documents
            })

    def _get_evidence(self, evidence, propositions,
                      therapy_descriptors, disease_descriptors,
                      assertion_methods, documents):
        """Return a list of evidence.

        :param dict evidence: Harvested CIViC evidence item record
        :param list propositions: A list of propositions
        :param list therapy_descriptors: A list of Therapy Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list assertion_methods: A list of assertion methods for the
            evidence
        :return: A list of Evidence
        """
        evidence = schemas.Evidence(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{evidence['name'].lower()}",
            description=evidence['description'],
            direction=self._get_evidence_direction(
                evidence['evidence_direction']),
            evidence_level=f"civic.evidence_level:"
                           f"{evidence['evidence_level']}",
            proposition=propositions[0]['_id'],
            variation_descriptor=f"civic:vid{evidence['variant_id']}",
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            assertion_method=assertion_methods[0]['id'],
            document=documents[0]['id']
        ).dict()
        return [evidence]

    def _get_assertion(self, assertion, propositions, eids, assertion_methods,
                       documents):
        """Return a list of assertions.

        :param dict assertion: Harvested CIViC assertion item record
        :param list propositions: A dict containing indexes for
            propositions and assertion methods
        :param list eids:
        :return: A list of Assertions
        """
        assertion_level = None
        if assertion['amp_level']:
            assertion_level = f"civic.amp_level:"\
                              f"{'_'.join(assertion['amp_level'].lower().split())}"  # noqa: E501

        assertion = schemas.Assertion(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{assertion['name'].lower()}",
            description=assertion['description'],
            direction=self._get_evidence_direction(assertion['evidence_direction']),  # noqa: E501
            assertion_level=assertion_level,
            proposition=propositions[0]['_id'],
            assertion_methods=[a['id'] for a in assertion_methods],
            document=documents[0]['id'],
            evidence=eids
        ).dict()
        return [assertion]

    def _get_descriptors(self, record, genes, variants, is_evidence=True):
        """Return tuple of descriptors if one exists for each type.

        :param dict record: A CIViC EID or AID
        :param dict genes: CIViC gene records
        :param dict variants: CIViC variant records
        :param bool is_evidence: `True` if EID. `False` if AID.
        """
        if len(record['drugs']) != 1:
            logger.warning(f"{record['name']} does not have exactly "
                           f"one therapy.")
            return None
        else:
            therapy_descriptors = self._get_therapy_descriptors(
                record['drugs'][0])

        if is_evidence:
            variation_descriptors = \
                self._get_variation_descriptors(self._get_record(
                    record['variant_id'], variants),
                    self._get_record(record['gene_id'], genes))
        else:
            variation_descriptors = self._get_variation_descriptors(
                self._get_record(record['variant']['id'], variants),
                self._get_record(record['gene']['id'], genes)
            )

        if len(variation_descriptors) != 1:
            logger.warning(f"{record['name']} does not have exactly "
                           f"one variant.")
            return None

        disease_descriptors = \
            self._get_disease_descriptors(record['disease'])
        if len(disease_descriptors) != 1:
            logger.warning(f"{record['name']} does not have exactly "
                           f"one disease.")
            return None

        return therapy_descriptors, variation_descriptors, disease_descriptors

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
            return None

    def _get_tr_propositions(self, evidence, variation_descriptors,
                             disease_descriptors, therapy_descriptors,
                             propositions_documents_ix):
        """Return a list of propositions.

        :param dict evidence: CIViC evidence item record
        :param list variation_descriptors: A list of Variation Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list therapy_descriptors: A list of therapy_descriptors
        :param dict propositions_documents_ix: Keeps track of proposition and
            document indexes
        :return: A list of therapeutic propositions.
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
            variation_origin=self._get_variation_origin(
                evidence['variant_origin']),
            has_originating_context=variation_descriptors[0]['value_id'],
            disease_context=disease_descriptors[0]['value']['disease_id'],
            therapy=therapy_descriptors[0]['value']['therapy_id']
        ).dict(by_alias=True)

        key = (proposition['type'], proposition['predicate'],
               proposition['variation_origin'],
               proposition['has_originating_context'],
               proposition['disease_context'], proposition['therapy'])

        proposition_index = self._set_ix(propositions_documents_ix,
                                         'propositions', key)
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
                return None
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
        # Find all possible queries to test against variant-normalizer
        variant_query = f"{gene['name']} {variant['name']}"
        hgvs_exprs = self._get_hgvs_expr(variant)
        hgvs_exprs_query = list()
        for expr in hgvs_exprs:
            if 'protein' in expr['syntax']:
                hgvs_exprs_query.append(expr)

        variant_norm_resp = None
        for query in [variant_query] + hgvs_exprs_query:
            try:
                validations = self.variant_to_vrs.get_validations(
                    variant_query)
            except:  # noqa: E722
                logger.error(f"toVRS does not support: {variant_query}")
                return []

            variant_norm_resp = \
                self.variant_normalizer.normalize(query, validations,
                                                  self.amino_acid_cache)
            if variant_norm_resp:
                break

        if not variant_norm_resp:
            logger.warning(f"{variant_query} is not yet supported in"
                           f" Variant Normalization normalize.")
            return []

        # For now, everything that we're able to normalize is as the protein
        # level. Will change this once variant normalizer can normalize
        # other types of variants other than just protein substitution
        # So molecule_context = protein and structural_type is always
        # SO:0001060
        variation_descriptor = schemas.VariationDescriptor(
            id=f"civic:vid{variant['id']}",
            label=variant['name'],
            description=variant['description'] if variant['description'] else None,  # noqa: E501
            value_id=variant_norm_resp.value_id,
            value=variant_norm_resp.value,
            gene_context=f"civic:gid{gene['id']}",
            molecule_context='protein',
            structural_type='SO:0001060',
            ref_allele_seq=re.split(r'\d+', variant['name'])[0],
            expressions=hgvs_exprs,
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
                    if clinvar_entry and clinvar_entry != 'N/A':
                        xrefs.append(f"{schemas.XrefSystem.CLINVAR.value}:"
                                     f"{clinvar_entry}")
            elif xref == 'allele_registry_id' and v['allele_registry_id']:
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
        display_name = disease['display_name']
        disease_norm_resp = None

        for query in [doid, display_name]:
            disease_norm_resp = self.disease_query_handler.search_groups(query)
            if disease_norm_resp['match_type'] != 0:
                break

        if not disease_norm_resp:
            logger.warning(f"{doid} and {display_name} not found in Disease "
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
        :param dict drug: A drug for a given evidence_item
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
                    schemas.Expression(syntax=syntax, value=hgvs_expr).dict()
                )
        return hgvs_expressions

    def _get_evidence_document(self, source, propositions_documents_ix):
        """Get an Evidence Item's source document.

        :param dict source: An evidence item's source
        :param propositions_documents_ix: Keeps track of proposition and
            document indexes
        """
        document = None
        source_type = source['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
            document_id = f"{prefix}:{source['citation_id']}"
            document_ix = self._set_ix(propositions_documents_ix, 'documents',
                                       document_id)
            xrefs = []
            if source['asco_abstract_id']:
                xrefs.append(f"asco.abstract:{source['asco_abstract_id']}")
            if source['pmc_id']:
                xrefs.append(f"pmc:{source['pmc_id']}")

            document = schemas.Document(
                id=f"document:{document_ix:03}",
                document_id=document_id,
                label=source['citation'],
                description=source['name'],
                xrefs=xrefs
            ).dict()
        else:
            logger.warning(f"{source_type} not in schemas.SourcePrefix.")
        return [document]

    def _get_assertion_document(self, assertion, propositions_documents_ix):
        """Get an Assertion's source document.

        :param dict assertion: A CIViC Assertion
        :param propositions_documents_ix: Keeps track of proposition and
            document indexes
        """
        label = assertion['nccn_guideline']
        version = assertion['nccn_guideline_version']
        document_id = '_'.join((label + version).split())
        document_ix = self._set_ix(propositions_documents_ix, 'documents',
                                   document_id)
        document = schemas.Document(
            id=f"document:{document_ix:03}",
            document_id=None,
            label=label,
            description=f"NCCN Guideline Version: {version}"
        ).dict()
        return [document]

    def _get_record(self, record_id, records):
        """Get a CIViC record by ID.

        :param str record_id: The ID of the record we are searching for
        :param dict records: A dict of records for a given CIViC record type
        """
        for r in records:
            if r['id'] == record_id:
                return r

    def _add_to_list(self, eid, key, list_name):
        """Add a unique item from an evidence item to a list.

        :param dict eid: Evidence Item that has been transformed to CDM
        :param str key: The key to access in the eid
        :param list list_name: The name of the list to
        """
        item = eid[key][0]
        if item not in list_name:
            list_name.append(item)

    def _set_ix(self, propositions_documents_ix, dict_key, search_key):
        """Set propositions_documents_ix.

        :param dict propositions_documents_ix: Keeps track of proposition and
            document indexes
        :param str dict_key: 'sources' or 'propositions'
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        if dict_key == 'documents':
            dict_key_ix = 'document_index'
        elif dict_key == 'propositions':
            dict_key_ix = 'proposition_index'
        else:
            raise KeyError("dict_key can only be `documents` or "
                           "`propositions`.")
        if propositions_documents_ix[dict_key].get(search_key):
            index = propositions_documents_ix[dict_key].get(search_key)
        else:
            index = propositions_documents_ix.get(dict_key_ix)
            propositions_documents_ix[dict_key][search_key] = index
            propositions_documents_ix[dict_key_ix] += 1
        return index
