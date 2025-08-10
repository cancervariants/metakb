"""Manage Neo4j database lifecycle."""

import ast
import logging
import os
from urllib.parse import urlparse, urlunparse

import boto3
from botocore.exceptions import ClientError
from neo4j import Driver, GraphDatabase, ManagedTransaction

from metakb.config import config as metakb_config
from metakb.schemas.api import ServiceEnvironment

_logger = logging.getLogger(__name__)


def _get_secret() -> str:
    """Get secrets for MetaKB instances.

    :return: code structured as string for consumption in ``ast.literal_eval``
    """
    secret_name = os.environ["METAKB_DB_SECRET"]
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


def _parse_credentials(url: str) -> tuple[str, str, str]:
    """Extract credential parameters from URL

    :param url: Neo4j connection URL
    :return: tuple containing cleaned URL, username, and password
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
    return (new_url, username, password)


def get_driver(url: str | None = None, initialize: bool = False) -> Driver:
    """Call global DB configuration given provided connection params, or fall back on
    environment params/defaults if not provided.

    At runtime, this method should be called before any queries are executed.

    Connection URL resolved in the following order:

    * If in a prod environment, ignore all other configs and fetch from AWS Secrets Manager
    * If URI provided, use it
    * If URI given by env var, use it
    * Otherwise, fall back on default

    :param url: connection URL, formatted a la ``bolt://<user>:<pass>@<host>:<port #>/<table name>``
    :param initialize: if ``True``, perform graph setup (add constraints/indexes)
    """
    if metakb_config.env == ServiceEnvironment.PROD:
        # overrule ANY provided configs and get connection url from AWS secrets

        secret = ast.literal_eval(_get_secret())
        url = f"bolt://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
    elif url:
        pass  # use argument if given
    else:
        url = metakb_config.db_url  # fall back on configs
    cleaned_url, username, password = _parse_credentials(url)
    driver = GraphDatabase.driver(cleaned_url, auth=(username, password))
    if initialize:
        initialize_graph(driver)
    return driver


_TMP_INITIALIZE_QUERY = ""
_TMP_DROP_CONSTRAINTS_QUERY = ""


def initialize_graph(driver: Driver) -> None:
    """TODO"""
    # TODO add indexes
    driver.execute_query(_TMP_INITIALIZE_QUERY)


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
        tx.run(_TMP_DROP_CONSTRAINTS_QUERY)

    with driver.session() as session:
        session.execute_write(_delete_all)
        if not keep_constraints:
            session.execute_write(_delete_constraints)
