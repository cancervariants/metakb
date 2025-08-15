"""Neo4j implementation of the repository abstraction."""

import logging
import os
from importlib.resources import files
from urllib.parse import urlparse, urlunparse

import boto3
from botocore.exceptions import ClientError
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Document, Method, Statement, TherapyGroup
from neo4j import Driver, GraphDatabase, ManagedTransaction

from metakb.config import get_configs
from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_models import CategoricalVariantNode
from metakb.schemas.api import ServiceEnvironment
from metakb.transformers.base import TransformedData

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
    # TODO add initialization
    # if initialize:
    #     with driver.session() as session:
    #         session.execute_write(_create_constraints)
    return driver


class _QueryContainer:
    def __init__(self):
        query_dir = files("metakb.repository") / "queries"
        self.initialize = (query_dir / "initialize.cypher").read_text(encoding="utf-8")
        self.teardown = (query_dir / "teardown.cypher").read_text(encoding="utf-8")
        self.load_dac_catvar = (
            query_dir / "load_definingalleleconstraint_catvar.cypher"
        ).read_text(encoding="utf-8")


class Neo4jRepository(AbstractRepository):
    """Neo4j implementation of a repository abstraction."""

    def __init__(self, driver: Driver) -> None:
        """Initialize. TODO create driver? session? idk"""
        self.driver = driver
        self.queries = _QueryContainer()

    def _add_dac_catvar(
        self, tx: ManagedTransaction, catvar: CategoricalVariant
    ) -> None:
        catvar_node = CategoricalVariantNode.from_vrs(catvar)
        tx.run(self.queries.load_dac_catvar, cv=catvar_node.model_dump(mode="json"))

    def add_catvar(self, tx: ManagedTransaction, catvar: CategoricalVariant) -> None:
        """Add categorical variant to DB

        Currently validates that the constraint property exists and has a length of
        exactly 1.

        :param catvar: a full Categorical Variant object
        """
        if catvar.constraints and len(catvar.constraints) == 1:
            constraint = catvar.constraints[0]

            if constraint.root.type == "DefiningAlleleConstraint":
                self._add_dac_catvar(tx, catvar)
            # in the future, handle other kinds of catvars here
        else:
            msg = f"Valid CatVars should have a single constraint but `constraints` property for {catvar.id} is {catvar.constraints}"
            raise ValueError(msg)

    def add_document(self, document: Document) -> None:
        raise NotImplementedError

    def add_method(self, method: Method) -> None:
        raise NotImplementedError

    def add_gene(
        self,
        gene: MappableConcept,  # TODO double check
    ) -> None:
        raise NotImplementedError

    def add_condition(self, condition: MappableConcept) -> None:
        raise NotImplementedError

    def add_therapy(
        self, therapy: MappableConcept | TherapyGroup
    ) -> None:  # TODO double check
        raise NotImplementedError

    # add statement evidence assertions
    def add_evidence(self, evidence) -> None:
        raise NotImplementedError

    def add_assertion(self, assertion) -> None:
        raise NotImplementedError

    def add_transformed_data(self, data: TransformedData) -> None:
        """Add a chunk of transformed data to the database.

        :param data: data grouped by GKS entity type
        """
        # TODO prune unused stuff
        # TODO some kind of session/transaction logic
        with self.driver.session() as session:
            for catvar in data.categorical_variants:
                session.execute_write(self.add_catvar, catvar)
            # for document in data.documents:
            #     session.execute_write(self.add_document, document)
            # for method in data.methods:
            #     session.execute_write(self.add_method, method)
            # for gene in data.genes:
            #     session.execute_write(self.add_gene, gene)
            # for condition in data.conditions:
            #     session.execute_write(self.add_condition, condition)
            # for therapy in data.therapies:
            #     session.execute_write(self.add_therapy, therapy)
            # for evidence in data.statements_evidence:
            #     session.execute_write(self.add_evidence, evidence)
            # for assertion in data.statements_assertions:
            #     session.execute_write(self.add_assertion, assertion)
