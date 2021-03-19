"""Graph database for storing harvested data."""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from typing import Tuple, Dict
import logging
import json

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Graph:
    """Manage requests to graph datastore.

    TODO
    * Docstrings
    * Need to add (currently excluding):
       * Expressions in Variation Descriptors
       * Extensions in any Descriptors (json serialize?)
          * including Variant Groups
       * any Assertion objects
    * format the long constaints string better
    * do any current serialized values need to be searchable?
    * refactor add_transformed_data()
    * do evidence line/assertion need specific methods?
    * handle other types of propositions?
    * can Labels be retrieved as part of the query?
    * handle prime (') symbols in strings -- skipping for now (see whitelist)
    * Verify correct value_ID for variation objects
    """

    def __init__(self, uri: str, credentials: Tuple[str, str]):
        """Initialize Graph driver instance.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        """
        self.driver = GraphDatabase.driver(uri, auth=credentials)
        with self.driver.session() as session:
            session.write_transaction(self._create_constraints)

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    def clear(self):
        """Debugging helper - wipe out DB."""
        def delete_all(tx):
            tx.run("MATCH (n) DETACH DELETE n;")
        with self.driver.session() as session:
            session.write_transaction(delete_all)

    @staticmethod
    def _create_constraints(tx):
        """Create unique property constraints for ID values"""
        try:
            tx.run("CREATE CONSTRAINT gene_id_constraint IF NOT EXISTS ON (n:Gene) ASSERT n.gene_id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT disease_id_constraint IF NOT EXISTS ON (n:Disease) ASSERT n.disease_id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT therapy_id_constraint IF NOT EXISTS ON (n:Therapy) ASSERT n.therapy_id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT vod_id_constraint IF NOT EXISTS ON (n:ValueObjectDescriptor) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT proposition_id_constraint IF NOT EXISTS ON (n:Proposition) ASSERT n._id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT evidence_id_constraint IF NOT EXISTS ON (n:Evidence) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT assertionmethod_id_constraint IF NOT EXISTS ON (n:AssertionMethod) ASSERT n.id IS UNIQUE;")  # noqa: E501
        except ServiceUnavailable as exception:
            logging.error("Failed to generate ID property constraints.")
            raise exception

    def add_transformed_data(self, data: Dict):
        """Add set of data formatted per Common Data Model to DB.
        :param Dict data: contains key/value pairs for data objects to add
            to DB, including Assertions, Therapies, Diseases, Genes,
            Variations, Propositions, and Evidence
        """
        with self.driver.session() as session:
            for method in data.get('assertion_methods', []):
                session.write_transaction(self._add_assertion_method, method)
            for descr in data.get('therapy_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for descr in data.get('disease_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for descr in data.get('gene_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for var_descr in data.get('variation_descriptors', []):
                session.write_transaction(self._add_variant_descriptor,
                                          var_descr)
            for proposition in data.get('propositions', []):
                session.write_transaction(self._add_therapeutic_response,
                                          proposition)
            for ev in data.get('evidence', []):
                session.write_transaction(self._add_evidence, ev)

    @staticmethod
    def _add_assertion_method(tx, assertion_method: Dict):
        """Add Assertion Method object to DB.
        :param Dict assertion_method: must include `id`, `label`, `url`,
            `version`, and `reference` values.
        """
        assertion_method['version'] = json.dumps(assertion_method['version'])
        query = """
        MERGE (n:AssertionMethod {id:$id, label:$label, url:$url,
            version:$version, reference: $reference});
        """
        try:
            tx.run(query, **assertion_method)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add AssertionMethod object\nQuery: "
                          f"{query}\nAssertionMethod: {assertion_method}")
            raise exception

    @staticmethod
    def _add_descriptor(tx, descriptor: Dict):
        """Add gene, therapy, or disease descriptor object to DB.
        :param Dict descriptor: must contain a `value` field with `type`
            and `<type>_id` fields
        """
        descr_type = descriptor['type']
        if descr_type == 'TherapyDescriptor':
            value_type = 'Therapy'
            value_id = descriptor['value']['therapy_id']
        elif descr_type == 'DiseaseDescriptor':
            value_type = 'Disease'
            value_id = descriptor['value']['disease_id']
        elif descr_type == 'GeneDescriptor':
            value_type = 'Gene'
            value_id = descriptor['value']['gene_id']
        nonnull_values = [f'{key}:"{descriptor[key]}"' for key
                          in ('id', 'label', 'description', 'xrefs',
                              'alternate_labels')
                          if descriptor[key]]
        values_joined = ', '.join(nonnull_values)

        try:
            query = f'''
            MERGE (descr:{descr_type} {{ {values_joined} }})
            MERGE (value:{value_type} {{ id: "{value_id}" }})
            MERGE (descr) -[:DESCRIBES]-> (value)
            '''
            tx.run(query)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Descriptor object\nQuery: {query}\n"
                          f"Descriptor: {descriptor}")
            raise exception

    @staticmethod
    def _add_variant_descriptor(tx, descriptor: Dict):
        """Add variant descriptor object to DB.
        :param Dict descriptor: must include a `value_id` field and a `value`
            object containing `type`, `state`, and `location` objects.
        """
        value_type = descriptor['value']['type']
        descriptor['value_state'] = json.dumps(descriptor['value']['state'])
        descriptor['value_location'] = \
            json.dumps(descriptor['value']['location'])
        descriptor['expressions'] = [json.dumps(e)
                                     for e in descriptor['expressions']]
        nonnull_values = [f'{key}:"{descriptor[key]}"' for key
                          in ('id', 'label', 'description', 'xrefs',
                              'alternate_labels', 'structural_type',
                              # 'expressions',
                              'ref_allele_seq')
                          if descriptor[key]]
        values_joined = ', '.join(nonnull_values)

        query = f"""
        MERGE (descr:VariationDescriptor
            {{ {values_joined} }})
        MERGE (value:{value_type}:Variation
            {{id:$value_id,
              state:$value_state,
              location:$value_location}})
        MERGE (gene_context:GeneDescriptor {{id:$gene_context}} )
        MERGE (descr) -[:DESCRIBES]-> (value)
        MERGE (descr) -[:HAS_GENE] -> (gene_context);
        """
        try:
            tx.run(query, **descriptor)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Variant Descriptor object\nQuery: "
                          f"{query}\nDescriptor: {descriptor}")
            raise exception

    @staticmethod
    def _add_therapeutic_response(tx, ther_response: Dict):
        """Add Therapeutic Response object to DB.
        :param Dict ther_response: must include `disease_context`, `therapy`,
            and `has_originating_context` fields.
        """
        nonnull_values = [f'{key}:"{ther_response[key]}"' for key
                          in ('_id', 'predicate', 'variation_origin')
                          if ther_response[key]]
        values_joined = ', '.join(nonnull_values)
        query = f"""
        MERGE (response:TherapeuticResponse:Proposition
            {{ {values_joined} }})
        MERGE (disease:Disease {{id:$disease_context}})
        MERGE (therapy:Therapy {{id:$therapy}})
        MERGE (variation:Variation {{id:$has_originating_context}})
        MERGE (response) -[:HAS_SUBJECT]-> (variation)
        MERGE (variation) -[:IS_SUBJECT_OF]-> (response)
        MERGE (response) -[:HAS_OBJECT]-> (therapy)
        MERGE (therapy) -[:IS_OBJECT_OF]-> (response)
        MERGE (response) -[:HAS_OBJECT_QUALIFIER]-> (disease)
        MERGE (disease) -[:IS_OBJECT_QUALIFIER_OF]-> (response)
        """
        try:
            tx.run(query, **ther_response)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add TherapeuticResponse object\n"
                          f"Query: {query}\nTherapeuticResponse: "
                          f"{ther_response}")
            raise exception

    @staticmethod
    def _add_document(tx, document: Dict):
        """Add Document object to DB.
        :param Dict document: must include `id`, `document_id`, `label`,
            `description`, and `xrefs` fields.
        """
        query = """
        MERGE (n:Document {id:$id, document_id:$document_id, label:$label,
                           description:$description, xrefs:$xrefs});
        """
        try:
            tx.run(query, **document)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Document object\n"
                          f"Query: {query}\nDocument: "
                          f"{document}")
            raise exception

    @staticmethod
    def _add_evidence(tx, evidence: Dict):
        """Add evidence object to DB.
        :param Dict evidence: must include `proposition`,
            `variation_descriptor`, `therapy_descriptor`, `disease_descriptor`,
            `assertion_method`, and `document` fields.
        """
        nonnull_values = [f'{key}:"{evidence[key]}"' for key
                          in ('id', 'description', 'direction',
                              'evidence_level')
                          if evidence[key]]
        values_joined = ', '.join(nonnull_values)

        query = f"""
        MERGE (ev:Evidence:Statement {{ {values_joined} }})
        MERGE (prop:Proposition {{_id:$proposition}})
        MERGE (var:VariationDescriptor {{id:$variation_descriptor}})
        MERGE (ther:TherapyDescriptor {{id:$therapy_descriptor}})
        MERGE (dis:DiseaseDescriptor {{id:$disease_descriptor}})
        MERGE (method:AssertionMethod {{id:$assertion_method}})
        MERGE (doc:Document {{id:$document}})
        MERGE (ev) -[:DEFINED_BY]-> (prop)
        MERGE (ev) -[:HAS_VARIANT]-> (var)
        MERGE (ev) -[:HAS_THERAPY]-> (ther)
        MERGE (ev) -[:HAS_DISEASE]-> (dis)
        MERGE (ev) -[:USES_METHOD]-> (method)
        MERGE (ev) -[:CITES]-> (doc)
        """
        try:
            tx.run(query, **evidence)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Evidence object\n"
                          f"Query: {query}\nEvidence: {evidence}")
            raise exception
