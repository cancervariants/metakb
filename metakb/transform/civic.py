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

        # Transform CIViC EIDs, then transform CIViC AIDs
        self._transform_statements(responses, evidence_items, variants, genes,
                                   propositions_support_evidence_ix,
                                   cdm_evidence_items)
        self._transform_statements(responses, assertions, variants, genes,
                                   propositions_support_evidence_ix,
                                   cdm_evidence_items, is_evidence=False)

        return responses

    def _transform_statements(self, responses, records, variants, genes,
                              propositions_support_evidence_ix,
                              cdm_evidence_items, is_evidence=True):
        """Add transformed CIViC EIDs and AIDs to response list.

        :param list responses: A list of dicts containing CDM data
        :param list records: A list of dicts containing EIDs or AIDs
        :param dict variants: CIViC variant records
        :param dict genes: CIViC gene records
        :param dict propositions_support_evidence_ix: Keeps track of
            proposition and support_evidence indexes
        :param dict cdm_evidence_items: A dict containing evidence items that
            have been transformed to the CDM
        :param bool is_evidence: `True` if records are CIViC evidence_items.
            `False` if records are CIViC assertions.
        """
        for record in records:
            if not is_evidence:
                descriptors = self._get_descriptors(record, genes, variants,
                                                    is_evidence=False)
            else:
                descriptors = self._get_descriptors(record, genes, variants)

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

            if is_evidence:
                gene_descriptors = self._get_gene_descriptors(
                    self._get_record(record['gene_id'], genes))
                support_evidence = \
                    self._get_eid_support_evidence(
                        record['source'], propositions_support_evidence_ix)
                methods = self._get_method(record)
                statements = self._get_statement(record, propositions,
                                                 variation_descriptors,
                                                 therapy_descriptors,
                                                 disease_descriptors, methods,
                                                 support_evidence)
            else:
                gene_descriptors = self._get_gene_descriptors(
                    self._get_record(record['gene']['id'], genes)
                )
                eids = [f"{schemas.NamespacePrefix.CIVIC.value}:"
                        f"{evidence['name'].lower()}" for evidence in
                        record['evidence_items'] if
                        cdm_evidence_items.get(evidence['name'])]
                support_evidence = \
                    self._get_aid_support_evidence(
                        record, propositions_support_evidence_ix,
                        cdm_evidence_items, eids)
                methods = self._get_method(record, is_evidence=False)
                statements = self._get_statement(record, propositions,
                                                 variation_descriptors,
                                                 therapy_descriptors,
                                                 disease_descriptors, methods,
                                                 support_evidence,
                                                 is_evidence=False)
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
            if is_evidence:
                cdm_evidence_items[record['name']] = response
            responses.append(response)

    def _get_statement(self, record, propositions, variant_descriptors,
                       therapy_descriptors, disease_descriptors,
                       methods, support_evidence, is_evidence=True):
        """Get a statement for an EID or AID.

        :param dict record: A CIViC EID or AID record
        :param list propositions: Propositions for the record
        :param list variant_descriptors: Variant Descriptors for the record
        :param list therapy_descriptors: Therapy Descriptors for the record
        :param list disease_descriptors: Disease Descriptors for the record
        :param list methods: Assertion methods for the record
        :param list support_evidence: Supporting evidence for the rcord
        :param bool is_evidence: `True` if record is a CIViC EID.
            `False` if record is a CIViC AID.
        """
        if is_evidence:
            evidence_level = f"civic.evidence_level:" \
                             f"{record['evidence_level']}"
        else:
            evidence_level = None
            # TODO: Do ACMG level
            if record['amp_level']:
                evidence_level = \
                    f"civic.amp_level:" \
                    f"{'_'.join(record['amp_level'].lower().split())}"

        statement = schemas.Statement(
            id=f"{schemas.NamespacePrefix.CIVIC.value}:"
               f"{record['name'].lower()}",
            description=record['description'],
            direction=self._get_evidence_direction(
                record['evidence_direction']),
            evidence_level=evidence_level,
            proposition=propositions[0]['_id'],
            variation_descriptor=variant_descriptors[0]['id'],
            therapy_descriptor=therapy_descriptors[0]['id'],
            disease_descriptor=disease_descriptors[0]['id'],
            method=methods[0]['id'],
            support_evidence=[se['id'] for se in support_evidence]
        ).dict()
        return [statement]

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

            # Might not be able to find NCIt therapy ID
            # Log captured in _get_therapy_descriptors
            if len(therapy_descriptors) != 1:
                return None

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

    def _get_tr_propositions(self, record, variation_descriptors,
                             disease_descriptors, therapy_descriptors,
                             propositions_support_evidence_ix):
        """Return a list of propositions.

        :param dict record: CIViC EID or AID
        :param list variation_descriptors: A list of Variation Descriptors
        :param list disease_descriptors: A list of Disease Descriptors
        :param list therapy_descriptors: A list of therapy_descriptors
        :param dict propositions_support_evidence_ix: Keeps track of
            proposition and support_evidence indexes
        :return: A list of therapeutic propositions.
        """
        proposition_type = \
            self._get_proposition_type(record['evidence_type'])

        # Only want TR for now
        if proposition_type != schemas.PropositionType.PREDICTIVE.value:
            return []

        predicate = self._get_predicate(proposition_type,
                                        record['clinical_significance'])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return []

        proposition = schemas.TherapeuticResponseProposition(
            _id="",
            type=proposition_type,
            predicate=predicate,
            variation_origin=self._get_variation_origin(
                record['variant_origin']),
            subject=variation_descriptors[0]['value_id'],
            object_qualifier=disease_descriptors[0]['value']['disease_id'],
            object=therapy_descriptors[0]['value']['therapy_id']
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

    def _get_proposition_type(self, evidence_type, is_evidence=True):
        """Return proposition type for a given EID or AID.

        :param str evidence_type: CIViC evidence type
        :param bool is_evidence: `True` if EID. `False` if AID.
        :return: A string representation of the proposition type
        """
        evidence_type = evidence_type.upper()
        if evidence_type in schemas.PropositionType.__members__.keys():
            if evidence_type == 'PREDISPOSING':
                if is_evidence:
                    proposition_type = schemas.PropositionType.PREDISPOSING
                else:
                    proposition_type = schemas.PropositionType.PATHOGENIC
            else:
                proposition_type = schemas.PropositionType[evidence_type]
        else:
            raise KeyError(f"Proposition Type {evidence_type} not found in "
                           f"schemas.PropositionType")
        return proposition_type.value

    def _get_variation_origin(self, variant_origin):
        """Return variant origin.

        :param str variant_origin: CIViC variant origin
        :return: A str representation of variation origin
        """
        if variant_origin == 'Somatic':
            origin = schemas.VariationOrigin.SOMATIC.value
        elif variant_origin in ['Rare Germline', 'Common Germline']:
            origin = schemas.VariationOrigin.GERMLINE.value
        elif variant_origin == 'N/A':
            origin = schemas.VariationOrigin.NOT_APPLICABLE.value
        else:
            origin = None
        return origin

    def _get_predicate(self, proposition_type, clin_sig):
        """Return predicate for an evidence item.

        :param str proposition_type: The proposition type
        :param str clin_sig: The evidence item's clinical significance
        :return: A string representation for predicate
        """
        if clin_sig is None or clin_sig.upper() in ['N/A', 'UNKNOWN']:
            return None

        clin_sig = '_'.join(clin_sig.upper().split())
        predicate = None

        if proposition_type == schemas.PropositionType.PREDICTIVE.value:
            if clin_sig == 'SENSITIVITY/RESPONSE':
                predicate = schemas.PredictivePredicate.SENSITIVITY.value
            elif clin_sig == 'RESISTANCE':
                predicate = schemas.PredictivePredicate.RESISTANCE.value
        elif proposition_type == schemas.PropositionType.DIAGNOSTIC.value:
            predicate = schemas.DiagnosticPredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.PROGNOSTIC.value:
            if clin_sig == 'POSITIVE':
                predicate = schemas.PrognosticPredicate.BETTER_OUTCOME.value
            else:
                predicate = schemas.PrognosticPredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.FUNCTIONAL.value:
            predicate = schemas.FunctionalPredicate[clin_sig].value
        elif proposition_type == schemas.PropositionType.ONCOGENIC.value:
            # TODO: There are currently no Oncogenic types in CIViC harvester
            #  Look into why this is
            pass
        elif proposition_type == schemas.PropositionType.PATHOGENIC.value:
            if clin_sig in ['PATHOGENIC', 'LIKELY_PATHOGENIC']:
                predicate = schemas.PathogenicPredicate.PATHOGENIC.value
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
        hgvs_exprs_queries = list()
        for expr in hgvs_exprs:
            if 'protein' in expr['syntax']:
                hgvs_exprs_queries.append(expr)

        variant_norm_resp = None
        for query in [variant_query] + hgvs_exprs_queries:
            if not query:
                continue
            validations = self.variant_to_vrs.get_validations(
                variant_query)

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
            extensions=self._get_variant_extensions(variant)
        ).dict()
        return [variation_descriptor]

    def _get_variant_extensions(self, variant):
        """Return a list of extensions for a variant.

        :param dict variant: A CIViC variant record
        :return: A list of extensions
        """
        extensions = [
            schemas.Extension(
                name='representative_variation_descriptor',
                value=f"civic:vid{variant['id']}.rep"
            ).dict(),
            schemas.Extension(
                name='civic_actionability_score',
                value=variant['civic_actionability_score']
            ).dict()
        ]

        variant_groups = variant['variant_groups']
        if variant_groups:
            v_groups = list()
            for v_group in variant_groups:
                v_groups.append({
                    'id': f"civic:vgid{v_group['id']}",
                    'label': v_group['name'],
                    'description': v_group['description'],
                    'variants':
                        [f"civic:vid{v['id']}" for v in v_group['variants']],
                    'type': 'variant_group'
                })
            extensions.append(schemas.Extension(
                name='variant_groups',
                value=v_groups
            ))
        return extensions

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
        """Return a Gene Descriptor.

        :param dict gene: A CIViC gene record
        :return A Gene Descriptor
        """
        found_match = False
        gene_norm_resp = None
        for query_str in [f"ncbigene:{gene['entrez_id']}", gene['name']] + gene['aliases']:  # noqa: E501
            if not query_str:
                continue

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
            if not query:
                continue

            disease_norm_resp = self.disease_query_handler.search_groups(query)
            if disease_norm_resp['match_type'] != 0:
                break

        if not disease_norm_resp or disease_norm_resp['match_type'] == 0:
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
        label = drug['name']
        ncit_id = f"ncit:{drug['ncit_id']}"
        therapy_norm_resp = None

        for query in [ncit_id, label]:
            if not query:
                continue

            therapy_norm_resp = self.therapy_query_handler.search_groups(query)
            if therapy_norm_resp['match_type'] != 0:
                break

        if not therapy_norm_resp or therapy_norm_resp['match_type'] == 0:
            logger.warning(f"{ncit_id} and {label} not found in Therapy "
                           f"Normalization normalize.")
            return []

        therapy_norm_resp = therapy_norm_resp['value_object_descriptor']

        therapy_norm_id = \
            therapy_norm_resp['value']['therapy_id']

        # TODO: RxNorm is highest priority, but in example listed NCIt?
        if not therapy_norm_id.startswith('ncit'):
            therapy_norm_id = None
            if 'xrefs' in therapy_norm_resp:
                for other_id in therapy_norm_resp['xrefs']:
                    if other_id.startswith('ncit:'):
                        therapy_norm_id = other_id

        if therapy_norm_id:
            therapies = schemas.ValueObjectDescriptor(
                id=f"civic:tid{drug['id']}",
                type="TherapyDescriptor",
                label=label,
                value=schemas.Therapy(therapy_id=therapy_norm_id),
                alternate_labels=drug['aliases']
            ).dict()
        else:
            return []
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

    def _get_method(self, record, is_evidence=True):
        """Get methods for a given record.

        :param dict record: A CIViC EID or AID
        :param bool is_evidence: `True` if record is a CIViC EID.
            `False` if record is a CIViC AID.
        :return: A list of methods
        """
        if is_evidence:
            methods = [schemas.Method(
                id=f'method:'
                   f'{schemas.MethodID.CIVIC_EID_SOP:03}',
                label='Standard operating procedure for curation and clinical interpretation of variants in cancer',  # noqa: E501
                url='https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x',  # noqa: E501
                version=schemas.Date(year=2019, month=11, day=29),
                reference='Danos, A.M., Krysiak, K., Barnell, E.K. et al.'
            ).dict()]
        else:
            if record['amp_level'] and not record['acmg_codes']:
                methods = [
                    schemas.Method(
                        id=f'method:{schemas.MethodID.CIVIC_AID_AMP_ASCO_CAP.value:03}',  # noqa: E501
                        label='Standards and Guidelines for the '
                              'Interpretation and Reporting of Sequence '
                              'Variants in Cancer: A Joint Consensus '
                              'Recommendation of the Association '
                              'for Molecular Pathology, American Society of '
                              'Clinical Oncology, and College of American '
                              'Pathologists',
                        url='https://pubmed.ncbi.nlm.nih.gov/27993330/',
                        version=schemas.Date(year=2017, month=1),
                        reference='Li MM, Datto M, Duncavage EJ, et al.'
                    ).dict()
                ]
            elif not record['amp_level'] and record['acmg_codes']:
                methods = [
                    schemas.Method(
                        id=f'method:'
                           f'{schemas.MethodID.CIVIC_AID_ACMG.value:03}',
                        label='Standards and guidelines for the '
                              'interpretation of sequence variants: a '
                              'joint consensus recommendation of the '
                              'American College of Medical Genetics and'
                              ' Genomics and the Association for '
                              'Molecular Pathology',
                        url='https://pubmed.ncbi.nlm.nih.gov/25741868/',
                        version=schemas.Date(year=2015, month=5),
                        reference='Richards S, Aziz N, Bale S, et al.'
                    ).dict()
                ]
            else:
                methods = []
        return methods

    def _get_eid_support_evidence(self, source,
                                  propositions_support_evidence_ix):
        """Get an EID's support evidence.

        :param dict source: An evidence item's source
        :param propositions_support_evidence_ix: Keeps track of proposition and
            support_evidence indexes
        """
        support_evidence = None
        source_type = source['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
            support_evidence_id = f"{prefix}:{source['citation_id']}"
            support_evidence_ix = \
                self._set_ix(propositions_support_evidence_ix,
                             'support_evidence', support_evidence_id)
            xrefs = []
            if source['asco_abstract_id']:
                xrefs.append(f"asco.abstract:{source['asco_abstract_id']}")
            if source['pmc_id']:
                xrefs.append(f"pmc:{source['pmc_id']}")

            support_evidence = schemas.SupportEvidence(
                id=f"support_evidence:{support_evidence_ix:03}",
                support_evidence_id=support_evidence_id,
                label=source['citation'],
                description=source['name'],
                xrefs=xrefs
            ).dict()
        else:
            logger.warning(f"{source_type} not in schemas.SourcePrefix.")
        return [support_evidence]

    def _get_aid_support_evidence(self, assertion,
                                  propositions_support_evidence_ix,
                                  cdm_evidence_items, eids):
        """Get an AID's support evidence.

        :param dict assertion: A CIViC Assertion
        :param propositions_support_evidence_ix: Keeps track of proposition and
            support_evidence indexes
        :param dict cdm_evidence_items: A dict containing evidence items that
            have been transformed to the CDM
        :param list eids: EIDs found in AID
        """
        # NCCN Guidlines
        label = assertion['nccn_guideline']
        version = assertion['nccn_guideline_version']
        support_evidence_id = '_'.join((label + version).split())
        support_evidence_ix = \
            self._set_ix(propositions_support_evidence_ix, 'support_evidence',
                         support_evidence_id)
        support_evidence = list()
        support_evidence.append(schemas.SupportEvidence(
            id=f"support_evidence:{support_evidence_ix:03}",
            support_evidence_id="https://www.nccn.org/professionals/"
                                "physician_gls/default.aspx",
            label=f"NCCN Guidelines: {label} version {version}",
            xrefs=[]
        ).dict())

        # EIDs
        for eid in eids:
            support_evidence_id = eid
            support_evidence_ix = \
                self._set_ix(propositions_support_evidence_ix,
                             'support_evidence', support_evidence_id)
            label = support_evidence_id.split(':')[-1].upper()
            support_evidence.append(schemas.SupportEvidence(
                id=f"support_evidence:{support_evidence_ix:03}",
                support_evidence_id=support_evidence_id,
                label=label,
                description=cdm_evidence_items[label]['statements'][0]['description'],  # noqa: E501
                xrefs=[]
            ).dict())

        # ACMG Codes
        if assertion['acmg_codes']:
            for acmg_code in assertion['acmg_codes']:
                support_evidence_id = f"acmg:{acmg_code['code']}"
                support_evidence_ix = \
                    self._set_ix(propositions_support_evidence_ix,
                                 'support_evidence', support_evidence_id)
                support_evidence.append(schemas.SupportEvidence(
                    id=f"support_evidence:{support_evidence_ix:03}",
                    support_evidence_id=support_evidence_id,
                    label=acmg_code['code'],
                    description=acmg_code['description'],
                    xrefs=[]
                ))

        return support_evidence

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
