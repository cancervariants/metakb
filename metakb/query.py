"""Module for queries."""
from neo4j import GraphDatabase
import logging
import json


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)

DESCRIPTORS = ['TherapyDescriptor', 'DiseaseDescriptor', 'VariationDescriptor']


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
                   self.find_statements_and_propositions_from_descriptors(query)]:  # noqa: E501
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
                statement_id = s.get('id')
                response = session.read_transaction(
                    self._find_and_return_statement_response, statement_id)
                support_evidence = list()
                se_list = session.read_transaction(
                    self._find_and_return_support_evidence, statement_id)

                for se in se_list:
                    support_evidence.append({
                        'id': se['support_evidence_id'],
                        'label': se['label'],
                        'description': se['description'],
                        'xrefs': se['xrefs'] if se['xrefs'] else []
                    })

                result = {
                    'id': statement_id,
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

    @staticmethod
    def _find_and_return_support_evidence(tx, statement_id):
        """Return a list of SupportEvidence Nodes for a given Statement."""
        query = (
            "MATCH (s:Statement)-[:CITES]->(se:SupportEvidence) "
            f"WHERE s.id = '{statement_id}' "
            "RETURN se"
        )
        return [se[0] for se in tx.run(query)]

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
                self.get_label_and_id(node, ['Therapy', 'Disease', 'Allele',
                                             'Variation'])
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

    def find_statements_and_propositions_from_descriptors(self, query):
        """Find Statement and Proposition Nodes that for descriptors.

        :param str query: The query to search on
        :return: A tuple (List[Proposition Nodes], List[Statement Nodes])
        """
        statements = list()
        propositions = list()
        with self.driver.session() as session:
            descriptors = self.find_descriptors(query)
            for descriptor in descriptors:
                d_label, d_id = descriptor
                statements += session.read_transaction(
                    self._find_and_return_statements_from_descriptor,
                    d_label, d_id
                )
                propositions += session.read_transaction(
                    self._find_and_return_propositions_from_descriptor,
                    d_label, d_id
                )
        return propositions, statements

    @staticmethod
    def _find_and_return_statements_from_descriptor(tx, descriptor_label,
                                                    descriptor_id):
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

    def find_descriptors(self, query):
        """Find Descriptors for a given query.

        :param str query: The query to search on
        :return: A list of tuples containing (Descriptor Label, Descriptor ID)
        """
        # Search on ID --> 1 Descriptor
        descriptor_labels_and_ids = set()
        descriptor = self.find_node_by_id(query)
        if descriptor:
            d_label, d_id = \
                self.get_label_and_id(descriptor, DESCRIPTORS)

            if d_label and d_id:
                descriptor_labels_and_ids.add((d_label, d_id))
                return list(descriptor_labels_and_ids)

        # Search on Label, Alt Label, Xrefs --> N Descriptors
        self.add_descriptors_labels_and_ids(
            descriptor_labels_and_ids,
            [self.find_node_by_label(query),
             self.find_node_from_list('alternate_labels', query),
             self.find_node_from_list('xrefs', query)],
            DESCRIPTORS
        )

        # Specific to Variant Descriptors

        # Search on HGVS expression and Sequence ID --> N Descriptors
        self.add_descriptors_labels_and_ids(
            descriptor_labels_and_ids,
            [self.find_node_from_list('expressions_transcript', query),
             self.find_node_from_list('expressions_protein', query),
             self.find_node_from_list('expressions_genomic', query),
             self.find_variation_descriptors_from_sequence_id(query)],
            ['VariationDescriptor']
        )

        # Search on Gene Symbol + Variant Name
        descriptors = self.find_gene_symbol_and_variant_name(query)
        for label_and_id in descriptors:
            descriptor_labels_and_ids.add((label_and_id[0], label_and_id[1]))
        return list(descriptor_labels_and_ids)

    def add_descriptors_labels_and_ids(self, descriptor_labels_and_ids,
                                       method_list, descriptor_label_matches):
        """Add tuple (label, id) to descriptor list.

        :param set descriptor_labels_and_ids: Contains tuples
            (Descriptor Node Label, Descriptor Node ID)
        :param list method_list: Methods to get the descriptors
        :param list descriptor_label_matches: Valid descriptor node labels
        """
        for descriptors in method_list:
            for descriptor in descriptors:
                d_label, d_id = self.get_label_and_id(descriptor,
                                                      descriptor_label_matches)
                if d_label and d_id:
                    descriptor_labels_and_ids.add((d_label, d_id))

    def find_variation_descriptors_from_sequence_id(self, query):
        """Find variation descriptors from a location sequence id.

        :param str query: The query to search on
        :return: A list of Variation Descriptor Nodes
        """
        with self.driver.session() as session:
            vds = session.read_transaction(
                self._find_variation_descriptors_from_sequence_id,
                query
            )
            return vds

    @staticmethod
    def _find_variation_descriptors_from_sequence_id(tx, sequence_id):
        """Find variation descriptor nodes given sequence id."""
        query = (
            "MATCH (a:Allele)<-[:DESCRIBES]-(vd:VariationDescriptor) "
            f"WHERE a.location_sequence_id = '{sequence_id}' "
            "RETURN DISTINCT vd"
        )
        return [vd[0] for vd in tx.run(query)]

    def find_gene_symbol_and_variant_name(self, query):
        """Find variation descriptors from GeneSymbol+Variant.

        :param str query: The query to search on
        :return: A list of tuples
            (VariationDescriptorLabel, VariationDescriptor ID)
        """
        variation_descriptors = set()
        query = query.split()
        if len(query) != 2:
            return variation_descriptors
        gene_symbol, variant = query

        # Check Gene
        gene_node_labels_and_ids = \
            self.check_gene_or_variant(gene_symbol, ['GeneDescriptor'])
        if not gene_node_labels_and_ids:
            return variation_descriptors

        # Check Variant
        variant_node_labels_and_ids = \
            self.check_gene_or_variant(variant, ['VariationDescriptor'])
        if not variant_node_labels_and_ids:
            return variation_descriptors

        # Check Gene and Variant Relationship Exists
        with self.driver.session() as session:
            for v in variant_node_labels_and_ids:
                for g in gene_node_labels_and_ids:
                    relationship_exists = session.read_transaction(
                        self._check_gene_variant_relationship,
                        g[1], v[1]
                    )
                    if relationship_exists:
                        variation_descriptors.add(v)

        return variation_descriptors

    @staticmethod
    def _check_gene_variant_relationship(tx, gene_id, variant_id):
        """Return whether a variant has a gene."""
        query = (
            "MATCH (g:GeneDescriptor {id: $gene_id}), (v:VariationDescriptor {id: $variant_id} ) "  # noqa:E 501
            "RETURN EXISTS ((v)-[:HAS_GENE]->(g))"
        )
        return tx.run(query, gene_id=gene_id,
                      variant_id=variant_id).single()[0]

    def check_gene_or_variant(self, query, node_label_matches):
        """Check if query is a Gene or Variant and return label and id.

        :param str query: The query to search on
        :param list node_label_matches: Valid node labels that the node can be
        :return: A tuple (node label, node id)
        """
        labels_and_ids = set()
        for nodes in [self.find_node_by_label(query),
                      self.find_node_from_list('alternate_labels', query)]:
            for node in nodes:
                node_label, node_id = \
                    self.get_label_and_id(node, node_label_matches)
                if node_label and node_id:
                    labels_and_ids.add((node_label, node_id))
        return labels_and_ids

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
        """Return a nodes by label."""
        # TODO: MOA stores VID labels as GENE p.VARIANT (TYPE)
        query = (
            "MATCH (n) "
            f"WHERE n.label =~ '(?i){label}' "
            "RETURN DISTINCT n"
        )
        return [n[0] for n in tx.run(query)]

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
            "RETURN DISTINCT n"
        )
        return [n[0] for n in tx.run(query)]

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
