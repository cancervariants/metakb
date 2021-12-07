"""Module for queries."""
from typing import Dict
from ga4gh.vrsatile.pydantic.vrsatile_model import Extension, Expression
from metakb.normalizers import VICCNormalizers
from metakb.schemas import SearchService, StatementResponse, \
    TherapeuticResponseProposition, VariationDescriptor, \
    ValueObjectDescriptor, GeneDescriptor, Method, \
    Document, SearchIDService, DiagnosticProposition, PrognosticProposition, \
    SearchStatementsService, NestedStatementResponse
import logging
from metakb.database import Graph
import json
from json.decoder import JSONDecodeError
from urllib.parse import quote


logger = logging.getLogger('metakb.query')
logger.setLevel(logging.DEBUG)


class QueryHandler:
    """Class for handling queries."""

    def __init__(self):
        """Initialize neo4j driver and the VICC normalizers."""
        self.driver = Graph().driver
        self.vicc_normalizers = VICCNormalizers()

    def get_normalized_therapy(self, therapy, warnings):
        """Get normalized therapy concept.

        :param str therapy: Therapy query
        :param list warnings: A list of warnings for the search query
        :return: A normalized therapy concept string if concept exists in
            thera-py, else `None`
        """
        _, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy([therapy])

        if not normalized_therapy_id:
            warnings.append(f'Therapy Normalizer unable to normalize: '
                            f'{therapy}')
        return normalized_therapy_id

    def get_normalized_disease(self, disease, warnings):
        """Get normalized disease concept.

        :param str disease: Disease query
        :param list warnings: A list of warnings for the search query
        :return: A normalized disease concept string if concept exists in
            disease-normalizer, else `None`
        """
        _, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease([disease])

        if not normalized_disease_id:
            warnings.append(f'Disease Normalizer unable to normalize: '
                            f'{disease}')
        return normalized_disease_id

    def get_normalized_variation(self, variation, warnings):
        """Get normalized variation concept.

        :param str variation: Variation query
        :param list warnings: A list of warnings for the search query
        :return: A normalized variant concept string if concept exists in
            variant-normalizer, else `None`
        """
        variant_norm_resp = \
            self.vicc_normalizers.normalize_variation([variation])
        normalized_variation = None
        if variant_norm_resp:
            normalized_variation = variant_norm_resp['variation_id']
        if not normalized_variation:
            # Check if VRS variation (allele, cnv, or haplotype)
            if variation.startswith(("ga4gh:VA.", "ga4gh:CNV.", "ga4gh:VH.")):
                normalized_variation = variation
            else:
                warnings.append(f'Variant Normalizer unable to normalize: '
                                f'{variation}')
        return normalized_variation

    def get_normalized_gene(self, gene, warnings):
        """Get normalized gene concept.

        :param str gene: Gene query
        :param list warnings: A list of warnings for the search query.
        :return: A normalized gene concept string if concept exists in
            gene-normalizer, else `None`
        """
        _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
        if not normalized_gene_id:
            warnings.append(f'Gene Normalizer unable to normalize: {gene}')
        return normalized_gene_id

    def get_normalized_terms(self, variation, disease, therapy, gene,
                             statement_id, response):
        """Find normalized terms for queried concepts.

        :param str variation: Variation (subject) query
        :param str disease: Disease (object_qualifier) query
        :param str therapy: Therapy (object) query
        :param str gene: Gene query
        :param str statement_id: Statement ID query
        :param Dict response: The search response
        :return: A tuple containing the normalized concepts if it exists, else
            None
        """
        if not (variation or disease or therapy or gene or statement_id):
            response['warnings'].append('No parameters were entered.')
            return None

        # Find normalized terms using VICC normalizers
        if therapy:
            response['query']['therapy'] = therapy
            normalized_therapy = \
                self.get_normalized_therapy(therapy.strip(),
                                            response['warnings'])
        else:
            normalized_therapy = None
        if disease:
            response['query']['disease'] = disease
            normalized_disease = \
                self.get_normalized_disease(disease.strip(),
                                            response['warnings'])
        else:
            normalized_disease = None
        if variation:
            response['query']['variation'] = variation
            normalized_variation = \
                self.get_normalized_variation(variation,
                                              response['warnings'])
        else:
            normalized_variation = None
        if gene:
            response['query']['gene'] = gene
            normalized_gene = self.get_normalized_gene(gene,
                                                       response['warnings'])
        else:
            normalized_gene = None

        valid_statement_id = None
        statement = None
        if statement_id:
            response['query']['statement_id'] = statement_id
            with self.driver.session() as session:
                statement = session.read_transaction(
                    self._get_statement_by_id, statement_id
                )
                if statement:
                    valid_statement_id = statement.get('id')
                else:
                    response['warnings'].append(
                        f"Statement: {statement_id} does not exist.")

        if (variation and not normalized_variation) or \
                (therapy and not normalized_therapy) or \
                (disease and not normalized_disease) or \
                (gene and not normalized_gene) or \
                (statement_id and not valid_statement_id):
            return None

        return (normalized_variation, normalized_disease, normalized_therapy,
                normalized_gene, statement, valid_statement_id)

    def search(self, variation='', disease='', therapy='', gene='',
               statement_id='', detail=False):
        """Get statements and propositions from queried concepts.

        :param str variation: Variation query
        :param str disease: Disease query
        :param str therapy: Therapy query
        :param str gene: Gene query
        :param str statement_id: Statement ID query
        :param bool detail: Whether or not to display all descriptors,
        methods, and documents
        :return: A dictionary containing the statements and propositions
            with relationships to the queried concepts
        """
        response: Dict = {
            'query': {
                'variation': None,
                'disease': None,
                'therapy': None,
                'gene': None,
                'statement_id': None,
                'detail': detail
            },
            'warnings': [],
            'matches': {
                "statements": [],
                "propositions": []
            },
            'statements': [],  # All Statements
            'propositions': [],  # All propositions
            'variation_descriptors': [],
            'gene_descriptors': [],
            'therapy_descriptors': [],
            'disease_descriptors': [],
            'methods': [],
            'documents': []
        }

        normalized_terms = self.get_normalized_terms(
            variation, disease, therapy, gene, statement_id, response)
        if normalized_terms is None:
            return SearchService(**response).dict()
        (normalized_variation, normalized_disease,
         normalized_therapy, normalized_gene, statement,
         valid_statement_id) = normalized_terms

        session = self.driver.session()
        proposition_nodes = session.read_transaction(
            self._get_propositions, normalized_therapy,
            normalized_variation, normalized_disease, normalized_gene,
            valid_statement_id
        )

        if not valid_statement_id:
            # If statement ID isn't specified, get all statements
            # related to a proposition
            statement_nodes = list()
            for p_node in proposition_nodes:
                p_id = p_node.get('id')
                if p_id not in response['matches']['propositions']:
                    response['matches']['propositions'].append(p_id)
                statements = session.read_transaction(
                    self._get_statements_from_proposition, p_id
                )
                for s in statements:
                    statement_nodes.append(s)
                    s_id = s.get('id')
                    if s_id not in response['matches']['statements']:
                        response['matches']['statements'].append(s_id)
        else:
            # Given Statement ID
            statement_nodes = [statement]
            s_id = statement.get('id')
            response['matches']['statements'].append(s_id)

            for p in proposition_nodes:
                p_id = p.get('id')
                if p_id not in response['matches']['propositions']:
                    response['matches']['propositions'].append(p_id)

        # Add statements found in `supported_by` to statement_nodes
        # Then add the associated proposition to proposition_nodes
        for s in statement_nodes:
            self.add_proposition_and_statement_nodes(
                session, s.get('id'), proposition_nodes, statement_nodes
            )

        if proposition_nodes and statement_nodes:
            response['statements'] = \
                self.get_statement_response(statement_nodes)
            response['propositions'] = \
                self.get_propositions_response(proposition_nodes)
        else:
            response['warnings'].append('Could not find statements '
                                        'associated with the queried'
                                        ' concepts.')

        if detail:
            for s in response['statements']:
                response['variation_descriptors'].append(
                    self._get_variation_descriptor(
                        response,
                        session.read_transaction(
                            self._find_node_by_id,
                            s['variation_descriptor']
                        )
                    )
                )
                if 'therapy_descriptor' in s.keys():
                    response['therapy_descriptors'].append(
                        self._get_therapy_descriptor(
                            session.read_transaction(
                                self._find_node_by_id, s['therapy_descriptor']
                            )
                        )
                    )
                else:
                    response['therapy_descriptors'] = []

                response['disease_descriptors'].append(
                    self._get_disease_descriptor(
                        session.read_transaction(
                            self._find_node_by_id, s['disease_descriptor']
                        )
                    )
                )

                response['methods'].append(
                    self._get_method(
                        session.read_transaction(
                            self._find_node_by_id, s['method']
                        )
                    )
                )

                # Sometimes CIViC AIDs have supported by statements
                # that we aren't able to transform
                sb_not_found = set()
                for sb_id in s['supported_by']:
                    try:
                        document = self._get_document(
                            session.read_transaction(
                                self._find_node_by_id, sb_id
                            )
                        )
                        if document:
                            response['documents'].append(document)
                    except ValueError:
                        sb_not_found.add(sb_id)
                if sb_not_found:
                    response['warnings'].append(f"Supported by evidence not "
                                                f"yet  supported in MetaKB: "
                                                f"{sb_not_found} for "
                                                f"{s['id']}")
        else:
            response['variation_descriptors'] = None
            response['gene_descriptors'] = None
            response['disease_descriptors'] = None
            response['therapy_descriptors'] = None
            response['methods'] = None
            response['documents'] = None

        session.close()
        return SearchService(**response).dict(exclude_none=True)

    def search_by_id(self, node_id):
        """Get node information from queried concepts.

        :param str node_id: node_id
        :return: A dictionary containing the node content
        """
        valid_node_id = None
        response = {
            'query': node_id,
            'warnings': []
        }

        if not node_id:
            response['warnings'].append("No parameters were entered.")
        elif node_id.strip() == '':
            response['warnings'].append("Cannot enter empty string.")
        else:
            node_id = node_id.strip()
            if '%' not in node_id and ':' in node_id:
                concept_name = quote(node_id.split(":", 1)[1])
                node_id = \
                    f"{node_id.split(':', 1)[0]}" \
                    f":{concept_name}"
            with self.driver.session() as session:
                node = session.read_transaction(
                    self._find_node_by_id, node_id
                )
                if node:
                    valid_node_id = node.get('id')
                else:
                    response['warnings'].append(f"Node: {node_id} "
                                                f"does not exist.")
        if (not node_id and not valid_node_id) or \
                (node_id and not valid_node_id):
            return SearchIDService(**response).dict(exclude_none=True)

        label, *_ = node.labels
        if label == 'Statement':
            statement = self._get_statement(node)
            if statement:
                response["statement"] = statement
        elif label in ['Proposition', 'TherapeuticResponse',
                       'Prognostic', 'Diagnostic']:
            proposition = self._get_proposition(node)
            if proposition:
                response["proposition"] = proposition
        elif label == 'VariationDescriptor':
            response['variation_descriptor'] = \
                self._get_variation_descriptor(response, node)
        elif label == 'TherapyDescriptor':
            response['therapy_descriptor'] = \
                self._get_therapy_descriptor(node)
        elif label == 'DiseaseDescriptor':
            response['disease_descriptor'] = self._get_disease_descriptor(node)
        elif label == 'GeneDescriptor':
            response['gene_descriptor'] = \
                self._get_gene_descriptor(node, self._get_gene_value_object(node))  # noqa: E501
        elif label == 'Document':
            document = self._get_document(node)
            if document:
                response['document'] = document
        elif label == 'Method':
            response['method'] = self._get_method(node)

        session.close()
        return SearchIDService(**response).dict(exclude_none=True)

    def search_statements(
            self, variation='', disease='', therapy='', gene='',
            statement_id=''):
        """Get nested statements from queried concepts

        :param str variation: Variation query
        :param str disease: Disease query
        :param str therapy: Therapy query
        :param str gene: Gene query
        :param str statement_id: Statement ID query
        :return: A dictionary containing the statements with nested
            propositions, descriptors, methods, and supported by documents
        """
        response: Dict = {
            'query': {
                'variation': None,
                'disease': None,
                'therapy': None,
                'gene': None,
                'statement_id': None
            },
            'warnings': [],
            'matches': {
                "statements": [],
                "propositions": []
            },
            'statements': []
        }

        normalized_terms = self.get_normalized_terms(
            variation, disease, therapy, gene, statement_id, response)
        if normalized_terms is None:
            return SearchStatementsService(**response).dict()
        (normalized_variation, normalized_disease,
         normalized_therapy, normalized_gene, statement,
         valid_statement_id) = normalized_terms

        session = self.driver.session()
        statement_nodes = list()
        proposition_nodes = session.read_transaction(
            self._get_propositions, normalized_therapy,
            normalized_variation, normalized_disease, normalized_gene,
            valid_statement_id
        )

        proposition_cache = dict()
        if not valid_statement_id:
            # If statement ID isn't specified, get all statements
            # related to a proposition
            for p_node in proposition_nodes:
                self._add_to_proposition_cache(
                    session, p_node, proposition_cache)
                statements = session.read_transaction(
                    self._get_statements_from_proposition, p_node.get('id')
                )
                for s in statements:
                    statement_nodes.append(s)
        else:
            # Given Statement ID
            statement_nodes.append(statement)
            p_node = proposition_nodes[0]
            self._add_to_proposition_cache(session, p_node, proposition_cache)

        # Add statements found in `supported_by` to statement_nodes
        # Then add the associated proposition to proposition_nodes
        og_prop_nodes_len = len(proposition_nodes)
        for s in statement_nodes:
            self.add_proposition_and_statement_nodes(
                session, s.get('id'), proposition_nodes, statement_nodes
            )

            if og_prop_nodes_len != len(proposition_nodes):
                for p_node in proposition_nodes:
                    self._add_to_proposition_cache(
                        session, p_node, proposition_cache)

        methods_cache = dict()
        variations_cache = dict()
        disease_cache = dict()
        therapy_cache = dict()
        document_cache = dict()

        for s in statement_nodes:

            s_id = s.get('id')
            statement_resp = session.read_transaction(
                self._find_and_return_statement_response, s_id
            )
            p_id = statement_resp.get('p_id')

            proposition = proposition_cache[p_id]

            method_id = statement_resp['m']['id']
            if method_id in methods_cache:
                method = methods_cache[method_id]
            else:
                method = self.search_by_id(method_id)['method']
                methods_cache[method_id] = method

            variation_id = statement_resp['vid']
            if variation_id in variations_cache:
                variation_descr = variations_cache[variation_id]
            else:
                variation_descr = self._get_variation_descriptor(
                    {},
                    session.read_transaction(
                        self._find_node_by_id, variation_id),
                    gene_context_by_id=False
                )
                variations_cache[variation_id] = variation_descr

            if proposition.type == 'therapeutic_response_proposition':
                therapy_id = statement_resp.get('tid')
                if therapy_id in therapy_cache:
                    therapy_descr = therapy_cache[therapy_id]
                else:
                    therapy_descr = self._get_therapy_descriptor(
                        session.read_transaction(self._find_node_by_id,
                                                 therapy_id)
                    )
                    therapy_cache[therapy_id] = therapy_descr
            else:
                therapy_descr = None

            disease_id = statement_resp.get('did')
            if disease_id in disease_cache:
                disease_descr = disease_cache[disease_id]
            else:
                disease_descr = self._get_disease_descriptor(
                    session.read_transaction(self._find_node_by_id,
                                             disease_id)
                )
                disease_cache[disease_id] = disease_descr

            supported_by = list()
            sb_not_found = set()
            sb_list = session.read_transaction(
                self._find_and_return_supported_by, s_id
            )
            for sb in sb_list:
                sb_id = sb.get('id')
                try:
                    if sb_id in document_cache:
                        document = document_cache[sb_id]
                    else:
                        document = self._get_document(
                            session.read_transaction(
                                self._find_node_by_id, sb_id
                            )
                        )

                    if document:
                        supported_by.append(document)
                        document_cache[sb_id] = document
                    else:
                        if sb_id.startswith('civic.eid'):
                            supported_by.append(sb_id)
                except ValueError:
                    sb_not_found.add(sb_id)
            if sb_not_found:
                response['warnings'].append(f"Supported by evidence not "
                                            f"yet  supported in MetaKB: "
                                            f"{sb_not_found} for "
                                            f"{s['id']}")

            params = {
                'id': s_id,
                'description': statement.get('description'),
                'direction': statement.get('direction'),
                'evidence_level': statement.get('evidence_level'),
                'variation_origin': statement.get('variation_origin'),
                'proposition': proposition,
                'variation_descriptor': variation_descr,
                'therapy_descriptor': therapy_descr,
                'disease_descriptor': disease_descr,
                'method': method,
                'supported_by': supported_by
            }
            response['statements'].append(
                NestedStatementResponse(**params).dict())
            response['matches']['statements'].append(s_id)
            response['matches']['propositions'].append(p_id)
        session.close()
        return response
        # return SearchStatementsService(**response).dict(exclude_none=True)

    def _add_to_proposition_cache(self, session, p_node, proposition_cache):
        p_id = p_node.get('id')
        if p_id not in proposition_cache:
            proposition_resp = session.read_transaction(
                self._find_and_return_proposition_response,
                p_id
            )
            proposition_type = p_node.get('type')
            proposition = {
                'id': p_id,
                'type': proposition_type,
                'predicate': p_node.get('predicate'),
                'subject': proposition_resp['subject'],
                'object_qualifier': proposition_resp['object_qualifier']
            }
            if proposition_type == 'therapeutic_response_proposition':
                proposition['object'] = proposition_resp['object']
                proposition = \
                    TherapeuticResponseProposition(**proposition)
            elif proposition_type == "prognostic_proposition":
                proposition = PrognosticProposition(**proposition)
            elif proposition_type == "diagnostic_proposition":
                proposition = DiagnosticProposition(**proposition)
            proposition_cache[p_id] = proposition

    def _get_variation_descriptor(self, response, variation_descriptor,
                                  gene_context_by_id=True):
        """Add variation descriptor to response.
        :param Node variation_descriptor: Variation Descriptor Node
        """
        keys = variation_descriptor.keys()
        vid = variation_descriptor.get('id')
        vd_params = {
            'id': vid,
            'label': variation_descriptor.get('label'),
            'description': variation_descriptor.get('description'),
            'variation_id': None,
            'variation': None,
            'gene_context': None,
            'molecule_context': variation_descriptor.get('molecule_context'),
            'structural_type': variation_descriptor.get('structural_type'),
            'vrs_ref_allele_seq': variation_descriptor.get('vrs_ref_allele_seq'),  # noqa: E501
            'expressions': [],
            'xrefs': variation_descriptor.get('xrefs'),
            'alternate_labels': variation_descriptor.get('alternate_labels'),
            'extensions': []
        }

        # Get Gene Descriptor / gene context
        with self.driver.session() as session:
            gene_descriptor = session.read_transaction(
                self._get_variation_descriptors_gene, vd_params['id']
            )
            gene_descriptor_id = gene_descriptor.get('id')

            gene_value_object = session.read_transaction(
                self._find_descriptor_value_object,
                gene_descriptor_id
            )
            gene_context = self._get_gene_descriptor(
                gene_descriptor, gene_value_object)

            if gene_context_by_id:
                # Reference gene descr by id
                vd_params['gene_context'] = gene_descriptor_id
            else:
                # gene context will be gene desecriptor
                vd_params['gene_context'] = gene_context

            if 'gene_descriptors' in response and\
                    gene_descriptor_id not in response['gene_descriptors']:
                response['gene_descriptors'].append(gene_context)

        # Get Variation Descriptor Expressions
        for key in ['expressions_genomic', 'expressions_protein',
                    'expressions_transcript']:
            if key in keys:
                for value in variation_descriptor.get(key):
                    vd_params['expressions'].append(
                        Expression(
                            syntax=f"hgvs:{key.split('_')[-1]}",
                            value=value
                        ).dict()
                    )
        # Get Variation Descriptor Extensions
        if vd_params['id'].startswith('civic.vid'):
            for field in ['civic_representative_coordinate',
                          'civic_actionability_score']:
                if field in keys:
                    vd_params['extensions'].append(
                        Extension(
                            name=field,
                            value=json.loads(variation_descriptor.get(field))
                        ).dict()
                    )
            with self.driver.session() as session:
                variant_group = session.read_transaction(
                    self._get_variation_group, vid
                )
                if variant_group:
                    variant_group = variant_group[0]
                    vg = Extension(
                        name='variant_group',
                        value=[{
                            'id': variant_group.get('id'),
                            'label': variant_group.get('label'),
                            'description': variant_group.get('description'),
                            'type': 'variant_group'
                        }]
                    ).dict()
                    for v in vg['value']:
                        if not v['description']:
                            del v['description']
                    vd_params['extensions'].append(vg)
        elif vd_params['id'].startswith('moa.variant'):
            for field in ['moa_representative_coordinate', 'moa_rsid']:
                if field in keys:
                    vd_params['extensions'].append(
                        Extension(
                            name=field,
                            value=json.loads(variation_descriptor.get(field))
                        ).dict()
                    )

        with self.driver.session() as session:
            value_object = session.read_transaction(
                self._find_descriptor_value_object, vd_params['id']
            )
            vd_params['variation_id'] = value_object.get('id')
            vd_params['variation'] = json.loads(value_object['variation'])
        return VariationDescriptor(**vd_params)

    @staticmethod
    def _get_variation_group(tx, vid):
        """Get a variation descriptor's variation group."""
        query = (
            "MATCH (vd:VariationDescriptor)-[:IN_VARIATION_GROUP]->(vg:VariationGroup) "  # noqa: E501
            f"WHERE toLower(vd.id) = toLower('{vid}') "
            "RETURN vg"
        )
        return tx.run(query).single()

    @staticmethod
    def _get_variation_descriptors_gene(tx, vid):
        """Get a Variation Descriptor's Gene Descriptor."""
        query = (
            "MATCH (vd:VariationDescriptor)-[:HAS_GENE]->(gd:GeneDescriptor) "
            f"WHERE toLower(vd.id) = toLower('{vid}') "
            "RETURN gd"
        )
        return tx.run(query).single()[0]

    @staticmethod
    def _get_gene_descriptor(gene_descriptor, gene_value_object):
        """Add gene descriptor to response.

        :param Node gene_descriptor: Gene Descriptor Node
        :param Node gene_value_object: Gene Node
        """
        gd_params = {
            'id': gene_descriptor.get('id'),
            'type': 'GeneDescriptor',
            'label': gene_descriptor.get('label'),
            'description': gene_descriptor.get('description'),
            'gene_id': gene_value_object.get('id'),
            'alternate_labels': gene_descriptor.get('alternate_labels'),
            'xrefs': gene_descriptor.get('xrefs')
        }

        return GeneDescriptor(**gd_params)

    def _get_therapy_descriptor(self, therapy_descriptor):
        """Add therapy descriptor to response.

        :param Node therapy_descriptor: Therapy Descriptor Node
        """
        td_params = {
            'id': therapy_descriptor.get('id'),
            'type': 'TherapyDescriptor',
            'label': therapy_descriptor.get('label'),
            'therapy_id': None,
            'alternate_labels': therapy_descriptor.get('alternate_labels'),
            'xrefs': therapy_descriptor.get('xrefs')
        }

        with self.driver.session() as session:
            value_object = session.read_transaction(
                self._find_descriptor_value_object, td_params['id']
            )
            td_params['therapy_id'] = value_object.get('id')

        return ValueObjectDescriptor(**td_params)

    def _get_disease_descriptor(self, disease_descriptor):
        """Add disease descriptor to response.

        :param Node disease_descriptor: Disease Descriptor Node
        """
        dd_params = {
            'id': disease_descriptor.get('id'),
            'type': 'DiseaseDescriptor',
            'label': disease_descriptor.get('label'),
            'disease_id': None,
            'xrefs': disease_descriptor.get('xrefs')
        }

        with self.driver.session() as session:
            value_object = session.read_transaction(
                self._find_descriptor_value_object, dd_params['id']
            )
            dd_params['disease_id'] = value_object.get('id')

        return ValueObjectDescriptor(**dd_params)

    @staticmethod
    def _get_method(method):
        """Add method to response.

        :param Node method: Method Node
        """
        params = dict()
        for key in method.keys():
            try:
                params[key] = json.loads(method.get(key))
            except JSONDecodeError:
                params[key] = method.get(key)

        return Method(**params)

    @staticmethod
    def _get_document(document):
        """Add document to response.

        :param Node document: Document Node
        """
        label, *_ = document.labels
        if label != 'Document':
            return None

        params = dict()
        for key in document.keys():
            params[key] = document.get(key)
        return Document(**params)

    @staticmethod
    def _find_node_by_id(tx, node_id):
        """Find a node by its ID."""
        query = (
            "MATCH (n) "
            f"WHERE toLower(n.id) = toLower('{node_id}') "
            "RETURN n"
        )
        return (tx.run(query).single() or [None])[0]

    @staticmethod
    def _find_descriptor_value_object(tx, descriptor_id):
        """Find a Descriptor's value object."""
        query = (
            "MATCH (d)-[:DESCRIBES]->(v)"
            f"WHERE toLower(d.id) = toLower('{descriptor_id}') "
            "RETURN v"
        )
        return tx.run(query).single()[0]

    def add_proposition_and_statement_nodes(self, session, statement_id,
                                            proposition_nodes,
                                            statement_nodes):
        """Get statements found in `supported_by` and their propositions."""
        supported_by_statements = session.read_transaction(
            self._find_and_return_supported_by, statement_id,
            only_statement=True
        )
        for s in supported_by_statements:
            if s not in statement_nodes:
                statement_nodes.append(s)
                proposition = session.read_transaction(
                    self._find_and_return_propositions_from_statement,
                    s.get('id')
                )
                if proposition and proposition \
                        not in proposition_nodes:
                    proposition_nodes.append(proposition)

    @staticmethod
    def _get_statement_by_id(tx, statement_id):
        """Get a Statement node by ID."""
        query = (
            "MATCH (s:Statement) "
            f"WHERE toLower(s.id) = toLower('{statement_id}') "
            "RETURN s"
        )
        return (tx.run(query).single() or [None])[0]

    @staticmethod
    def _get_propositions(tx, normalized_therapy, normalized_variation,
                          normalized_disease, normalized_gene,
                          valid_statement_id):
        """Get propositions that contain normalized concepts queried."""
        query = ""
        if valid_statement_id:
            query += "MATCH (s:Statement {id:$s_id})-[:DEFINED_BY]->" \
                     "(p:Proposition) "
        if normalized_therapy:
            query += "MATCH (p:Proposition)<-[:IS_OBJECT_OF]-" \
                     "(t:Therapy {id:$t_id}) "
        if normalized_variation:
            lower_normalized_variation = normalized_variation.lower()
            query += "MATCH (p:Proposition)<-[:IS_SUBJECT_OF]-(a:Allele "
            if lower_normalized_variation.startswith('ga4gh:sq.'):
                # Sequence ID
                query += "{location_sequence_id: $v_id}) "
            else:
                query += "{id:$v_id}) "
        if normalized_disease:
            query += "MATCH (p:Proposition)<-[:IS_OBJECT_QUALIFIER_OF]-" \
                     "(d:Disease {id:$d_id}) "
        if normalized_gene:
            query += "MATCH (g:Gene {id:$g_id})<-[:DESCRIBES]-" \
                     "(gd:GeneDescriptor)<-[:HAS_GENE]-" \
                     "(vd:VariationDescriptor)-[:DESCRIBES]->(v:Allele)-" \
                     "[:IS_SUBJECT_OF]->(p:Proposition) "
        query += "RETURN DISTINCT p"

        return [p[0] for p in tx.run(query, t_id=normalized_therapy,
                                     v_id=normalized_variation,
                                     d_id=normalized_disease,
                                     g_id=normalized_gene,
                                     s_id=valid_statement_id)]

    @staticmethod
    def _get_statements_from_proposition(tx, proposition_id):
        """Get statements that are defined by a proposition."""
        query = (
            "MATCH (p:Proposition {id: $proposition_id})<-[:DEFINED_BY]-(s:Statement) "  # noqa: E501
            "RETURN DISTINCT s"
        )
        return [s[0] for s in tx.run(query, proposition_id=proposition_id)]

    def get_statement_response(self, statements):
        """Return a list of statements from Statement and Proposition nodes.

        :param list statements: A list of Statement Nodes
        :return: A list of dicts containing statement response output
        """
        statements_response = list()
        for s in statements:
            statements_response.append(
                self._get_statement(s)
            )
        return statements_response

    @staticmethod
    def _find_and_return_statement_response(tx, statement_id):
        """Return IDs and method related to a Statement."""
        queries = (
            ("MATCH (s)-[r1]->(td:TherapyDescriptor) ", "td.id AS tid,"),
            ("", "")
        )
        for q in queries:
            query = (
                "MATCH (s:Statement) "
                f"WHERE s.id = '{statement_id}' "
                f"{q[0]}"
                "MATCH (s)-[r2]->(vd:VariationDescriptor) "
                "MATCH (s)-[r3]->(dd:DiseaseDescriptor) "
                "MATCH (s)-[r4]->(m:Method) "
                "MATCH (s)-[r6]->(p:Proposition) "
                f"RETURN {q[1]} vd.id AS vid, dd.id AS did, m,"
                " p.id AS p_id"
            )
            result = tx.run(query).single()
            if result:
                return result
        return None

    def get_propositions_response(self, propositions):
        """Return a list of propositions from Proposition nodes.

        :param list propositions: A list of Proposition Nodes
        :return: A list of Propositions
        """
        propositions_response = list()
        for p in propositions:
            proposition = self._get_proposition(p)
            if proposition and proposition not in propositions_response:
                propositions_response.append(proposition)
        return propositions_response

    @staticmethod
    def _find_and_return_proposition_response(tx, proposition_id):
        """Return value ids from a proposition."""
        queries = (
            ("MATCH (n) -[r1]-> (t:Therapy) ", "t.id AS object,"), ("", "")
        )
        for q in queries:
            query = (
                f"MATCH (n) "
                f"WHERE n.id = '{proposition_id}' "
                f"{q[0]}"
                "MATCH (n) -[r2]-> (v:Variation) "
                "MATCH (n) -[r3]-> (d:Disease) "
                f"RETURN {q[1]} v.id AS subject, d.id AS object_qualifier"
            )
            result = tx.run(query).single()
            if result:
                return result
        return None

    @staticmethod
    def _find_and_return_supported_by(tx, statement_id, only_statement=False):
        """Statement and Document Nodes that support a given Statement.

        :param bool only_statement: `True` if only match on Statement,
            `False` if match on both Statement and Document
        """
        if not only_statement:
            match = "MATCH (s:Statement)-[:CITES]->(sb) "
        else:
            match = "MATCH (s:Statement)-[:CITES]->(sb:Statement) "
        query = (
            f"{match}"
            f"WHERE s.id = '{statement_id}' "
            "RETURN sb"
        )
        return [se[0] for se in tx.run(query)]

    @staticmethod
    def _find_and_return_propositions_from_statement(tx, statement_id):
        """Find propositions from a given statement."""
        query = (
            "MATCH (p:Proposition)<-[:DEFINED_BY]-(s:Statement) "
            f"WHERE toLower(s.id) = toLower('{statement_id}') "
            "RETURN p"
        )
        return (tx.run(query).single() or [None])[0]

    def _get_gene_value_object(self, node):
        """Get gene value object from gene descriptor object

        :param descriptor object node: gene descriptor object
        :return: gene value object
        """
        with self.driver.session() as session:
            gene_value_object = session.read_transaction(
                self._find_descriptor_value_object, node.get('id')
            )
        return gene_value_object

    def _get_proposition(self, p):
        """Return a proposition.

        :param Node p: Proposition Node
        :return: A proposition
        """
        with self.driver.session() as session:
            p_id = p.get('id')
            p_type = p.get('type')
            proposition = None
            value_ids = session.read_transaction(
                self._find_and_return_proposition_response, p_id
            )
            params = {
                "id": p_id,
                "type": p_type,
                "predicate": p.get("predicate"),
                "subject": value_ids["subject"],
                "object_qualifier": value_ids["object_qualifier"]
            }
            if p_type == "therapeutic_response_proposition":
                params["object"] = value_ids["object"]
                proposition = \
                    TherapeuticResponseProposition(**params)
            elif p_type == "prognostic_proposition":
                proposition = PrognosticProposition(**params)
            elif p_type == "diagnostic_proposition":
                proposition = DiagnosticProposition(**params)
            return proposition

    def _get_statement(self, s):
        """Return a statement.

        :param Node s: Statement Node
        """
        with self.driver.session() as session:
            statement_id = s.get('id')
            response = session.read_transaction(
                self._find_and_return_statement_response, statement_id)
            se_list = session.read_transaction(
                self._find_and_return_supported_by, statement_id)

            statement = StatementResponse(
                id=statement_id,
                description=s.get('description'),
                direction=s.get('direction'),
                evidence_level=s.get('evidence_level'),
                variation_origin=s.get('variation_origin'),
                proposition=response['p_id'],
                variation_descriptor=response['vid'],
                therapy_descriptor=response['tid'] if 'tid' in response.keys() else None,  # noqa: E501
                disease_descriptor=response['did'],
                method=response['m']['id'],
                supported_by=[se['id'] for se in se_list]
            ).dict(exclude_none=True)
            return statement
