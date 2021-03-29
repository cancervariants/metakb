"""Graph database for storing harvested data."""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from typing import Tuple, Dict
import logging
import json
from pathlib import Path

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


def _create_keys_string(entity, keys) -> str:
    """Create formatted string for requested keys if non-null in entity.
    :param Dict entity: entity to check against, eg a Disease or Statement
    :param Tuple keys: key names to check
    :return: formatted String for use in Cypher query
    """
    nonnull_keys = [f"{key}:${key}"
                    for key in keys if entity.get(key)]
    keys_string = ', '.join(nonnull_keys)
    return keys_string


class Graph:
    """Manage requests to graph datastore."""

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

    def load_from_json(self, infile_path: Path):
        """Load evidence into DB from given JSON file.
        :param Path infile_path: path to file formatted as array of successive
            collections of evidence, disease/therapy/gene/variation objects,
            statements, etc
        """
        logger.info(f"Loading data from {infile_path}")
        with open(infile_path, 'r') as f:
            items = json.load(f)
            loaded_count = 0
            for item in items:
                self.add_transformed_data(item)
                loaded_count += 1
        logger.info(f"Successfully loaded {loaded_count} statements.")

    @staticmethod
    def _create_constraints(tx):
        """Create unique property constraints for ID values"""
        try:
            tx.run("CREATE CONSTRAINT gene_id_constraint IF NOT EXISTS ON (n:Gene) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT disease_id_constraint IF NOT EXISTS ON (n:Disease) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT therapy_id_constraint IF NOT EXISTS ON (n:Therapy) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT variation_id_constraint IF NOT EXISTS ON (n:Variation) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT gene_desc_id_constraint IF NOT EXISTS ON (n:GeneDescriptor) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT therapy_desc_id_constraint IF NOT EXISTS ON (n:TherapyDescriptor) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT disease_desc_id_constraint IF NOT EXISTS ON (n:DiseaseDescriptor) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT variation_desc_id_constraint IF NOT EXISTS ON (n:VariationDescriptor) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT variation_grp_id_constraint IF NOT EXISTS ON (n:VariationGroup) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT proposition_id_constraint IF NOT EXISTS ON (n:Proposition) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT support_evidence_id_constraint IF NOT EXISTS ON (n:SupportEvidence) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT statement_id_constraint IF NOT EXISTS ON (n:Statement) ASSERT n.id IS UNIQUE;")  # noqa: E501
            tx.run("CREATE CONSTRAINT method_id_constraint IF NOT EXISTS ON (n:Method) ASSERT n.id IS UNIQUE;")  # noqa: E501
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
            for method in data.get('methods', []):
                session.write_transaction(self._add_method, method)
            for descr in data.get('therapy_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for descr in data.get('disease_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for descr in data.get('gene_descriptors', []):
                session.write_transaction(self._add_descriptor, descr)
            for var_descr in data.get('variation_descriptors', []):
                session.write_transaction(self._add_variation_descriptor,
                                          var_descr)
            for ev in data.get('support_evidence'):
                session.write_transaction(self._add_support_evidence, ev)
            for proposition in data.get('propositions', []):
                session.write_transaction(self._add_proposition,
                                          proposition)
            for ev in data.get('statements', []):
                session.write_transaction(self._add_statement, ev)

    @staticmethod
    def _add_method(tx, method: Dict):
        """Add Method object to DB.
        :param Dict method: must include `id`, `label`, `url`,
            `version`, and `reference` values.
        """
        method['version'] = json.dumps(method['version'])
        query = """
        MERGE (n:Method {id:$id, label:$label, url:$url,
            version:$version, reference: $reference});
        """
        try:
            tx.run(query, **method)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Method object\nQuery: "
                          f"{query}\nAssertionMethod: {method}")
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

        descr_keys = _create_keys_string(descriptor, ('id', 'label',
                                                      'description', 'xrefs',
                                                      'alternate_labels'))

        query = f'''
        MERGE (descr:{descr_type} {{ {descr_keys} }})
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
    def _add_variation_descriptor(tx, descriptor_in: Dict):
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
        for expression in descriptor['expressions']:
            syntax = expression['syntax'].split(':')[1]
            key = f"expressions_{syntax}"
            if key in descriptor:
                descriptor[key].append(expression['value'])
            else:
                descriptor[key] = [expression['value']]

        nonnull_keys = [_create_keys_string(descriptor,
                                            ('id', 'label', 'description',
                                             'xrefs', 'alternate_labels',
                                             'structural_type',
                                             'molecule_context',
                                             'expressions_transcript',
                                             'expressions_genomic',
                                             'expressions_protein',
                                             'ref_allele_seq'))]

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
                MERGE (grp:VariationGroup {{id:$group_id, label:$group_label,
                                            description:$group_description}})
                MERGE (var:VariationDescriptor {{ {descriptor_keys} }})
                MERGE (var) -[:IN_VARIATION_GROUP]-> (grp)
                """
                try:
                    tx.run(query, **params)
                except ServiceUnavailable as exception:
                    logging.error(f"Failed to add Variant Descriptor object\n"
                                  f"Query: {query}\nDescriptor: {descriptor}")
                    raise exception

    @staticmethod
    def _add_proposition(tx, proposition: Dict):
        """Add Proposition object to DB.
        :param Dict proposition: must include `disease_context`, `therapy`,
            and `has_originating_context` fields.
        """
        proposition['id'] = proposition['_id']

        formatted_keys = _create_keys_string(proposition, ('id', 'predicate',
                                                           'variation_origin',
                                                           'type'))
        prop_type = proposition.get('type')
        if prop_type == "therapeutic_response_proposition":
            prop_label = ":TherapeuticResponse"
        else:
            prop_label = ""

        query = f"""
        MERGE (response{prop_label}:Proposition
            {{ {formatted_keys} }})
        MERGE (disease:Disease {{id:$object_qualifier}})
        MERGE (therapy:Therapy {{id:$object}})
        MERGE (variation:Variation {{id:$subject}})
        MERGE (response) -[:HAS_SUBJECT]-> (variation)
        MERGE (variation) -[:IS_SUBJECT_OF]-> (response)
        MERGE (response) -[:HAS_OBJECT]-> (therapy)
        MERGE (therapy) -[:IS_OBJECT_OF]-> (response)
        MERGE (response) -[:HAS_OBJECT_QUALIFIER]-> (disease)
        MERGE (disease) -[:IS_OBJECT_QUALIFIER_OF]-> (response)
        """
        try:
            tx.run(query, **proposition)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Proposition object\n"
                          f"Query: {query}\nProposition: {proposition}")
            raise exception

    @staticmethod
    def _add_support_evidence(tx, support_evidence: Dict):
        """Add SupportEvidence object to DB.
        :param Dict support_evidence: must include `id` field.
        """
        formatted_keys = _create_keys_string(support_evidence,
                                             ('id', 'label',
                                              'support_evidence_id', 'xrefs',
                                              'description'))
        query = f"""
        MERGE (n:SupportEvidence {{ {formatted_keys} }});
        """
        try:
            tx.run(query, **support_evidence)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Document object\n"
                          f"Query: {query}\nDocument: "
                          f"{support_evidence}")
            raise exception

    @staticmethod
    def _add_statement(tx, statement: Dict):
        """Add Statement object to DB.
        :param Dict statement: must include `id`, `variation_descriptor`,
            `therapy_descriptor`, `disease_descriptor`, `method`, and
            `support_evidence` fields.
        """
        formatted_keys = _create_keys_string(statement, ('id', 'description',
                                                         'direction',
                                                         'evidence_level'))
        match_line = ""
        rel_line = ""
        support_evidence = statement.get('support_evidence', [])
        if support_evidence:
            for i, ev in enumerate(support_evidence):
                name = f"doc_{i}"
                statement[name] = ev
                match_line += f"MERGE ({name}:SupportEvidence {{ id:${name} }})\n"  # noqa: E501
                rel_line += f"MERGE (ev) -[:CITES]-> ({name})\n"

        query = f"""
        MERGE (ev:Statement {{ {formatted_keys} }})
        MERGE (prop:Proposition {{id:$proposition}})
        MERGE (var:VariationDescriptor {{id:$variation_descriptor}})
        MERGE (ther:TherapyDescriptor {{id:$therapy_descriptor}})
        MERGE (dis:DiseaseDescriptor {{id:$disease_descriptor}})
        MERGE (method:Method {{id:$method}})
        {match_line}
        MERGE (ev) -[:DEFINED_BY]-> (prop)
        MERGE (ev) -[:HAS_VARIATION]-> (var)
        MERGE (ev) -[:HAS_THERAPY]-> (ther)
        MERGE (ev) -[:HAS_DISEASE]-> (dis)
        MERGE (ev) -[:USES_METHOD]-> (method)
        {rel_line}
        """

        try:
            tx.run(query, **statement)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Evidence object\n"
                          f"Query: {query}\nEvidence: {statement}")
            raise exception
