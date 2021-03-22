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
    * Need to add (currently excluding):
       * any Assertion objects
    * do evidence line/assertion need specific methods?
    * handle other types of propositions?
    * handling variant groups correctly?
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
    def json_to_string(obj: Dict):
        """Sanitize tricky characters in values and dump JSON-like object
        into a single string or array compatible with Neo4j property
        constraints.
        :param Dict obj: JSON-like object to convert
        :return: String containing dumped object
        """
        raise NotImplementedError

    @staticmethod
    def string_to_json(obj: str):
        """Convert dumped String back into JSON-like object."""
        raise NotImplementedError

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
            descriptor['value_id'] = descriptor['value']['therapy_id']
        elif descr_type == 'DiseaseDescriptor':
            value_type = 'Disease'
            descriptor['value_id'] = descriptor['value']['disease_id']
        elif descr_type == 'GeneDescriptor':
            value_type = 'Gene'
            descriptor['value_id'] = descriptor['value']['gene_id']

        nonnull_keys = [f"{key}:${key}"
                        for key in ('id', 'label', 'description', 'xrefs',
                                    'alternate_labels')
                        if descriptor[key]]
        descriptor_keys = ', '.join(nonnull_keys)

        query = f'''
        MERGE (descr:{descr_type} {{ {descriptor_keys} }})
        MERGE (value:{value_type} {{ id:$value_id }})
        MERGE (descr) -[:DESCRIBES]-> (value)
        '''
        try:
            tx.run(query, **descriptor)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Descriptor object\nQuery: {query}\n"
                          f"Descriptor: {descriptor}")
            raise exception

    @staticmethod
    def _add_variant_descriptor(tx, descriptor_in: Dict):
        """Add variant descriptor object to DB.
        :param Dict descriptor_in: must include a `value_id` field and a
            `value` object containing `type`, `state`, and `location` objects.
        """
        descriptor = descriptor_in.copy()

        # prepare value properties
        value_type = descriptor['value']['type']
        descriptor['value_state'] = json.dumps(descriptor['value']['state'])
        location = descriptor['value']['location']
        descriptor['value_location_type'] = location['type']
        descriptor['value_location_sequence_id'] = location['sequence_id']
        descriptor['value_location_interval_start'] = \
            location['interval']['start']
        descriptor['value_location_interval_end'] = location['interval']['end']
        descriptor['value_location_interval_type'] = \
            location['interval']['type']

        # prepare descriptor properties
        descriptor['expressions'] = json.dumps(descriptor['expressions'])
        nonnull_keys = [f"{key}:${key}"
                        for key in ('id', 'label', 'description', 'xrefs',
                                    'alternate_labels', 'structural_type',
                                    'expressions', 'ref_allele_seq')
                        if descriptor[key]]

        # handle extensions
        variant_groups = None
        extensions = descriptor.get('extensions')
        if extensions:
            for ext in extensions:
                name = ext['name']
                if name == 'variant_groups':
                    variant_groups = ext['value']
                else:
                    descriptor[name] = json.dumps(ext['value'])
                    nonnull_keys.append(f"{name}:${name}")

        descriptor_keys = ', '.join(nonnull_keys)

        query = f"""
        MERGE (descr:VariationDescriptor
            {{ {descriptor_keys} }})
        MERGE (value:{value_type}:Variation
            {{id:$value_id,
              state:$value_state,
              location_type:$value_location_type,
              location_sequence_id:$value_location_sequence_id,
              location_interval_start:$value_location_interval_start,
              location_interval_end:$value_location_interval_end,
              location_interval_type:$value_location_interval_type
              }})
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
        if variant_groups:
            for grp in variant_groups:
                params = descriptor.copy()
                params['group_id'] = grp['id']
                params['group_label'] = grp['label']
                params['group_description'] = grp['description']

                query = f"""
                MERGE (grp:VariantGroup {{id:$group_id, label:$group_label,
                                         description:$group_description}})
                MERGE (var:VariationDescriptor {{ {descriptor_keys} }})
                MERGE (var) -[:IN_VARIANT_GROUP]-> (grp)
                """
                try:
                    tx.run(query, **params)
                except ServiceUnavailable as exception:
                    logging.error(f"Failed to add Variant Descriptor object\n"
                                  f"Query: {query}\nDescriptor: {descriptor}")
                    raise exception

    @staticmethod
    def _add_therapeutic_response(tx, ther_response: Dict):
        """Add Therapeutic Response object to DB.
        :param Dict ther_response: must include `disease_context`, `therapy`,
            and `has_originating_context` fields.
        """
        ther_response['id'] = ther_response['_id']
        nonnull_keys = [f"{key}:${key}"
                        for key in ('id', 'predicate', 'variation_origin')
                        if ther_response[key]]
        formatted_keys = ', '.join(nonnull_keys)

        query = f"""
        MERGE (response:TherapeuticResponse:Proposition
            {{ {formatted_keys} }})
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
        nonnull_keys = [f"{key}:${key}" for key
                        in ('id', 'description', 'direction',
                            'evidence_level')
                        if evidence[key]]
        formatted_keys = ', '.join(nonnull_keys)

        query = f"""
        MERGE (ev:Evidence:Statement {{ {formatted_keys} }})
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
