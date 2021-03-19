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
    * how to do extensions -- JSON?
    * do any current serialized values need to be searchable?
    * refactor add_transformed_data()
    """

    def __init__(self, uri: str, credentials: Tuple[str, str]):
        """Initialize Graph driver instance.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        """
        self.driver = GraphDatabase.driver(uri, auth=credentials)

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    def add_transformed_data(self, data: Dict):
        """Add set of data formatted per Common Data Model to DB.

        :param Dict data: contains Evidence, Proposition, Assertion Methods,
        and Values/Descriptors for Gene, Disease, Therapy, and Variation
        """
        with self.driver.session() as session:
            for proposition in data.get('propositions', []):
                session.write_transaction(self._add_therapeutic_response,
                                          proposition)
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
            for ev in data.get('evidence', []):
                session.write_transaction(self._add_evidence, ev)

    @staticmethod
    def _add_evidence(tx, evidence: Dict):
        """Add evidence object to DB.

        :param Dict evidence: Evidence object
        TODO different methods for assertion/evidence/evidence line?
        TODO better names for relationships -- or get rid of them?
        """
        query = """
        MERGE (ev:Evidence {id:$id, description:$description,
                            direction:$direction,
                            evidence_level:$evidence_level})
        MATCH (prop:Proposition {_id:$proposition})
        MATCH (var:VariationDescriptor {id:$variation_descriptor})
        MATCH (ther:TherapyDescriptor {id:$therapy_descriptor})
        MATCH (dis:DiseaseDescriptor {id:$disease_descriptor})
        MATCH (method:AssertionMethod {id:$assertion_method})
        MATCH (doc:Document {id:$document})
        MERGE (ev) -[:SUPPORTS]-> (prop)
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

    @staticmethod
    def _add_descriptor(tx, descriptor: Dict):
        """Add descriptor object to DB."""
        descr_type = descriptor['type']
        if descr_type == 'TherapyDescriptor':
            descriptor['value_type'] = 'Therapy'
            descriptor['value_id_name'] = 'therapy_id'
            descriptor['value_id'] = descriptor['value']['therapy_id']
        elif descr_type == 'DiseaseDescriptor':
            descriptor['value_type'] = 'Disease'
            descriptor['value_id_name'] = 'disease_id'
            descriptor['value_id'] = descriptor['value']['disease_id']
        elif descr_type == 'GeneDescriptor':
            descriptor['value_type'] = 'Gene'
            descriptor['value_id_name'] = 'gene_id'
            descriptor['value_id'] = descriptor['value']['gene_id']

        query = """
        MERGE (descr:$type {id:$id, label:$label, description:$description,
                            xrefs:$xrefs, alternate_labels:$alternate_labels})
        MERGE (value:$value_type {$value_id_name:$value_id})
        MERGE (descr) -[:DESCRIBES]-> (value);
        """
        try:
            tx.run(query, **descriptor)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Descriptor object\nQuery: {query}\n"
                          f"Descriptor: {descriptor}")
            raise exception

    @staticmethod
    def _add_variant_descriptor(tx, descriptor: Dict):
        """Add variant descriptor object to DB.
        TODO: evaluate using APOC functions
        """
        descriptor['value_type'] = 'Allele'
        descriptor['value_state'] = json.dumps(descriptor['state'])
        descriptor['value_location'] = json.dumps(descriptor['location'])
        descriptor['expressions'] = [json.dumps(e)
                                     for e in descriptor['expressions']]

        query = """
        MERGE (descr:VariationDescriptor
            {id:$id, label:$label, description:$description, xrefs:$xrefs,
             alternate_labels:$alternate_labels,
             molecule_context:$molecule_context,
             structural_type:$structural_type, expressions:$expressions,
             ref_allele_seq:$ref_allele_seq})
        MERGE (value:$value_type {state:$value_state,
                                  location:$value_location})
        MATCH (gene_context:GeneDescriptor {id:$gene_context}})
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
    def _add_assertion_method(tx, assertion_method: Dict):
        """Add Assertion Method object to DB."""
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
    def _add_therapeutic_response(tx, ther_response: Dict):
        """Add Therapeutic Response object to DB.
        TODO: generalize for other types of propositions?
        TODO: how to handle predictive predicate, variation origin
        :param Dict ther_response: TherapeuticResponse object as dict
        """
        query = """
        MERGE (n:TherapeuticResponse {id:$id, type:$type,
                                      predicate:$predicate,
                                      variation_origin:$variation_origin});
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
        """Add Document object to DB."""
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
