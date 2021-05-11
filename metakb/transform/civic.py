"""A module for to transform CIViC."""
from typing import Optional, Dict, List
from metakb import PROJECT_ROOT
import json
import logging
import metakb.schemas as schemas
from metakb.normalizers import VICCNormalizers

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CIViCTransform:
    """A class for transforming CIViC to the common data model."""

    def __init__(self,
                 file_path=f"{PROJECT_ROOT}/data/civic"
                           f"/civic_harvester.json") -> None:
        """Initialize VICC normalizers and class attributes.

        :param str file_path: The file path to the harvested json to transform.
        """
        self._file_path = file_path
        self.vicc_normalizers = VICCNormalizers()
        self.transformed = {
            'statements': list(),
            'propositions': list(),
            'variation_descriptors': list(),
            'gene_descriptors': list(),
            'therapy_descriptors': list(),
            'disease_descriptors': list(),
            'methods': list(),
            'documents': list()
        }
        # Able to normalize these IDSs
        self.valid_ids = {
            'variation_descriptors': dict(),
            'disease_descriptors': dict(),
            'therapy_descriptors': dict()
        }
        # Unable to normalize these IDSs
        self.invalid_ids = {
            'therapy_descriptors': list(),
            'disease_descriptors': list()
        }

    def _extract(self) -> Dict[str, list]:
        """Extract the CIViC harvested data file."""
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _create_json(self,
                     civic_dir=PROJECT_ROOT / 'data' / 'civic' / 'transform',
                     fn='civic_cdm.json') -> None:
        """Create a composite JSON for the transformed CIViC data.

        :param Path civic_dir: The civic transform data directory
        :param str fn: The file name for the transformed data
        """
        civic_dir.mkdir(exist_ok=True, parents=True)
        with open(f"{civic_dir}/{fn}", 'w+') as f:
            json.dump(self.transformed, f)

    def transform(self, propositions_documents_ix=None) -> Dict[str, dict]:
        """Transform CIViC harvested json to common data model.

        :param Dict propositions_documents_ix: Indexes for propositions and
            documents
        :return: An updated propositions_documents_ix object
        """
        data = self._extract()
        evidence_items = data['evidence']
        assertions = data['assertions']
        variants = data['variants']
        genes = data['genes']
        if not propositions_documents_ix:
            propositions_documents_ix = {
                # Keep track of documents index value
                'document_index': 1,
                # {document_id: document_index}
                'documents': dict(),
                # Keep track of proposition index value
                'proposition_index': 1,
                # {tuple: proposition_index}
                'propositions': dict()
            }

        # Filter Variant IDs for
        # Prognostic, Predictive, and Diagnostic evidence
        supported_evidence_types = ['Prognostic', 'Predictive', 'Diagnostic']
        vids = {e['variant_id'] for e in evidence_items
                if e['evidence_type'] in supported_evidence_types}
        vids |= {a['variant']['id'] for a in assertions
                 if a['evidence_type'] in supported_evidence_types}

        self._add_variation_descriptors(variants, vids)
        self._add_gene_descriptors(genes)
        self._add_methods()
        self._transform_evidence_and_assertions(evidence_items,
                                                propositions_documents_ix)
        self._transform_evidence_and_assertions(assertions,
                                                propositions_documents_ix,
                                                is_evidence=False)
        return propositions_documents_ix

    def _transform_evidence_and_assertions(self, records,
                                           propositions_documents_ix,
                                           is_evidence=True) -> None:
        """Transform statements, propositions, descriptors, and documents
        from CIViC evidence items and assertions.

        :param list records: CIViC Evidence Items or Assertions
        :param dict propositions_documents_ix: Indexes for propositions and
            documents
        :param bool is_evidence: `True` if records are evidence items.
            `False` if records are assertions.
        """
        for r in records:
            # Omit entries that are not in an accepted state
            if r['status'] != 'accepted':
                logger.warning(f"civic:{r['name'].lower()} has status:"
                               f" {r['status']}")
                continue

            if r['evidence_type'] not in ['Predictive', 'Prognostic',
                                          'Diagnostic']:

                continue
            else:
                # Functional Evidence types do not have a disease
                if not r['disease']:
                    continue

            if r['evidence_type'] == 'Predictive':
                if len(r['drugs']) != 1:
                    continue
                else:
                    therapy_id = f"civic:tid{r['drugs'][0]['id']}"
                    therapy_descriptor = \
                        self._add_therapy_descriptor(therapy_id, r)
                    if not therapy_descriptor:
                        continue

                    if therapy_descriptor not in self.transformed['therapy_descriptors']:  # noqa: E501
                        self.transformed['therapy_descriptors'].append(therapy_descriptor)  # noqa: E501
            else:
                therapy_id = None
                therapy_descriptor = None

            disease_id = f"civic:did{r['disease']['id']}"
            disease_descriptor = self._add_disease_descriptor(disease_id, r)
            if not disease_descriptor:
                continue

            if disease_descriptor not in self.transformed['disease_descriptors']:  # noqa: E501
                self.transformed['disease_descriptors'].append(disease_descriptor)  # noqa: E501

            if is_evidence:
                variant_id = f"civic:vid{r['variant_id']}"
            else:
                variant_id = f"civic:vid{r['variant']['id']}"
            variation_descriptor = \
                self.valid_ids['variation_descriptors'].get(variant_id)
            if not variation_descriptor:
                continue

            proposition = self._get_proposition(
                r, variation_descriptor, disease_descriptor,
                therapy_descriptor, propositions_documents_ix
            )

            # Only support Therapeutic Response and Prognostic
            if not proposition:
                continue

            if proposition not in self.transformed['propositions']:
                self.transformed['propositions'].append(proposition)

            if is_evidence:
                # Evidence items's method and evidence level
                method = f'method:{schemas.MethodID.CIVIC_EID_SOP:03}'
                evidence_level = f"civic.evidence_level:{r['evidence_level']}"

                # Supported by evidence for evidence item
                document = self._get_eid_document(r['source'])
                if document not in self.transformed['documents']:
                    self.transformed['documents'].append(document)
                supported_by = [document['id']]
            else:
                # Assertion's method
                if r['amp_level'] and not r['acmg_codes']:
                    method = \
                        f'method:' \
                        f'{schemas.MethodID.CIVIC_AID_AMP_ASCO_CAP.value:03}'
                elif not r['amp_level'] and r['acmg_codes']:
                    method = f'method:' \
                             f'{schemas.MethodID.CIVIC_AID_ACMG.value:03}'
                else:
                    # Statements are required to have a method
                    logger.warning(f"Unable to get method for "
                                   f"civic:{r['name'].lower()}")
                    continue

                # assertion's evidence level
                evidence_level = self._get_assertion_evidence_level(r)

                # Supported by evidence for assertion
                supported_by = list()
                documents = \
                    self._get_aid_document(r, propositions_documents_ix)
                for d in documents:
                    if d not in self.transformed['documents']:
                        self.transformed['documents'].append(d)
                    supported_by.append(d['id'])
                for evidence_item in r['evidence_items']:
                    supported_by.append(f"civic:eid{evidence_item['id']}")

            statement = schemas.Statement(
                id=f"{schemas.NamespacePrefix.CIVIC.value}:"
                   f"{r['name'].lower()}",
                description=r['description'],
                direction=self._get_evidence_direction(
                    r['evidence_direction']),
                evidence_level=evidence_level,
                proposition=proposition['id'],
                variation_origin=self._get_variation_origin(
                    r['variant_origin']),
                variation_descriptor=variant_id,
                therapy_descriptor=therapy_id,
                disease_descriptor=disease_id,
                method=method,
                supported_by=supported_by
            ).dict(exclude_none=True)
            self.transformed['statements'].append(statement)

    def _get_evidence_direction(self, direction) -> Optional[str]:
        """Return the evidence direction.

        :param str direction: The civic evidence_direction value
        :return: `supports` or `does_not_support` or None
        """
        if direction == 'Supports':
            return schemas.Direction.SUPPORTS.value
        elif direction == 'Does Not Support':
            return schemas.Direction.DOES_NOT_SUPPORT.value
        else:
            return None

    def _get_assertion_evidence_level(self, assertion) -> Optional[str]:
        """Return evidence_level for CIViC assertion.

        :param dict assertion: CIViC Assertion
        :return: CIViC assertion evidence_level
        """
        evidence_level = None
        # TODO: CHECK
        if assertion['amp_level']:
            if assertion['amp_level'] == 'Not Applicable':
                evidence_level = None
            else:
                tier, level = assertion['amp_level'].split(' - ')
                tier = tier.split()[1]
                if tier == 'I':
                    tier = 1
                elif tier == 'II':
                    tier = 2
                elif tier == 'III':
                    tier = 3
                elif tier == 'IV':
                    tier = 4
                evidence_level = f"amp_asco_cap_2017_level:" \
                                 f"{tier}{level.split()[1]}"
        return evidence_level

    def _get_proposition(self, record, variation_descriptor,
                         disease_descriptor, therapy_descriptor,
                         propositions_documents_ix) -> Optional[dict]:
        """Return a proposition for a record.

        :param dict record: CIViC EID or AID
        :param dict variation_descriptor: The record's variation descriptor
        :param dict disease_descriptor: The record's disease descriptor
        :param dict therapy_descriptor: The record's therapy descriptor
        :param dict propositions_documents_ix: Indexes for propositions and
            documents
        :return: A proposition
        """
        proposition_type = \
            self._get_proposition_type(record['evidence_type'])

        predicate = self._get_predicate(proposition_type,
                                        record['clinical_significance'])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return None

        params = {
            'id': '',
            'type': proposition_type,
            'predicate': predicate,
            'subject': variation_descriptor['value_id'],
            'object_qualifier': disease_descriptor['value']['id']
        }

        if proposition_type == schemas.PropositionType.PROGNOSTIC.value:
            proposition = \
                schemas.PrognosticProposition(**params).dict(exclude_none=True)
        elif proposition_type == schemas.PropositionType.PREDICTIVE.value:
            params['object'] = therapy_descriptor['value']['id']
            proposition =\
                schemas.TherapeuticResponseProposition(**params).dict(
                    exclude_none=True
                )
        elif proposition_type == schemas.PropositionType.DIAGNOSTIC.value:
            proposition = \
                schemas.DiagnosticProposition(**params).dict(
                    exclude_none=True)

        # Get corresponding id for proposition
        key = (proposition['type'],
               proposition['predicate'],
               proposition['subject'],
               proposition['object_qualifier'])
        if proposition_type == schemas.PropositionType.PREDICTIVE.value:
            key = key + (proposition['object'],)
        proposition_index = self._set_ix(propositions_documents_ix,
                                         'propositions', key)
        proposition['id'] = f"proposition:{proposition_index:03}"

        return proposition

    def _get_proposition_type(self, evidence_type, is_evidence=True) -> str:
        """Return proposition type for a given EID or AID.

        :param str evidence_type: CIViC evidence type
        :param bool is_evidence: `True` if EID. `False` if AID.
        :return: Proposition's type
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

    def _get_variation_origin(self, variant_origin) -> Optional[str]:
        """Return variant origin.

        :param str variant_origin: CIViC variant origin
        :return: Variation origin
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

    def _get_predicate(self, proposition_type, clin_sig) -> Optional[str]:
        """Return predicate for an evidence item.

        :param str proposition_type: The proposition type
        :param str clin_sig: The evidence item's clinical significance
        :return: Predicate for proposition
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
            logger.warning(f"CIViC proposition type: {proposition_type} "
                           f"not supported in Predicate schemas")
        return predicate

    def _add_variation_descriptors(self, variants, vids) -> None:
        """Add Variation Descriptors to dict of transformations.

        :param list variants: CIViC variants
        :param set vids: Candidate CIViC Variant IDs
        """
        for variant in variants:
            if variant['id'] not in vids:
                continue
            variant_id = f"civic:vid{variant['id']}"
            normalizer_responses = list()
            variant_query = f"{variant['entrez_name']} {variant['name']}"
            hgvs_exprs = self._get_hgvs_expr(variant)

            # TODO: Remove as more get implemented in variant normalizer
            #  Filtering to speed up transformation
            vname_lower = variant['name'].lower()

            if vname_lower.endswith('fs') or vname_lower.endswith('del') or '-' in vname_lower or '/' in vname_lower:  # noqa: E501
                if not hgvs_exprs:
                    logger.warning("Variant Normalizer does not support "
                                   f"{variant_id}: {variant_query}")
                    continue

            unable_to_normalize = {
                'mutation', 'amplification', 'exon', 'overexpression',
                'frameshift', 'promoter', 'deletion', 'type', 'insertion',
                'expression', 'duplication', 'copy', 'underexpression',
                'number', 'variation', 'repeat', 'rearrangement', 'activation',
                'expression', 'mislocalization', 'translocation', 'wild',
                'polymorphism', 'frame', 'shift', 'loss', 'function', 'levels',
                'inactivation', 'snp', 'fusion', 'dup', 'truncation',
                'homozygosity', 'gain', 'phosphorylation',
            }

            if set(vname_lower.split()) & unable_to_normalize:
                if not hgvs_exprs:
                    logger.warning("Variant Normalizer does not support "
                                   f"{variant_id}: {variant_query}")
                    continue

            # If c. in variant name, this indicates transcript
            # Otherwise it indicates protein or genomic
            transcript_queries = list()
            genomic_queries = list()
            protein_queries = list()
            for expr in hgvs_exprs:
                if 'protein' in expr['syntax']:
                    protein_queries.append(expr['value'])
                elif 'genomic' in expr['syntax']:
                    genomic_queries.append(expr['value'])
                else:
                    transcript_queries.append(expr['value'])

            # Order based on type of variant we think it is in order to
            # give corresponding value_id/value.
            if 'c.' in variant_query:
                queries = \
                    transcript_queries + genomic_queries + [variant_query] + \
                    protein_queries
            else:
                queries = \
                    protein_queries + genomic_queries + \
                    [variant_query] + transcript_queries

            variant_norm_resp = self.vicc_normalizers.normalize_variant(
                queries, normalizer_responses
            )

            if not variant_norm_resp:
                logger.warning(
                    "Variant Normalizer unable to find MANE transcript "
                    f"for civic:vid{variant['id']} : {variant_query}"
                )

            # Couldn't find MANE transcript
            if not variant_norm_resp and len(normalizer_responses) > 0:
                variant_norm_resp = normalizer_responses[0]
            elif not variant_norm_resp and len(normalizer_responses) == 0:
                logger.warning("Variant Normalizer unable to normalize: "
                               f"civic:vid{variant['id']} using queries "
                               f"{queries}")
                continue

            if variant['variant_types']:
                structural_type = variant['variant_types'][0]['so_id']
            else:
                structural_type = None

            variation_descriptor = schemas.VariationDescriptor(
                id=variant_id,
                label=variant['name'],
                description=variant['description'] if variant['description'] else None,  # noqa: E501
                value_id=variant_norm_resp.value_id,
                value=variant_norm_resp.value,
                gene_context=f"civic:gid{variant['gene_id']}",
                structural_type=structural_type,
                expressions=hgvs_exprs,
                xrefs=self._get_variant_xrefs(variant),
                alternate_labels=[v_alias for v_alias in
                                  variant['variant_aliases'] if not
                                  v_alias.startswith('RS')],
                extensions=self._get_variant_extensions(variant)
            ).dict(exclude_none=True)
            self.valid_ids['variation_descriptors'][variant_id] = \
                variation_descriptor
            self.transformed['variation_descriptors'].append(
                variation_descriptor
            )

    def _get_variant_extensions(self, variant) -> list:
        """Return a list of extensions for a variant.

        :param dict variant: A CIViC variant record
        :return: A list of extensions
        """
        extensions = [
            schemas.Extension(
                name='civic_representative_coordinate',
                value={k: v for k, v in variant['coordinates'].items()
                       if v is not None}
            ).dict(exclude_none=True),
            schemas.Extension(
                name='civic_actionability_score',
                value=variant['civic_actionability_score']
            ).dict(exclude_none=True)
        ]

        variant_groups = variant['variant_groups']
        if variant_groups:
            v_groups = list()
            for v_group in variant_groups:
                params = {
                    'id': f"civic:vgid{v_group['id']}",
                    'label': v_group['name'],
                    'description': v_group['description'],
                    'type': 'variant_group'
                }
                if v_group['description'] == '':
                    del params['description']
                v_groups.append(params)
            extensions.append(schemas.Extension(
                name='variant_group',
                value=v_groups
            ).dict(exclude_none=True))
        return extensions

    def _get_variant_xrefs(self, v) -> Optional[List[str]]:
        """Return a list of xrefs for a variant.

        :param dict v: A CIViC variant record
        :return: A dictionary of xrefs
        """
        xrefs = []
        for xref in ['clinvar_entries', 'allele_registry_id',
                     'variant_aliases']:
            if xref == 'clinvar_entries':
                for clinvar_entry in v['clinvar_entries']:
                    if clinvar_entry and clinvar_entry not in ['N/A',
                                                               "NONE FOUND"]:
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

    def _get_hgvs_expr(self, variant) -> Optional[List[Dict[str, str]]]:
        """Return a list of hgvs expressions for a given variant.

        :param dict variant: A CIViC variant record
        :return: A list of hgvs expressions
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
                    schemas.Expression(syntax=syntax,
                                       value=hgvs_expr).dict(exclude_none=True)
                )
        return hgvs_expressions

    def _add_gene_descriptors(self, genes) -> None:
        """Add Gene Descriptors to dict of transformations.

        :param list genes: CIViC genes
        """
        for gene in genes:
            gene_id = f"civic:gid{gene['id']}"
            ncbigene = f"ncbigene:{gene['entrez_id']}"
            queries = [ncbigene, gene['name']] + gene['aliases']

            _, normalized_gene_id = \
                self.vicc_normalizers.normalize_gene(queries)

            if normalized_gene_id:
                gene_descriptor = schemas.GeneDescriptor(
                    id=gene_id,
                    label=gene['name'],
                    description=gene['description'] if gene['description'] else None,  # noqa: E501
                    value=schemas.Gene(id=normalized_gene_id),
                    alternate_labels=gene['aliases'],
                    xrefs=[ncbigene]
                ).dict(exclude_none=True)
                self.transformed['gene_descriptors'].append(gene_descriptor)
            else:
                logger.warning(f"Gene Normalizer unable to normalize {gene_id}"
                               f"using queries: {queries}")

    def _add_disease_descriptor(self, disease_id, record) \
            -> Optional[schemas.ValueObjectDescriptor]:
        """Add disease ID to list of valid or invalid transformations.

        :param str disease_id: The CIViC ID for the disease
        :param dict record: CIViC AID or EID
        :return: A disease descriptor
        """
        disease_descriptor = \
            self.valid_ids['disease_descriptors'].get(disease_id)
        if disease_descriptor:
            return disease_descriptor
        else:
            disease_descriptor = None
            if disease_id not in self.invalid_ids['disease_descriptors']:
                disease_descriptor = \
                    self._get_disease_descriptors(record['disease'])
                if disease_descriptor:
                    self.valid_ids['disease_descriptors'][disease_id] = \
                        disease_descriptor
                else:
                    self.invalid_ids['disease_descriptors'].append(disease_id)
            return disease_descriptor

    def _get_disease_descriptors(self, disease) \
            -> Optional[schemas.ValueObjectDescriptor]:
        """Get a disease descriptor.

        :param dict disease: A CIViC disease record
        :return: A Disease Descriptor
        """
        if not disease:
            return None

        disease_id = f"civic:did{disease['id']}"
        display_name = disease['display_name']
        doid = disease['doid']

        if not doid:
            logger.warning(f"{disease_id} ({display_name}) has null DOID")
            queries = [display_name]
            xrefs = []
        else:
            doid = f"DOID:{disease['doid']}"
            queries = [doid, display_name]
            xrefs = [doid]

        _, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.warning(f"Disease Normalizer unable to normalize: "
                           f"{disease_id} using queries {queries}")
            return None

        disease_descriptor = schemas.ValueObjectDescriptor(
            id=disease_id,
            type="DiseaseDescriptor",
            label=display_name,
            value=schemas.Disease(id=normalized_disease_id),
            xrefs=xrefs if xrefs else None
        ).dict(exclude_none=True)
        return disease_descriptor

    def _add_therapy_descriptor(self, therapy_id, record)\
            -> Optional[schemas.ValueObjectDescriptor]:
        """Add therapy ID to list of valid or invalid transformations.

        :param str therapy_id: The CIViC ID for the drug
        :param dict record: CIViC AID or EID
        :return: A therapy descriptor
        """
        therapy_descriptor = \
            self.valid_ids['therapy_descriptors'].get(therapy_id)
        if therapy_descriptor:
            return therapy_descriptor
        else:
            therapy_descriptor = None
            if therapy_id not in self.invalid_ids['therapy_descriptors']:
                therapy_descriptor = \
                    self._get_therapy_descriptor(record['drugs'][0])
                if therapy_descriptor:
                    self.valid_ids['therapy_descriptors'][therapy_id] = \
                        therapy_descriptor
                else:
                    self.invalid_ids['therapy_descriptors'].append(therapy_id)
            return therapy_descriptor

    def _get_therapy_descriptor(self, drug) \
            -> Optional[schemas.ValueObjectDescriptor]:
        """Get a therapy descriptor.

        :param dict drug: A CIViC drug record
        :return: A Therapy Descriptor
        """
        therapy_id = f"civic:tid{drug['id']}"
        label = drug['name']
        ncit_id = f"ncit:{drug['ncit_id']}"
        queries = [ncit_id, label]

        _, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy(queries)

        if not normalized_therapy_id:
            logger.warning(f"Therapy Normalizer unable to normalize: "
                           f"using queries {ncit_id} and {label}")
            return None

        therapy_descriptor = schemas.ValueObjectDescriptor(
            id=therapy_id,
            type="TherapyDescriptor",
            label=label,
            value=schemas.Drug(id=normalized_therapy_id),
            alternate_labels=drug['aliases'],
            xrefs=[ncit_id]
        ).dict(exclude_none=True)
        return therapy_descriptor

    def _add_methods(self) -> None:
        """Add methods to list of transformations."""
        self.transformed['methods'] = [
            schemas.Method(
                id=f'method:'
                   f'{schemas.MethodID.CIVIC_EID_SOP:03}',
                label='Standard operating procedure for curation and clinical'
                      ' interpretation of variants in cancer',
                url='https://genomemedicine.biomedcentral.com/articles/'
                    '10.1186/s13073-019-0687-x',
                version=schemas.Date(year=2019, month=11, day=29).dict(),
                authors='Danos, A.M., Krysiak, K., Barnell, E.K. et al.'
            ).dict(exclude_none=True),
            schemas.Method(
                id=f'method:'
                   f'{schemas.MethodID.CIVIC_AID_AMP_ASCO_CAP.value:03}',
                label='Standards and Guidelines for the '
                      'Interpretation and Reporting of Sequence '
                      'Variants in Cancer: A Joint Consensus '
                      'Recommendation of the Association '
                      'for Molecular Pathology, American Society of '
                      'Clinical Oncology, and College of American '
                      'Pathologists',
                url='https://pubmed.ncbi.nlm.nih.gov/27993330/',
                version=schemas.Date(year=2017,
                                     month=1).dict(exclude_none=True),
                authors='Li MM, Datto M, Duncavage EJ, et al.'
            ).dict(exclude_none=True),
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
                version=schemas.Date(year=2015,
                                     month=5).dict(exclude_none=True),
                authors='Richards S, Aziz N, Bale S, et al.'
            ).dict(exclude_none=True)
        ]

    def _get_eid_document(self, source) -> Optional[schemas.Document]:
        """Get an EID's document.

        :param dict source: An evidence item's source
        :return: Document for EID
        """
        document = None
        source_type = source['source_type'].upper()
        if source_type in schemas.SourcePrefix.__members__:
            prefix = schemas.SourcePrefix[source_type].value
            document_id = f"{prefix}:{source['citation_id']}"
            xrefs = []
            if source['asco_abstract_id']:
                xrefs.append(f"asco.abstract:{source['asco_abstract_id']}")
            if source['pmc_id']:
                xrefs.append(f"pmc:{source['pmc_id']}")

            document = schemas.Document(
                id=document_id,
                label=source['citation'],
                description=source['name'],
                xrefs=xrefs if xrefs else None
            ).dict(exclude_none=True)
        else:
            logger.warning(f"{source_type} not in schemas.SourcePrefix")
        return document

    def _get_aid_document(self, assertion, propositions_documents_ix) \
            -> List[schemas.Document]:
        """Get an AID's documents.

        :param dict assertion: A CIViC Assertion
        :param propositions_documents_ix: Keeps track of proposition and
            documents indexes
        :return: A list of AID documents
        """
        # NCCN Guidlines
        documents = list()
        label = assertion['nccn_guideline']
        version = assertion['nccn_guideline_version']
        if label and version:
            document_id = '_'.join((label + version).split())
            document_ix = \
                self._set_ix(propositions_documents_ix, 'documents',
                             document_id)
            documents = list()
            documents.append(schemas.Document(
                id=f"document:{document_ix:03}",
                document_id="https://www.nccn.org/professionals/"
                            "physician_gls/default.aspx",
                label=f"NCCN Guidelines: {label} version {version}"
            ).dict(exclude_none=True))

        # TODO: Check this after first pass
        # ACMG Codes
        if assertion['acmg_codes']:
            for acmg_code in assertion['acmg_codes']:
                document_id = f"acmg:{acmg_code['code']}"
                documents.append(schemas.Document(
                    id=document_id,
                    label=acmg_code['code'],
                    description=acmg_code['description']
                ).dict(exclude_none=True))

        return documents

    def _set_ix(self, propositions_documents_ix, dict_key, search_key) -> int:
        """Set indexes for documents or propositions.

        :param dict propositions_documents_ix: Keeps track of
            proposition and documents indexes
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
