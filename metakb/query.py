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
        response = {
            'query': query,
            'matches': []
        }

        if query == '':
            return response

        query = query.lower()

    def find_evidence_from_propositions(self, propositions):
        """Find evidence items that support propositions.

        :param list propositions: TR records
        """
        propositions_ids = [tr[0].get('_id') for tr in propositions]
        evidence_items = list()
        with self.driver.session() as session:
            for proposition_id in propositions_ids:
                evidence_items.append(session.read_transaction(
                    self._find_and_return_evidence_from_proposition_id,
                    proposition_id))
            return evidence_items

    @staticmethod
    def _find_and_return_evidence_from_proposition_id(tx, proposition_id):
        query = (
            "MATCH (e:Evidence)-[:SUPPORTS]->(tr:TherapeuticResponse) "
            f"WHERE tr._id =~ '(?i){proposition_id}' "
            "RETURN e"
        )
        return ([e for e in tx.run(query)] or [None])[0]

    def find_propositions_from_id(self, query):
        """Try to find proposition from query.

        :param str query: The ID to search
        :return: A list of propositions
        """
        node = self.find_node_by_id(query)
        if not node:
            return []
        else:
            node = node[0]
        label, *_ = node.labels
        node_id = node.get('id')

        relationship = \
            self.find_relationship('TherapeuticResponse', label).get('type')

        tr_nodes = self.get_node_from_relationship(
            'TherapeuticResponse', label, node_id, relationship)
        return tr_nodes

    def find_evidence_by_label(self, query):
        """Descriptor label"""
        nodes = self.find_node_by_label(query)
        if not nodes:
            return []

        evidence_items = list()

        for node in nodes:
            node = node[0]
            label, *_ = node.labels
            node_id = node.get('id')
            r = self.find_relationship('Evidence', label).get('type')
            e = self.find_evidence_from_descriptor(node_id, label, r)
            evidence_items += e

        return evidence_items

    def find_evidence_from_descriptor(self, descriptor_id, descriptor_label,
                                      relationship):
        """Find evidence items for a given descriptor"""
        with self.driver.session() as session:
            evidence_items = session.read_transaction(
                self._find_and_return_evidence_from_descriptor,
                descriptor_id, descriptor_label, relationship)
            return evidence_items

    @staticmethod
    def _find_and_return_evidence_from_descriptor(tx, descriptor_id,
                                                  descriptor_label,
                                                  relationship):
        """Return evidence matches from descriptor."""
        query = (
            f"MATCH (d:{descriptor_label})<-[:{relationship}]-(e:Evidence) "
            f"WHERE d.id =~ '(?i){descriptor_id}' "
            "RETURN e"
        )
        return [e[0] for e in tx.run(query)]

    def find_node_by_label(self, label):
        """Find descriptor node by label."""
        with self.driver.session() as session:
            node = \
                session.read_transaction(self._find_and_return_node_by_label,
                                         label)
            return node

    @staticmethod
    def _find_and_return_node_by_label(tx, label):
        """Find Descriptors by label."""
        # TODO: MOA stores VID labels as GENE p.VARIANT (TYPE)
        query = (
            "MATCH (n) "
            f"WHERE n.label =~ '(?i){label}' "
            "RETURN n"
        )
        return [n for n in tx.run(query)]

    def find_node_by_id(self, node_id):
        """Find a node by ID."""
        with self.driver.session() as session:
            node = session.read_transaction(self._find_and_return_node_by_id,
                                            node_id)
            return node

    @staticmethod
    def _find_and_return_node_by_id(tx, node_id):
        query = (
            "MATCH (n) "
            f"WHERE n.id =~ '(?i){node_id}' "
            "RETURN n"
        )
        return ([n for n in tx.run(query)] or [None])[0]

    def find_relationship(self, node1_label, node2_label):
        """Find relationship from node1 to node2."""
        with self.driver.session() as session:
            relationship = \
                session.read_transaction(self._find_and_return_relationship,
                                         node1_label, node2_label)
            return relationship

    @staticmethod
    def _find_and_return_relationship(tx, node1_label, node2_label):
        """Return relationship for two nodes."""
        query = (
            f"MATCH (n1:{node1_label})-[r]->(n2:{node2_label}) "
            "RETURN type(r) as type"
        )
        return ({r for r in tx.run(query)} or {None}).pop()

    def get_node_from_relationship(self, node1_label, node2_label, value_id,
                                   relationship):
        """Return relationship for two nodes."""
        with self.driver.session() as session:
            node = session.read_transaction(
                self._find_and_return_node_from_relationship,
                node1_label, node2_label, value_id, relationship)
            return node

    @staticmethod
    def _find_and_return_node_from_relationship(tx, node1_label, node2_label,
                                                value_id, relationship):
        query = (
            f"MATCH (n1:{node1_label})-[:{relationship}]->(n2:{node2_label}) "
            f"WHERE n2.id =~ '(?i){value_id}' "
            "RETURN n1"
        )
        return [n for n in tx.run(query)]
