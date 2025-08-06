"""Provide functions for acquiring and managing a connection to the Neo4j storage backend."""

import ast
import logging
import os

import boto3
from botocore.exceptions import ClientError
from neomodel import config as neomodel_config
from neomodel import db

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


def configure_db(url: str = "") -> None:
    """Call global DB configuration given provided connection params, or fall back on
    environment params/defaults if not provided.

    At runtime, this method should be called before any queries are executed.

    Connection URL resolved in the following order:

    * If in a prod environment, ignore all other configs and fetch from AWS Secrets Manager
    * If URI provided, use it
    * If URI given by env var, use it
    * Otherwise, fall back on default

    :param url: connection URL, formatted a la ``bolt://<user>:<pass>@<host>:<port #>/<table name>``
    """
    if metakb_config.env == ServiceEnvironment.PROD:
        # overrule ANY provided configs and get connection url from AWS secrets

        secret = ast.literal_eval(_get_secret())
        url = f"bolt://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
    elif url:
        pass  # use explicitly-provided params
    elif metakb_config.db_url:
        url = metakb_config.db_url
    else:
        # default -- Neo4j will probably force you to reconfigure this
        url = "bolt://neo4j:neo4j@localhost:7687"

    neomodel_config.DATABASE_URL = url


def clear_graph(clear_schema: bool = False) -> None:
    """Wipe all nodes/relations in DB. Optionally wipe constraints and indices.

    :param driver: Neo4j driver instance
    :param keep_constraints: if ``True``, don't clear constraints
    """
    db.clear_neo4j_database(clear_constraints=clear_schema, clear_indexes=clear_schema)
