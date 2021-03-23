"""Module for queries."""
from neo4j import GraphDatabase
import logging


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
        #  Search by ID
        #  Search by HGVS
        response = {
            'query': query,
            'propositions': [],
            'statements': []
        }

        if query == '':
            return response

        query = query.lower()
        return response

    def find_statements_from_descriptor(self, query):
        """Find Statement nodes from a descriptor query."""
        with self.driver.session() as session:
            node_label, node_id = self.find_descriptor(query)
            statement_nodes = session.read_transaction(
                self._find_and_return_statements_from_descriptor,
                node_id, node_label
            )
            return statement_nodes

    @staticmethod
    def _find_and_return_statements_from_descriptor(tx, descriptor_id,
                                                    descriptor_label):
        """Return statement matches from a given Descriptor ID."""
        query = (
            f"MATCH (d:{descriptor_label})<-[r]-(s:Statement) "
            f"WHERE d.id =~ '(?i){descriptor_id}' "
            "RETURN s"
        )
        return {s[0] for s in tx.run(query)}

    def find_propositions_from_descriptor(self, query):
        """Find TR propositions from a descriptor query."""
        with self.driver.session() as session:
            node_label, node_id = self.find_descriptor(query)
            tr_nodes = session.read_transaction(
                self._find_and_return_propositions_from_descriptor,
                node_label, node_id
            )
            return tr_nodes

    @staticmethod
    def _find_and_return_propositions_from_descriptor(tx, descriptor_label,
                                                      descriptor_id):
        """Return TR propositions from Descriptor ID."""
        query = (
            f"MATCH (d:{descriptor_label})-[r1]->(n)-[r2]->(tr:TherapeuticResponse) "  # noqa: #501
            f"WHERE d.id = '{descriptor_id}' "
            "RETURN tr"
        )
        return {tr[0] for tr in tx.run(query)}

    def find_propositions_and_statements_from_value(self, query):
        """Find Propositions and Statements from a value in a VOD."""
        node = self.find_node_by_id(query)
        propositions = None
        statements = None

        if node:
            node_label, *_ = node.labels
            # Possible values in a VOD
            if node_label in ['Therapy', 'Disease', 'Variation']:
                node_id = node.get('id')
                with self.driver.session() as session:
                    propositions = session.read_transaction(
                        self._find_and_return_propositions_from_value,
                        node_label, node_id
                    )
                    statements = session.read_transaction(
                        self._find_and_return_statements_from_value,
                        node_label, node_id
                    )

        if not propositions and not statements:
            return None

        return propositions, statements

    @staticmethod
    def _find_and_return_statements_from_value(tx, value_label, value_id):
        """Return Statement nodes from a value ID."""
        query = (
            f"MATCH (value:{value_label})<-[r1]-(descriptor)<-[r2]-(s:Statement) "  # noqa: E501
            f"WHERE value.id = '{value_id}' "
            "RETURN s"
        )
        return {s[0] for s in tx.run(query)}

    @staticmethod
    def _find_and_return_propositions_from_value(tx, value_label, value_id):
        """Return Proposition nodes from a value ID."""
        query = (
            f"MATCH (value:{value_label})-[r]->(tr:TherapeuticResponse) "
            f"WHERE value.id = '{value_id}' "
            "RETURN tr"
        )
        return {tr[0] for tr in tx.run(query)}

    def find_descriptor(self, query):
        """Find a descriptor node from query."""
        # Search on ID, Label, Alt Label, Xrefs
        for node in [self.find_node_by_id(query),
                     self.find_node_by_label(query),
                     self.find_node_from_list('alternate_labels', query),
                     self.find_node_from_list('xrefs', query)]:
            if node:
                node_label, *_ = node.labels
                if 'Descriptor' in node_label:
                    return node_label, node.get('id')
        return None

    def find_node_by_id(self, node_id):
        """Return a node by ID if ID exists."""
        with self.driver.session() as session:
            node = session.read_transaction(self._find_and_return_node_by_id,
                                            node_id)
            return node

    @staticmethod
    def _find_and_return_node_by_id(tx, node_id):
        """Return node by id."""
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
        """If query is in a node's list, return that node."""
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
