"""Graph database for storing harvested data."""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, ConstraintError
from typing import Tuple, Dict, Set
import logging
import json
from pathlib import Path
from os import environ
import boto3
import base64
from botocore.exceptions import ClientError
import ast

logger = logging.getLogger('metakb.database')
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

    def __init__(self, uri: str = '', credentials: Tuple[str, str] = ('', '')):
        """Initialize Graph driver instance.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        """
        if 'METAKB_NORM_EB_PROD' in environ:
            secret = ast.literal_eval(self.get_secret())
            uri = f"bolt://{secret['host']}:{secret['port']}"
            credentials = (secret['username'], secret['password'])
        elif 'METAKB_DB_URL' in environ and 'METAKB_DB_USERNAME' in environ and 'METAKB_DB_PASSWORD' in environ:  # noqa: E501
            uri = environ['METAKB_DB_URL']
            credentials = (environ['METAKB_DB_USERNAME'],
                           environ['METAKB_DB_PASSWORD'])
        elif not (uri and credentials[0] and credentials[1]):
            # Local
            uri = "bolt://localhost:7687"
            credentials = ("neo4j", "admin")
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

    def load_from_json(self, src_transformed_cdm: Path):
        """Load evidence into DB from given JSON file.
        :param Path src_transformed_cdm: path to file for a source's
            transformed data to common data model containing statements,
            propositions, variation/therapy/disease/gene descriptors,
            methods, and documents
        """
        logger.info(f"Loading data from {src_transformed_cdm}")
        with open(src_transformed_cdm, 'r') as f:
            items = json.load(f)
            self.add_transformed_data(items)

    @staticmethod
    def _create_constraints(tx):
        """Create unique property constraints for ID values"""
        for label in [
            'Gene', 'Disease', 'Therapy', 'Variation', 'GeneDescriptor',
            'TherapyDescriptor', 'DiseaseDescriptor',
            'VariationDescriptor', 'VariationGroup', 'Proposition',
            'Document', 'Statement', 'Method'
        ]:
            query = (
                f"CREATE CONSTRAINT {label.lower()}_id_constraint "
                f"IF NOT EXISTS ON (n:{label}) "
                "ASSERT n.id IS UNIQUE;"
            )
            try:
                tx.run(query)
            except ServiceUnavailable as exception:
                logging.error(f"Failed to generate ID property "
                              f"constraint for {label}.")
                raise exception

    def add_transformed_data(self, data: Dict):
        """Add set of data formatted per Common Data Model to DB.
        :param Dict data: contains key/value pairs for data objects to add
            to DB, including statements, propositions,
            variation/therapy/disease/gene descriptors, methods, and documents
        """
        added_ids = set()  # Used to keep track of IDs that are in statements
        with self.driver.session() as session:
            loaded_count = 0
            for ev in data.get('statements', []):
                self._get_ids_from_statement(ev, added_ids)
            for var_descr in data.get('variation_descriptors', []):
                if var_descr['id'] in added_ids:
                    gc = var_descr['gene_context']
                    if gc:
                        added_ids.add(gc)
            for method in data.get('methods', []):
                try:
                    session.write_transaction(self._add_method, method,
                                              added_ids)
                except ConstraintError:
                    logger.warning(f"{method['id']} exists already.")
                    continue
            for descriptor in ['therapy_descriptors', 'disease_descriptors',
                               'gene_descriptors']:
                for d in data.get(descriptor, []):
                    try:
                        session.write_transaction(
                            self._add_descriptor, d, added_ids
                        )
                    except ConstraintError:
                        logger.warning(f"{d['id']} exists already.")
                        continue
            for var_descr in data.get('variation_descriptors', []):
                try:
                    session.write_transaction(self._add_variation_descriptor,
                                              var_descr, added_ids)
                except ConstraintError:
                    logger.warning(f"{var_descr['id']} exists already.")
                    continue
            for doc in data.get('documents'):
                try:
                    session.write_transaction(self._add_document, doc)
                except ConstraintError:
                    logger.warning(f"{doc['id']} exists already.")
                    continue
            for proposition in data.get('propositions', []):
                try:
                    session.write_transaction(self._add_proposition,
                                              proposition)
                except ConstraintError:
                    logger.warning(f"{proposition['id']} exists already.")
                    continue
            for s in data.get('statements', []):
                loaded_count += 1
                try:
                    session.write_transaction(self._add_statement, s,
                                              added_ids)
                except ConstraintError:
                    logger.warning(f"{s['id']} exists already.")
            logger.info(f"Successfully loaded {loaded_count} statements.")

    @staticmethod
    def _add_method(tx, method: Dict, added_ids: Set[str]):
        """Add Method object to DB.
        :param Dict method: must include `id`, `label`, `url`,
            `version`, and `authors` values.
        :param set added_ids: IDs found in statements
        """
        method['version'] = json.dumps(method['version'])
        query = """
        MERGE (n:Method {id:$id, label:$label, url:$url,
            version:$version, authors: $authors});
        """
        if method['id'] in added_ids:
            try:
                tx.run(query, **method)
            except ServiceUnavailable as exception:
                logging.error(f"Failed to add Method object\nQuery: "
                              f"{query}\nAssertionMethod: {method}")
                raise exception

    @staticmethod
    def _add_descriptor(tx, descriptor: Dict, added_ids: Set[str]):
        """Add gene, therapy, or disease descriptor object to DB.
        :param Dict descriptor: must contain a `value` field with `type`
            and `<type>_id` fields. `type` field must be one of
            {'TherapyDescriptor', 'DiseaseDescriptor', 'GeneDescriptor'}
        :param set added_ids: IDs found in statements
        """
        if descriptor['id'] not in added_ids:
            return
        descr_type = descriptor['type']
        if descr_type == 'TherapyDescriptor':
            value_type = 'Therapy'
        elif descr_type == 'DiseaseDescriptor':
            value_type = 'Disease'
        elif descr_type == 'GeneDescriptor':
            value_type = 'Gene'
        else:
            raise TypeError(f"Invalid Descriptor type: {descr_type}")

        value_id = f"{value_type.lower()}_id"
        descr_keys = _create_keys_string(descriptor, ('id', 'label',
                                                      'description', 'xrefs',
                                                      'alternate_labels'))

        query = f'''
        MERGE (descr:{descr_type} {{ {descr_keys} }})
        MERGE (value:{value_type} {{ id:${value_id} }})
        MERGE (descr) -[:DESCRIBES]-> (value)
        '''
        try:
            tx.run(query, **descriptor)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to add Descriptor object\nQuery: {query}\n"
                          f"Descriptor: {descriptor}")
            raise exception

    @staticmethod
    def _add_variation_descriptor(tx, descriptor_in: Dict,
                                  added_ids: Set[str]):
        """Add variant descriptor object to DB.
        :param Dict descriptor_in: must include a `value_id` field and a
            `value` object containing `type`, `state`, and `location` objects.
        :param set added_ids: IDs found in statements
        """
        descriptor = descriptor_in.copy()

        if descriptor['id'] not in added_ids:
            return

        # prepare value properties
        variation_type = descriptor['variation']['type']
        descriptor['variation'] = json.dumps(descriptor['variation'])
        # prepare descriptor properties
        expressions = descriptor.get('expressions')
        if expressions:
            for expression in expressions:
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
                                             'vrs_ref_allele_seq'))]

        # handle extensions
        variant_groups = None
        extensions = descriptor.get('extensions')
        if extensions:
            for ext in extensions:
                name = ext['name']
                if name == 'variant_group':
                    variant_groups = ext['value']
                else:
                    descriptor[name] = json.dumps(ext['value'])
                    nonnull_keys.append(f"{name}:${name}")

        descriptor_keys = ', '.join(nonnull_keys)

        query = f"""
        MERGE (descr:VariationDescriptor
            {{ {descriptor_keys} }})
        MERGE (value:{variation_type}:Variation
            {{id:$variation_id,
              variation:$variation
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
                params['group_description'] = grp.get('description', '')

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
        formatted_keys = _create_keys_string(proposition, ('id', 'predicate',
                                                           'type'))
        prop_type = proposition.get('type')
        if prop_type == "therapeutic_response_proposition":
            prop_label = ":TherapeuticResponse"
            therapy_obj = "MERGE (therapy:Therapy {id:$object})"
            therapy_rel = """MERGE (response) -[:HAS_OBJECT]-> (therapy)
            MERGE (therapy)-[:IS_OBJECT_OF]->(response)"""
        else:
            therapy_obj, therapy_rel = "", ""
            if prop_type == "prognostic_proposition":
                prop_label = ":Prognostic"
            elif prop_type == "diagnostic_proposition":
                prop_label = ":Diagnostic"
            else:
                prop_label = ""

        query = f"""
        MERGE (response{prop_label}:Proposition
            {{ {formatted_keys} }})
        MERGE (disease:Disease {{id:$object_qualifier}})
        {therapy_obj}
        MERGE (variation:Variation {{id:$subject}})
        MERGE (response) -[:HAS_SUBJECT]-> (variation)
        MERGE (variation) -[:IS_SUBJECT_OF]-> (response)
        {therapy_rel}
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
    def _add_document(tx, document: Dict):
        """Add Document object to DB.
        :param Dict document: must include `id` field.
        """
        try:
            query = "MATCH (n:Document {id:$id}) RETURN n"
            result = tx.run(query, **document)
        except ServiceUnavailable as exception:
            logging.error(f"Failed to read Document object\n"
                          f"Query: {query}\nDocument: "
                          f"{document}")
            raise exception

        if not result.single():
            formatted_keys = _create_keys_string(document,
                                                 ('id', 'label',
                                                  'document_id',
                                                  'xrefs',
                                                  'description'))
            query = f"""
            MERGE (n:Document {{ {formatted_keys} }});
            """
            try:
                tx.run(query, **document)
            except ServiceUnavailable as exception:
                logging.error(f"Failed to add Document object\n"
                              f"Query: {query}\nDocument: "
                              f"{document}")
                raise exception

    def _get_ids_from_statement(self, statement, added_ids):
        """Add descriptors and method IDs to list of added_ids.

        :param Node statement: Statement node
        :param set added_ids: IDs found in statements
        """
        for node_id in [statement.get('therapy_descriptor'),
                        statement.get('variation_descriptor'),
                        statement.get('disease_descriptor'),
                        statement.get('method')]:
            if node_id:
                added_ids.add(node_id)

    @staticmethod
    def _add_statement(tx, statement: Dict, added_ids: Set[str]):
        """Add Statement object to DB.
        :param Dict statement: must include `id`, `variation_descriptor`,
            `disease_descriptor`, `method`, and `supported_by` fields as well
            as optional `therapy_descriptor` field
        :param set added_ids: IDs found in statements
        """
        formatted_keys = _create_keys_string(statement, ('id', 'description',
                                                         'direction',
                                                         'variation_origin',
                                                         'evidence_level'))
        match_line = ""
        rel_line = ""
        supported_by = statement.get('supported_by', [])
        if supported_by:
            for i, ev in enumerate(supported_by):
                name = f"doc_{i}"
                statement[name] = ev
                match_line += f"MERGE ({name} {{ id:${name} }})\n"
                rel_line += f"MERGE (ev) -[:CITES]-> ({name})\n"

        td = statement.get('therapy_descriptor')
        if td:
            therapy_descriptor = \
                f"MERGE (ther:TherapyDescriptor {{id:$therapy_descriptor}})"  # noqa: F541, E501
            therapy_obj = f"MERGE (ev) -[:HAS_THERAPY]-> (ther)"  # noqa: F541
            added_ids.add(td)
        else:
            therapy_descriptor, therapy_obj = "", ""

        query = f"""
        MERGE (ev:Statement {{ {formatted_keys} }})
        MERGE (prop:Proposition {{id:$proposition}})
        MERGE (var:VariationDescriptor {{id:$variation_descriptor}})
        {therapy_descriptor}
        MERGE (dis:DiseaseDescriptor {{id:$disease_descriptor}})
        MERGE (method:Method {{id:$method}})
        {match_line}
        MERGE (ev) -[:DEFINED_BY]-> (prop)
        MERGE (ev) -[:HAS_VARIATION]-> (var)
        {therapy_obj}
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

    @staticmethod
    def get_secret():
        """Get secrets for MetaKB instances."""
        secret_name = environ['METAKB_DB_PASSWORD']
        region_name = "us-east-2"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            logger.warning(e)
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected
                # secret text using the provided KMS key.
                raise e
            elif e.response['Error']['Code'] == \
                    'InternalServiceErrorException':
                # An error occurred on the server side.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for
                # the current state of the resource.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                raise e
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary,
            # one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                return secret
            else:
                decoded_binary_secret = base64.b64decode(
                    get_secret_value_response['SecretBinary'])
                return decoded_binary_secret
