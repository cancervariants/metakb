"""Module for queries."""
from neo4j import GraphDatabase
import logging
import json


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Query:
    """Class for handling queries."""

    def __init__(self, uri, credentials):
        """Initialize neo4j driver.

        :param str uri: Address of neo4j database
        :param Tuple[str,str] credentials: [username, password]
        """
        self.driver = GraphDatabase.driver(uri, auth=credentials)

    def search(self, query):
        """Return response for query search.

        :param str query: The query to search on
        """
        # TODO:
        #  Search ID (HGNC ID?)
        #  Search Gene Descriptor???
        #  Search sequence_id, start, stop?
        response = {
            'query': query,
            'statements': []
        }

        if query == '':
            return response

        query = query.strip()

        # Try Statement ID, Value IDs (object, subject, object_qualifier),
        # Descriptor fields (ID, label, alternate_labels, xrefs),
        # Variation Descriptor (HGVS Expressions, GeneSymbol + Variant Name)
        for ps in [self.find_statement_and_proposition(query),
                   self.find_propositions_and_statements_from_value(query),
                   self.find_statements_and_propositions_from_descriptor(query),  # noqa: E501
                   self.find_statements_and_propositions_from_variation_descriptor(query)]:  # noqa: E501
            propositions, statements = ps
            if propositions and statements:
                response['statements'] = \
                    self.get_statement_response(statements, propositions)
                return response
        return response

    def get_statement_response(self, statements, propositions):
        """Return a list of statements from Statement and Proposition nodes.

        :param list statements: A list of Statement Nodes
        :param list propositions: A list of Proposition Nodes
        :return: A list of dicts containing statement response output
        """
        statements_response = list()
        propositions = self.get_propositions_response(propositions)
        for s in statements:
            with self.driver.session() as session:
                responses = session.read_transaction(
                    self._find_and_return_statement_response,
                    s.get('id')
                )
                for response in responses:
                    support_evidence = list()
                    se_list = session.read_transaction(
                        self._find_and_return_support_evidence,
                        s.get('id')
                    )
                    for se in se_list:
                        support_evidence.append({
                            'id': se['support_evidence_id'],
                            'label': se['label'],
                            'description': se['description'],
                            'xrefs': se['xrefs'] if se['xrefs'] else []
                        })

                    result = {
                        'id': s.get('id'),
                        'type': s.get('type'),
                        'description': s.get('description'),
                        'direction': s.get('direction'),
                        'evidence_level': s.get('evidence_level'),
                        'proposition': propositions.get(response['tr_id'],
                                                        None),
                        'variation_descriptor': response['vid'],
                        'therapy_descriptor': response['tid'],
                        'disease_descriptor': response['did'],
                        'method': {
                            'label': response['m']['label'],
                            'url': response['m']['url'],
                            'version': json.loads(response['m']['version']),
                            'reference': response['m']['reference']
                        },
                        'support_evidence': support_evidence
                    }
                    statements_response.append(result)
        return statements_response

    @staticmethod
    def _find_and_return_support_evidence(tx, statement_id):
        """Return a list of SupportEvidence Nodes for a given Statement."""
        query = (
            "MATCH (s:Statement)-[:CITES]->(se:SupportEvidence) "
            f"WHERE s.id = '{statement_id}' "
            "RETURN se"
        )
        return [se[0] for se in tx.run(query)]

    @staticmethod
    def _find_and_return_statement_response(tx, statement_id):
        """Return a list of IDs and method related to a Statement."""
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
        return [r for r in tx.run(query)]

    def get_propositions_response(self, propositions):
        """Return a list of propositions from Proposition nodes.

        :param list propositions: A list of Proposition Nodes
        """
        propositions_response = dict()
        for p in propositions:
            with self.driver.session() as session:
                value_ids = session.read_transaction(
                    self._find_and_return_proposition_response,
                    p.get('id')
                )
                propositions_response[p.get('id')] = {
                    'type': p.get('type'),
                    'predicate': p.get('predicate'),
                    'variation_origin': p.get('variation_origin'),
                    'subject': value_ids['subject'],
                    'object_qualifier': value_ids['object_qualifier'],
                    'object': value_ids['object']
                }
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

    def find_statements_and_propositions_from_descriptor(self, query):
        """Get statements and propositions for a given descriptor node.

        :param str query: The query to search on
        :return: A tuple (List[Proposition Nodes], List[Statement Nodes])
        """
        statements = None
        propositions = None
        with self.driver.session() as session:
            descriptor = self.find_descriptor(query)
            if descriptor:
                node_label, node_id = descriptor
                statements = session.read_transaction(
                    self._find_and_return_statements_from_descriptor,
                    node_id, node_label
                )
                propositions = session.read_transaction(
                    self._find_and_return_propositions_from_descriptor,
                    node_label, node_id
                )

        return propositions, statements

    @staticmethod
    def _find_and_return_statements_from_descriptor(tx, descriptor_id,
                                                    descriptor_label):
        """Return a list of statement nodes from a Descriptor node."""
        query = (
            f"MATCH (d:{descriptor_label})<-[r]-(s:Statement) "
            f"WHERE d.id =~ '(?i){descriptor_id}' "
            "RETURN DISTINCT s"
        )
        return [s[0] for s in tx.run(query)]

    @staticmethod
    def _find_and_return_propositions_from_descriptor(tx, descriptor_label,
                                                      descriptor_id):
        """Return TR propositions from Descriptor ID."""
        query = (
            f"MATCH (d:{descriptor_label})-[r1]->(n)-[r2]->(tr:TherapeuticResponse) "  # noqa: #501
            f"WHERE d.id = '{descriptor_id}' "
            "RETURN DISTINCT tr"
        )
        return [tr[0] for tr in tx.run(query)]

    def find_propositions_and_statements_from_value(self, query):
        """Find Propositions and Statements from a value in a VOD.

        :param str query: The query to search on
        :return: A tuple (List[PropositionNodes], List[StatementNodes])
        """
        node = self.find_node_by_id(query)
        propositions = None
        statements = None

        if node:
            node_label, node_id = \
                self.get_label_and_id(node, ['Therapy', 'Disease', 'Allele'])
            if node_label and node_id:
                with self.driver.session() as session:
                    propositions = session.read_transaction(
                        self._find_and_return_propositions_from_value,
                        node_label, node_id
                    )
                    statements = session.read_transaction(
                        self._find_and_return_statements_from_value,
                        node_label, node_id
                    )

        return propositions, statements

    @staticmethod
    def _find_and_return_statements_from_value(tx, value_label, value_id):
        """Return a list of Statement nodes from a value ID."""
        query = (
            f"MATCH (value:{value_label})<-[r1]-(descriptor)<-[r2]-(s:Statement) "  # noqa: E501
            f"WHERE value.id = '{value_id}' "
            "RETURN DISTINCT s"
        )
        return [s[0] for s in tx.run(query)]

    @staticmethod
    def _find_and_return_propositions_from_value(tx, value_label, value_id):
        """Return a list of Proposition nodes from a value ID."""
        query = (
            f"MATCH (value:{value_label})-[r]->(tr:TherapeuticResponse) "
            f"WHERE value.id = '{value_id}' "
            "RETURN DISTINCT tr"
        )
        return [tr[0] for tr in tx.run(query)]

    def find_descriptor(self, query):
        """Find a descriptor node from query.

        :param str query: The query to search on
        :return: A tuple (Node's label, Node's ID)
        """
        # Search on ID, Label, Alt Label, Xrefs
        for node in [self.find_node_by_id(query),
                     self.find_node_by_label(query),
                     self.find_node_from_list('alternate_labels', query),
                     self.find_node_from_list('xrefs', query)]:
            if node:
                node_label, node_id = \
                    self.get_label_and_id(node, ['TherapyDescriptor',
                                                 'DiseaseDescriptor',
                                                 'VariationDescriptor'])
                if node_label and node_id:
                    return node_label, node_id
        return None

    def find_node_by_id(self, node_id):
        """Find a node by its ID.

        :param str node_id: The node ID to search for
        :return: A Node from the neo4j database
        """
        with self.driver.session() as session:
            node = session.read_transaction(self._find_and_return_node_by_id,
                                            node_id)
            return node

    @staticmethod
    def _find_and_return_node_by_id(tx, node_id):
        """Return a node by id."""
        query = (
            "MATCH (n) "
            f"WHERE n.id =~ '(?i){node_id}' "
            "RETURN n"
        )
        return (tx.run(query).single() or [None])[0]

    def find_node_by_label(self, label):
        """Find node by label."""
        with self.driver.session() as session:
            node = \
                session.read_transaction(self._find_and_return_node_by_label,
                                         label)
            return node

    @staticmethod
    def _find_and_return_node_by_label(tx, label):
        """Return a single node by label."""
        # TODO: MOA stores VID labels as GENE p.VARIANT (TYPE)
        query = (
            "MATCH (n) "
            f"WHERE n.label =~ '(?i){label}' "
            "RETURN n"
        )
        return (tx.run(query).single() or [None])[0]

    def find_node_from_list(self, list_name, query):
        """Find a node if a query exists in a Node's list.

        :param str list_name: The name of the Node's list to find the value
        :param str query: The string to find in the Node's list
        :return: A Node from the neo4j database.
        """
        with self.driver.session() as session:
            node = session.read_transaction(
                self._find_and_return_node_from_list, list_name, query
            )
            return node

    @staticmethod
    def _find_and_return_node_from_list(tx, list_name, query):
        """Return node that contains query in its list."""
        query = (
            "MATCH (n) "
            f"WHERE ANY (query IN n.{list_name} WHERE query =~ '(?i){query}') "  # noqa: #501
            "RETURN n"
        )
        return (tx.run(query).single() or [None])[0]

    def find_statements_and_propositions_from_variation_descriptor(self,
                                                                   query):
        """Find statements and propositions for a Variation Descriptor.

        :param str query: The query to search on
        :return: A tuple (List[PropositionNodes], List[StatementNodes])
        """
        statements = None
        propositions = None
        with self.driver.session() as session:
            vd = self.find_variation_descriptor(query)
            if vd:
                node_label, node_id = vd
                statements = session.read_transaction(
                    self._find_and_return_statements_from_descriptor,
                    node_id, node_label
                )
                propositions = session.read_transaction(
                    self._find_and_return_propositions_from_descriptor,
                    node_label, node_id
                )
        return propositions, statements

    def find_variation_descriptor(self, query):
        """Find variation descriptor from HGVS expr or GeneSymbol+Variant.

        :param str query: The query to search on
        :return: A tuple (VariationDescriptorLabel, VariationDescriptor ID)
        """
        # Try search on HGVS string first
        for node in [self.find_node_from_list('expressions_transcript', query),
                     self.find_node_from_list('expressions_protein', query),
                     self.find_node_from_list('expressions_genomic', query)]:
            if node:
                node_label, node_id = \
                    self.get_label_and_id(node, ['VariationDescriptor'])
                if node_label and node_id:
                    return node_label, node_id

        query = query.split()
        if len(query) != 2:
            return None
        gene_symbol, variant = query

        # Check Gene First
        gene_node_label, gene_node_id = \
            self.check_gene_or_variant(gene_symbol, ['GeneDescriptor'])
        if not gene_node_label and not gene_node_id:
            return None

        # Check Variant Now
        variant_node_label, variant_node_id = \
            self.check_gene_or_variant(variant, ['VariationDescriptor'])
        if not variant_node_label and not variant_node_id:
            return None

        with self.driver.session() as session:
            relationship_exists = session.read_transaction(
                self._check_gene_variant_relationship,
                gene_node_id, variant_node_id
            )
            if not relationship_exists:
                return None

        return variant_node_label, variant_node_id

    @staticmethod
    def _check_gene_variant_relationship(tx, gene_id, variant_id):
        """Return whether a variant has a gene."""
        query = (
            "MATCH (g:GeneDescriptor {id: $gene_id}), (v:VariationDescriptor {id: $variant_id} ) "  # noqa:E 501
            "RETURN EXISTS ((v)-[:HAS_GENE]->(g))"
        )
        return tx.run(query, gene_id=gene_id,
                      variant_id=variant_id).single()[0]

    def find_statement_and_proposition(self, query):
        """Find statement by ID with its proposition.

        :param str query: The query to search on
        :return: A tuple ([PropositionNode], [StatementNode])
        """
        node = self.find_node_by_id(query)
        statement = None
        proposition = None
        if node:
            node_label, node_id = self.get_label_and_id(node, ['Statement'])
            if node_label and node_id:
                statement = [node]
                with self.driver.session() as session:
                    proposition = [session.read_transaction(
                        self._find_and_return_statement_proposition,
                        node_id
                    )]
        return proposition, statement

    @staticmethod
    def _find_and_return_statement_proposition(tx, statement_id):
        """Return a statement's proposition."""
        query = (
            "MATCH (s:Statement)-[:DEFINED_BY]->(p:Proposition) "
            f"WHERE s.id = '{statement_id}' "
            "RETURN p"
        )
        return (tx.run(query).single() or [None])[0]

    def get_label_and_id(self, node, node_label_matches):
        """Get node label and ID.

        :param Node node: The node from the neo4j database
        :param list node_label_matches: Valid node labels that the node can be
        :return: A tuple (node label, node id)
        """
        node_label, *_ = node.labels
        node_id = None

        if node_label in node_label_matches:
            node_id = node.get('id')

        return node_label, node_id

    def check_gene_or_variant(self, query, node_label_matches):
        """Check if query is a Gene or Variant and return label and id.

        :param str query: The query to search on
        :param list node_label_matches: Valid node labels that the node can be
        :return: A tuple (node label, node id)
        """
        node_id = None
        node_label = None
        for node in [self.find_node_by_label(query),
                     self.find_node_from_list('alternate_labels', query)]:
            if node:
                node_label, node_id = \
                    self.get_label_and_id(node, node_label_matches)
                if node_label and node_id:
                    break

        return node_label, node_id
