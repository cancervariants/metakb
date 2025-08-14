"""Neo4j implementation of the repository abstraction."""

from neo4j import Driver, GraphDatabase

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Document, Method, Statement, TherapyGroup

from metakb.repository.base import AbstractRepository
from metakb.config import .


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


class Neo4jRepository(AbstractRepository):
    """Abstract definition of a repository class.

    Used to access and store core MetaKB data.
    """

    def get_statement(
        self, statement_id: str
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ):
        """Given a single statement ID, get it back.

        :param statement_id: the ID of a statement
        :raise KeyError: if unable to retrieve it
        """
        raise NotImplementedError

    def search_statements(
        self,
        statement_id: str | None = None,
        variation_id: str | None = None,
        gene_id: str | None = None,
        therapy_id: str | None = None,
        disease_id: str | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        raise NotImplementedError

    def _add_dac_catvar(self, catvar: CategoricalVariant) -> None:
        raise NotImplementedError

    def add_catvar(self, catvar: CategoricalVariant) -> None:
        """Add categorical variant to DB

        :param catvar: a full Categorical Variant object
        """
        if catvar.constraints and len(catvar.constraints) == 1:
            constraint = catvar.constraints[0]

            if constraint.type == "DefiningAlleleConstraint":
                self._add_dac_catvar(catvar)
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
