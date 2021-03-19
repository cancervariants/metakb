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

    def find_node(self, node_label, node_id):
        """Find a node by label and id.

        :param str node_label: The label of the node
        :param str node_id: The id of the node label to find
        :return: The Record of the node if it exists, else `None`.
        """
        with self.driver.session() as session:
            node = session.read_transaction(
                self._find_and_return_node, node_label, node_id
            )
            return node

    @staticmethod
    def _find_and_return_node(tx, node_label, node_id):
        query = (
            f"MATCH (n:{node_label}) "
            "WHERE n.id = $node_id "
            "RETURN n"
        )
        return ([n for n in tx.run(query, node_label=node_label,
                                   node_id=node_id)] or [None])[0]


q = Query(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
# r = q.graph.driver.session().run("MATCH (p:Proposition) RETURN p")
# print([n for n in r])
# print(q.find_proposition("proposition:125"))
print(q.find_node('Evidence', 'civic:eid2997'))
