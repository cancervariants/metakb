"""Acquire connection to Neo4j graph database."""

import ast
import logging
from os import environ

import boto3
from botocore.exceptions import ClientError
from neo4j import Driver, GraphDatabase, ManagedTransaction

logger = logging.getLogger(__name__)


def _get_secret() -> str:
    """Get secrets for MetaKB instances.

    :return: code structured as string for consumption in ``ast.literal_eval``
    """
    secret_name = environ["METAKB_DB_SECRET"]
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.exception("Encountered ClientError while fetching secrets")
        raise
    else:
        return get_secret_value_response["SecretString"]


def _get_credentials(
    uri: str, credentials: tuple[str, str]
) -> tuple[str, tuple[str, str]]:
    """Acquire structured credentials.

    * Arguments are required. If they're not empty strings, return them as credentials.
    * If in a production environment, fetch from AWS Secrets Manager.
    * If all env vars declared, use them
    * Otherwise, use defaults

    :param uri: connection URI, formatted a la ``bolt://<host>:<port #>``
    :param credentials: tuple containing username and password
    :return: tuple containing host, and a second tuple containing username/password
    """
    if not (uri and credentials[0] and credentials[1]):
        if "METAKB_EB_PROD" in environ:
            secret = ast.literal_eval(_get_secret())
            uri = f"bolt://{secret['host']}:{secret['port']}"
            credentials = (secret["username"], secret["password"])
        else:
            if all(
                [
                    "METAKB_DB_URL" in environ,
                    "METAKB_DB_USERNAME" in environ,
                    "METAKB_DB_PASSWORD" in environ,
                ]
            ):
                uri = environ["METAKB_DB_URL"]
                credentials = (
                    environ["METAKB_DB_USERNAME"],
                    environ["METAKB_DB_PASSWORD"],
                )
            else:  # local default settings
                uri = "bolt://localhost:7687"
                credentials = ("neo4j", "password")
    return uri, credentials


_CONSTRAINTS = {
    "strength_constraint": "CREATE CONSTRAINT coding_constraint IF NOT EXISTS FOR (n:Strength) REQUIRE n.primaryCoding IS UNIQUE;",
    "gene_id_constraint": "CREATE CONSTRAINT gene_id_constraint IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE;",
    "disease_id_constraint": "CREATE CONSTRAINT disease_id_constraint IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;",
    "therapy_id_constraint": "CREATE CONSTRAINT therapy_id_constraint IF NOT EXISTS FOR (n:Therapy) REQUIRE n.id IS UNIQUE;",
    "variation_id_constraint": "CREATE CONSTRAINT variation_id_constraint IF NOT EXISTS FOR (n:Variation) REQUIRE n.id IS UNIQUE;",
    "categoricalvariant_id_constraint": "CREATE CONSTRAINT categoricalvariant_id_constraint IF NOT EXISTS FOR (n:CategoricalVariant) REQUIRE n.id IS UNIQUE;",
    "variantgroup_id_constraint": "CREATE CONSTRAINT variantgroup_id_constraint IF NOT EXISTS FOR (n:VariantGroup) REQUIRE n.id IS UNIQUE;",
    "location_id_constraint": "CREATE CONSTRAINT location_id_constraint IF NOT EXISTS FOR (n:Location) REQUIRE n.id IS UNIQUE;",
    "document_id_constraint": "CREATE CONSTRAINT document_id_constraint IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;",
    "statement_id_constraint": "CREATE CONSTRAINT statement_id_constraint IF NOT EXISTS FOR (n:Statement) REQUIRE n.id IS UNIQUE;",
    "method_id_constraint": "CREATE CONSTRAINT method_id_constraint IF NOT EXISTS FOR (n:Method) REQUIRE n.id IS UNIQUE;",
    "classification_constraint": "CREATE CONSTRAINT classification_constraint IF NOT EXISTS FOR (n:Classification) REQUIRE n.primaryCoding IS UNIQUE;",
    "evidence_line_id_constraint": "CREATE CONSTRAINT evidence_line_id_constraint IF NOT EXISTS FOR (n:EvidenceLine) REQUIRE n.id IS UNIQUE;",
}


def _create_constraints(tx: ManagedTransaction) -> None:
    """Create unique property constraints for nodes

    :param tx: Transaction object provided to transaction functions
    """
    for query in _CONSTRAINTS.values():
        tx.run(query)


def get_driver(
    uri: str = "",
    credentials: tuple[str, str] = ("", ""),
    add_constraints: bool = False,
) -> Driver:
    """Initialize Graph driver instance.

    Connection URI/credentials are resolved as follows:

    1. Use function args if given
    2. Use values from AWS secrets manager if env var ``METAKB_EB_PROD`` is set
    3. Use values from env vars ``METAKB_DB_URL``, ``METAKB_DB_USERNAME``, and
        ``METAKB_DB_PASSWORD``, if all are defined
    4. Use local defaults: ``"bolt://localhost:7687"``, with username ``"neo4j"``
        and password ``"password"``

    :param uri: address of Neo4j DB
    :param credentials: tuple containing username and password
    :return: Neo4j driver instance
    """
    uri, credentials = _get_credentials(uri, credentials)
    driver = GraphDatabase.driver(uri, auth=credentials)
    if add_constraints:
        with driver.session() as session:
            session.execute_write(_create_constraints)
    return driver


def clear_graph(driver: Driver, keep_constraints: bool = False) -> None:
    """Wipe all nodes/relations (not constraints) in DB.

    :param driver: Neo4j driver instance
    :param keep_constraints: if ``True``, don't clear constraints
    """

    def _delete_all(tx: ManagedTransaction) -> None:
        """Delete all nodes and relationships

        :param tx: Transaction object provided to transaction functions
        """
        tx.run("MATCH (n) DETACH DELETE n;")

    def _delete_constraints(tx: ManagedTransaction) -> None:
        """Delete all constraints

        :param tx: Transaction object provided to transaction functions
        """
        for constraint_name in _CONSTRAINTS:
            query = f"DROP CONSTRAINT {constraint_name} IF EXISTS;"
            tx.run(query)

    with driver.session() as session:
        session.execute_write(_delete_all)
        if not keep_constraints:
            session.execute_write(_delete_constraints)
