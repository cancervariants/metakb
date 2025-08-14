"""Acquire connection to Neo4j graph database."""

import ast
import logging
from os import environ
from urllib.parse import urlparse, urlunparse

import boto3
from botocore.exceptions import ClientError
from neo4j import Driver, GraphDatabase, ManagedTransaction

from metakb.config import get_configs
from metakb.schemas.api import ServiceEnvironment

_logger = logging.getLogger(__name__)


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
        _logger.exception("Encountered ClientError while fetching secrets")
        raise
    else:
        return get_secret_value_response["SecretString"]


class Neo4jCredentialsError(Exception):
    """Raise for invalid or unparseable Neo4j credentials"""


def _parse_credentials(url: str) -> tuple[str, tuple[str, str]]:
    """Extract credential parameters from URL

    :param url: Neo4j connection URL
    :return: tuple containing cleaned URL, (username, and password)
    """
    parsed = urlparse(url)
    username = parsed.username
    password = parsed.password
    hostname = parsed.hostname
    port = parsed.port
    if not all([username, password, port, hostname]):
        _logger.error("Unable to parse Neo4j credentials from URL %s", url)
        raise Neo4jCredentialsError

    clean_netloc = f"{hostname}:{port}"
    new_url = urlunparse(parsed._replace(netloc=clean_netloc))
    return (new_url, (username, password))


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
    url: str | None = None,
    initialize: bool = False,
) -> Driver:
    """Get DB connection given provided connection params, or fall back on environment
    params/defaults if not provided.

    Connection URL resolved in the following order:

    * If in a prod environment, ignore all other configs and fetch from AWS Secrets Manager
    * If connection string is provided, use it
    * If connection string is given by env var ``METAKB_DB_URL``, use it
    * Otherwise, fall back on default

    :param url: connection string for Neo4j DB. Formatted as ``bolt://<username>:<password>@<hostname>``
    :param initialize: whether to perform additional DB setup (e.g. add constraints, indexes)
    :return: Neo4j driver instance
    """
    configs = get_configs()
    if configs.env == ServiceEnvironment.PROD:
        # overrule ANY provided configs and get connection url from AWS secrets

        secret = ast.literal_eval(_get_secret())
        url = f"bolt://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
    elif url:
        pass  # use argument if given
    else:
        url = configs.db_url
    cleaned_url, credentials = _parse_credentials(url)
    driver = GraphDatabase.driver(cleaned_url, auth=credentials)
    if initialize:
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
