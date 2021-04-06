"""Module for queries."""
from gene.query import QueryHandler as GeneQueryHandler
from variant.to_vrs import ToVRS
from variant.normalize import Normalize as VariantNormalizer
from variant.tokenizers.caches.amino_acid_cache import AminoAcidCache
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler
from metakb.schemas import SearchService, StatementResponse, \
    TherapeuticResponseProposition
import logging
from metakb.database import Graph


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class QueryHandler:
    """Class for handling queries."""

    def __init__(self):
        """Initialize neo4j driver and the VICC normalizers."""
        self.driver = Graph().driver
        self.gene_query_handler = GeneQueryHandler()
        self.variant_normalizer = VariantNormalizer()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()
        self.variant_to_vrs = ToVRS()
        self.amino_acid_cache = AminoAcidCache()

    def get_normalized_therapy(self, therapy, warnings):
        """Get normalized therapy concept.

        :param str therapy: Therapy query
        :param list warnings: A list of warnings for the search query
        :return: A normalized therapy concept string if concept exists in
            thera-py, else `None`
        """
        therapy_norm_resp = \
            self.therapy_query_handler.search_groups(therapy)

        normalized_therapy = None
        if therapy_norm_resp['match_type'] != 0:
            therapy_norm_resp = therapy_norm_resp[
                'value_object_descriptor']
            therapy_norm_id = therapy_norm_resp['value']['therapy_id']
            if not therapy_norm_id.startswith('ncit'):
                therapy_norm_id = None
                if 'xrefs' in therapy_norm_resp:
                    for other_id in therapy_norm_resp['xrefs']:
                        if other_id.startswith('ncit:'):
                            therapy_norm_id = other_id

            if therapy_norm_id:
                normalized_therapy = therapy_norm_id
        if not normalized_therapy:
            warnings.append(f'therapy-normalizer could not '
                            f'normalize {therapy}.')
        return normalized_therapy

    def get_normalized_disease(self, disease, warnings):
        """Get normalized disease concept.

        :param str disease: Disease query
        :param list warnings: A list of warnings for the search query
        :return: A normalized disease concept string if concept exists in
            disease-normalizer, else `None`
        """
        disease_norm_response = \
            self.disease_query_handler.search_groups(disease)
        normalized_disease = None
        if disease_norm_response['match_type'] != 0:
            normalized_disease = disease_norm_response['value_object_descriptor']['value']['disease_id']  # noqa: E501
            if not normalized_disease.startswith('ncit:'):
                normalized_disease = None

        if not normalized_disease:
            warnings.append(f'disease-normalizer could not normalize '
                            f'{disease}.')
        return normalized_disease

    def get_normalized_variation(self, variation, warnings):
        """Get normalized variation concept.

        :param str variation: Variation query
        :param list warnings: A list of warnings for the search query
        :return: A normalized variant concept string if concept exists in
            variant-normalizer, else `None`
        """
        validations = self.variant_to_vrs.get_validations(variation)
        variation_norm_resp =\
            self.variant_normalizer.normalize(variation, validations,
                                              self.amino_acid_cache)
        normalized_variation = None
        if variation_norm_resp:
            normalized_variation = variation_norm_resp.value_id
        if not normalized_variation:
            # Check if VRS object
            lower_variation = variation.lower()
            if lower_variation.startswith('ga4gh:va.') or lower_variation.startswith('ga4gh:sq.'):  # noqa: E501
                normalized_variation = variation
            else:
                warnings.append(f'variant-normalizer could not normalize '
                                f'{variation}.')
        return normalized_variation

    def get_normalized_gene(self, gene, warnings):
        """Get normalized gene concept.

        :param str gene: Gene query
        :param list warnings: A list of warnings for the search query.
        :return: A normalized gene concept string if concept exists in
            gene-normalizer, else `None`
        """
        gene_norm_resp = self.gene_query_handler.search_sources(gene,
                                                                incl='hgnc')
        normalized_gene = None
        if gene_norm_resp['source_matches']:
            if gene_norm_resp['source_matches'][0]['match_type'] != 0:
                normalized_gene = gene_norm_resp['source_matches'][0]['records'][0].concept_id  # noqa: E501
        if not normalized_gene:
            warnings.append(f'gene-normalizer could not normalize {gene}.')
        return normalized_gene

    def get_normalized_terms(self, variation, disease, therapy, gene,
                             response):
        """Find normalized terms for queried concepts.

        :param str variation: Variation (subject) query
        :param str disease: Disease (object_qualifier) query
        :param str therapy: Therapy (object) query
        :param str gene: Gene query
        :param dict response: The search response
        :return: A tuple containing the normalized concepts if it exists
        """
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
        return normalized_variation, normalized_disease, normalized_therapy, normalized_gene  # noqa: E501

    def search(self, variation='', disease='', therapy='', gene='',
               statement_id=''):
        """Get statements and propositions from queried concepts.

        :param str variation: Variation query
        :param str disease: Disease query
        :param str therapy: Therapy query
        :param str gene: Gene query
        :param str statement_id: Statement ID query
        :return: A dictionary containing the statements and propositions
            with relationships to the queried concepts
        """
        response = {
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
            'statements': [],  # All Statements
            'propositions': []  # All propositions
        }

        if not (variation or disease or therapy or gene or statement_id):
            response['warnings'].append('No parameters were entered.')
            return SearchService(**response).dict()

        (normalized_variation, normalized_disease,
         normalized_therapy, normalized_gene) = \
            self.get_normalized_terms(variation, disease,
                                      therapy, gene, response)

        # Check that the statement_id actually exists
        valid_statement_id = None
        if statement_id:
            response['query']['statement_id'] = statement_id
            with self.driver.session() as session:
                statement = session.read_transaction(
                    self._get_statement_by_id, statement_id
                )
                if statement:
                    valid_statement_id = statement.get('id')
                else:
                    response['warnings'].append(f"Statement: {statement_id} "
                                                f"does not exist.")

        # Need to make sure that each concept that was
        # queried returned a normalized concept
        if (variation and not normalized_variation) or \
                (therapy and not normalized_therapy) or \
                (disease and not normalized_disease) or \
                (gene and not normalized_gene) or \
                (statement_id and not valid_statement_id):
            return SearchService(**response).dict()

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
                    if s not in statement_nodes:
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
        session.close()
        return SearchService(**response).dict()

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
            with self.driver.session() as session:
                statement_id = s.get('id')
                response = session.read_transaction(
                    self._find_and_return_statement_response, statement_id)
                se_list = session.read_transaction(
                    self._find_and_return_supported_by, statement_id)
                statements_response.append(StatementResponse(
                    id=statement_id,
                    description=s.get('description'),
                    direction=s.get('direction'),
                    evidence_level=s.get('evidence_level'),
                    variation_origin=s.get('variation_origin'),
                    proposition=response['tr_id'],
                    variation_descriptor=response['vid'],
                    therapy_descriptor=response['tid'],
                    disease_descriptor=response['did'],
                    method=response['m']['id'],
                    supported_by=[se['id'] for se in se_list]
                ).dict())
        return statements_response

    @staticmethod
    def _find_and_return_statement_response(tx, statement_id):
        """Return IDs and method related to a Statement."""
        query = (
            "MATCH (s) "
            f"WHERE s.id = '{statement_id}' "
            "MATCH (s)-[r1]->(td:TherapyDescriptor) "
            "MATCH (s)-[r2]->(vd:VariationDescriptor) "
            "MATCH (s)-[r3]->(dd:DiseaseDescriptor) "
            "MATCH (s)-[r4]->(m:Method) "
            "MATCH (s)-[r6]->(tr:TherapeuticResponse) "
            "RETURN td.id AS tid, vd.id AS vid, dd.id AS did, m,"
            " tr.id AS tr_id"
        )
        return tx.run(query).single()

    def get_propositions_response(self, propositions):
        """Return a list of propositions from Proposition nodes.

        :param list propositions: A list of Proposition Nodes
        :return: A list of Propositions
        """
        propositions_response = list()
        for p in propositions:
            with self.driver.session() as session:
                p_id = p.get('id')
                value_ids = session.read_transaction(
                    self._find_and_return_proposition_response, p_id
                )
                proposition = TherapeuticResponseProposition(
                    id=p.get('id'),
                    type=p.get('type'),
                    predicate=p.get('predicate'),
                    subject=value_ids['subject'],
                    object_qualifier=value_ids['object_qualifier'],
                    object=value_ids['object']
                ).dict()
                if proposition not in propositions_response:
                    propositions_response.append(proposition)
        return propositions_response

    @staticmethod
    def _find_and_return_proposition_response(tx, proposition_id):
        """Return value ids from a proposition."""
        query = (
            f"MATCH (n) "
            f"WHERE n.id = '{proposition_id}' "
            "MATCH (n) -[r1]-> (t:Therapy) "
            "MATCH (n) -[r2]-> (v:Variation) "
            "MATCH (n) -[r3]-> (d:Disease) "
            "RETURN t.id AS object, v.id AS subject, d.id AS object_qualifier"
        )
        return tx.run(query).single()

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