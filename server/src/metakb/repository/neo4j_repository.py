"""Neo4j implementation of the repository abstraction."""

import ast
import logging
import os
from typing import NamedTuple
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
from ga4gh.va_spec.base import (
    Condition,
    Document,
    Method,
    Statement,
    Therapeutic,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from neo4j import (
    Driver,
    GraphDatabase,
    Record,
    Session,
    Transaction,
)
from neo4j.graph import Node

from metakb.config import get_config
from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_models import (
    AlleleNode,
    CategoricalVariantNode,
    ClassificationNode,
    DefiningAlleleConstraintNode,
    DiagnosticStatementNode,
    DiseaseNode,
    DocumentNode,
    DrugNode,
    EvidenceLineNode,
    GeneNode,
    LiteralSequenceExpressionNode,
    MethodNode,
    PrognosticStatementNode,
    ReferenceLengthExpressionNode,
    SequenceLocationNode,
    StrengthNode,
    TherapeuticReponseStatementNode,
    TherapyGroupNode,
)
from metakb.repository.queries import catalog as queries_catalog
from metakb.schemas.api import ServiceEnvironment

_logger = logging.getLogger(__name__)


CYPHER_PAGE_LIMIT = 999999999


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


class _Neo4jConnectionParams(NamedTuple):
    """Contain components of a Neo4j db connection"""

    username: str
    password: str
    url: str


def _parse_connection_params(url: str) -> _Neo4jConnectionParams:
    """Extract credential parameters from URL

    :param url: Neo4j connection URL
    :return: tuple containing cleaned URL, (username, and password)
    """
    parsed = urlparse(url)
    username = parsed.username
    password = parsed.password
    hostname = parsed.hostname
    port = parsed.port
    if not password:
        _logger.error("Unable to parse password")
        raise Neo4jCredentialsError
    if not all([username, password, port, hostname]):
        _logger.error(
            "Unable to parse Neo4j credentials from URL. Got username:%s, password:****, port:%s, hostname:%s",
            username,
            port,
            hostname,
        )
        raise Neo4jCredentialsError

    clean_netloc = f"{hostname}:{port}"
    new_url = urlunparse(parsed._replace(netloc=clean_netloc))
    return _Neo4jConnectionParams(username=username, password=password, url=new_url)


def get_driver(
    url: str | None = None,
) -> Driver:
    """Get DB connection given provided connection params, or fall back on environment
    params/defaults if not provided.

    Connection URL resolved in the following order:

    * If in a prod environment, ignore all other configs and fetch from AWS Secrets Manager
    * If connection string is provided, use it
    * If connection string is given by env var ``METAKB_DB_URL``, use it
    * Otherwise, fall back on default

    :param url: connection string for Neo4j DB. Formatted as ``bolt://<username>:<password>@<hostname>``
    :return: Neo4j driver instance
    """
    configs = get_config()
    if configs.env in (
        ServiceEnvironment.PROD,
        ServiceEnvironment.STAGING,
        ServiceEnvironment.DEV,
    ):
        if url:
            _logger.warning(
                "Overriding DB connection string from `url` param because %s environment is declared",
                configs.env,
            )
        if configs.db_url:
            _logger.warning(
                "Overriding DB connection string from env variable because %s environment is declared",
                configs.env,
            )
        secret = ast.literal_eval(_get_secret())
        url = f"bolt://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
    elif url:
        pass  # use argument if given
    else:
        url = configs.db_url
    connection_params = _parse_connection_params(url)
    return GraphDatabase.driver(
        connection_params.url,
        auth=(connection_params.username, connection_params.password),
    )


class Neo4jRepository(AbstractRepository):
    """Neo4j implementation of a repository abstraction."""

    def __init__(self, session: Session) -> None:
        """Initialize repository instance

        :param session: Neo4j driver session
        """
        self.session = session

    def initialize(
        self,
    ) -> None:
        """Set up DB schema"""
        with self.session.begin_transaction() as tx:
            for query in queries_catalog.initialize():
                tx.run(query)

    def add_catvar(self, tx: Transaction, catvar: CategoricalVariant) -> None:
        """Add categorical variant to DB

        Currently validates that the constraint property exists and has a length of
        exactly 1.

        :param tx: Neo4j transaction
        :param catvar: a full Categorical Variant object
        """
        if catvar.constraints and len(catvar.constraints) == 1:
            constraint = catvar.constraints[0]

            if constraint.root.type == "DefiningAlleleConstraint":
                catvar_node = CategoricalVariantNode.from_gks(catvar)
                tx.run(
                    queries_catalog.load_dac_catvar(),
                    cv=catvar_node.model_dump(mode="json"),
                )
            # in the future, handle other kinds of catvars here
        else:
            msg = f"Valid CatVars should have a single constraint but `constraints` property for {catvar.id} is {catvar.constraints}"
            raise ValueError(msg)

    def add_document(self, tx: Transaction, document: Document) -> None:
        """Add document to DB

        :param tx: Neo4j transaction
        :param document: VA-Spec document
        """
        document_node = DocumentNode.from_gks(document)
        tx.run(
            queries_catalog.load_document(), doc=document_node.model_dump(mode="json")
        )

    def add_gene(
        self,
        tx: Transaction,
        gene: MappableConcept,
    ) -> None:
        """Add gene to DB

        :param tx: Neo4j transcation
        :param gene: VA-Spec gene object
        """
        gene_node = GeneNode.from_gks(gene)
        tx.run(queries_catalog.load_gene(), gene=gene_node.model_dump(mode="json"))

    def add_condition(self, tx: Transaction, condition: Condition) -> None:
        """Add condition to DB.

        For now, only handles individual diseases.

        :param tx: Neo4j transaction
        :param condition: VA-Spec condition
        """
        root = condition.root
        if isinstance(root, MappableConcept) and root.conceptType == "Disease":
            disease_node = DiseaseNode.from_gks(root)
            tx.run(
                queries_catalog.load_disease(),
                disease=disease_node.model_dump(mode="json"),
            )
        else:
            msg = f"Unsupported condition type: {condition}"
            raise NotImplementedError(msg)

    def add_therapeutic(self, tx: Transaction, therapeutic: Therapeutic) -> None:
        """Add a therapeutic -- either an individual Drug or a group.

        :param tx: Neo4j transaction
        :param therapeutic: VA-Spec therapeutic object
        """
        root = therapeutic.root
        if isinstance(root, MappableConcept):
            drug_node = DrugNode.from_gks(root)
            tx.run(queries_catalog.load_drug(), drug=drug_node.model_dump(mode="json"))
        elif isinstance(root, TherapyGroup):
            therapy_group_node = TherapyGroupNode.from_gks(root)
            tx.run(
                queries_catalog.load_therapy_group(),
                therapy_group=therapy_group_node.model_dump(mode="json"),
            )
        else:
            msg = f"Unrecognized therapeutic type: {therapeutic}"
            raise TypeError(msg)

    def add_method(self, tx: Transaction, method: Method) -> None:
        """Add a Method object.

        :param tx: Neo4j transaction
        :param method: VA-Spec method object
        """
        tx.run(
            queries_catalog.load_method(),
            method=MethodNode.from_gks(method).model_dump(mode="json"),
        )

    def add_statement(self, tx: Transaction, statement: Statement) -> None:
        """Add a Statement object.

        Currently supports statements based on
        * VariantTherapeuticResponseProposition
        * VariantPrognosticProposition
        * VariantDiagnosticProposition

        :param tx: Neo4j transaction
        :param statement: VA-Spec Statement
        """
        match statement.proposition:
            case VariantTherapeuticResponseProposition():
                statement_node = TherapeuticReponseStatementNode.from_gks(statement)
            case VariantDiagnosticProposition():
                statement_node = DiagnosticStatementNode.from_gks(statement)
            case VariantPrognosticProposition():
                statement_node = PrognosticStatementNode.from_gks(statement)
            case _:
                msg = f"Unsupported proposition type: {statement.proposition.type}"
                raise NotImplementedError(msg)
        tx.run(
            queries_catalog.load_statement(),
            statement=statement_node.model_dump(mode="json"),
        )

    def load_statement(self, statement: Statement) -> None:
        """Load individual statement, and contained entities, into DB

        :param statement: statement to load
        """
        with self.session.begin_transaction() as tx:
            proposition = statement.proposition
            self.add_catvar(tx, proposition.subjectVariant)
            self.add_gene(tx, proposition.geneContextQualifier)
            # handle proposition-specific properties
            if proposition.type == "VariantTherapeuticResponseProposition":
                self.add_condition(tx, proposition.conditionQualifier)
                self.add_therapeutic(tx, proposition.objectTherapeutic)
            elif proposition.type in {
                "VariantDiagnosticProposition",
                "VariantPrognosticProposition",
            }:
                self.add_condition(tx, proposition.objectCondition)
            else:
                raise NotImplementedError(proposition)
            if statement.reportedIn:
                for document in statement.reportedIn:
                    self.add_document(tx, document)
            self.add_document(tx, statement.specifiedBy.reportedIn)
            self.add_method(tx, statement.specifiedBy)
            self.add_statement(tx, statement)

    @staticmethod
    def _make_allele_node(
        allele_record: Node, sl_record: Node, se_record: Node
    ) -> AlleleNode:
        """Build a VRS Allele node from the raw Neo4j node results


        :param allele_record: Neo4j allele record
        :param sl_record: Neo4j sequence location record
        :param se_record: Neo4j sequence expression record
        :return: Repository Allele node
        :raise ValueError: if unable to coerce SequenceExpression into a repository node model
        """
        if "LiteralSequenceExpression" in se_record.labels:
            state_node = LiteralSequenceExpressionNode(**se_record)
        elif "ReferenceLengthExpression" in se_record.labels:
            state_node = ReferenceLengthExpressionNode(**se_record)
        else:
            msg = f"Unrecognized sequence expression node structure: {se_record}"
            raise ValueError(msg)
        return AlleleNode(
            has_location=SequenceLocationNode(**sl_record),
            has_state=state_node,
            **allele_record,
        )

    @staticmethod
    def _make_therapeutic_node(
        therapy_group_record: Node | None, drug_record: Node | None
    ) -> TherapyGroupNode | DrugNode:
        """Make node fulfilling therapeutic proposition property.

        :param therapy_group_record: Neo4j therapy group column record
        :param drug_record: Neo4j drug column record
        :raise ValueError: if both nodes are None (this means something has gone wrong)
        """
        if therapy_group_record is None and drug_record is None:
            msg = "Both `therapy_group` and `drug` keys in the statement response are NULL. Unable to build therapeutic object."
            raise ValueError(msg)
        if therapy_group_record:
            return TherapyGroupNode(
                has_therapies=[DrugNode(**m) for m in therapy_group_record["members"]],
                **therapy_group_record["therapy_group"],
            )
        return DrugNode(**drug_record)

    def get_statement(
        self, statement_id: str
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
        | None
    ):
        """Retrieve a statement

        :param statement_id: ID of the statement minted by the source
        :return: complete statement if available
        """
        results = self.session.execute_read(
            lambda tx, **kwargs: list(
                tx.run(queries_catalog.search_statements(), **kwargs)
            ),
            variation_ids=[],
            therapy_ids=[],
            condition_ids=[],
            gene_ids=[],
            statement_ids=[statement_id],
            start=0,
            limit=1,
        )
        if not results:
            return None
        processed_results = self._get_statements_from_results(results)
        if len(processed_results) != 1:
            _logger.error(
                "Unexpected quantity of statements in processed results list: %s",
                processed_results,
            )
            raise RuntimeError
        return processed_results[0]

    def _get_statement_node_from_result(
        self, record: Record
    ) -> (
        DiagnosticStatementNode
        | PrognosticStatementNode
        | TherapeuticReponseStatementNode
    ):
        """Given an individual Neo4j result row, produce the repository statement node

        :param record: Neo4j result row
        :return: A statement node with all entities/supporting data filled in
        """
        defining_allele_node = self._make_allele_node(
            record["defining_allele"],
            record["defining_allele_sl"],
            record["defining_allele_se"],
        )
        constraint_node = DefiningAlleleConstraintNode(
            has_defining_allele=defining_allele_node, **record["constraint"]
        )
        member_nodes = [
            self._make_allele_node(m["allele"], m["location"], m["state"])
            for m in record["members"]
        ]
        variant_node = CategoricalVariantNode(
            has_constraint=constraint_node, has_members=member_nodes, **record["cv"]
        )
        gene_node = GeneNode(**record["g"])
        condition_node = DiseaseNode(**record["c"])
        method_node = MethodNode(
            has_document=DocumentNode(**record["method_doc"]), **record["method"]
        )
        document_nodes = [DocumentNode(**d) for d in record["documents"]]
        strength_node = StrengthNode(**record["str"])
        evidence_line_nodes = [
            EvidenceLineNode(
                id=record_line["direction"],
                direction=record_line["direction"],
                has_evidence_items=[
                    self._get_evidence_line_statement_node(statement_id)
                    for statement_id in record_line["evidence_item_ids"]
                ],
            )
            for record_line in record["evidence_lines"]
        ]
        classification_node = (
            ClassificationNode(**record["classification"])
            if record["classification"]
            else None
        )

        match record["s"]["proposition_type"]:
            case "VariantTherapeuticResponseProposition":
                statement = TherapeuticReponseStatementNode(
                    has_method=method_node,
                    has_documents=document_nodes,
                    has_strength=strength_node,
                    has_evidence_lines=evidence_line_nodes,
                    has_classification=classification_node,
                    has_condition=condition_node,
                    has_gene=gene_node,
                    has_variant=variant_node,
                    has_therapeutic=self._make_therapeutic_node(
                        record["therapy_group"], record["drug"]
                    ),
                    **record["s"],
                )
            case "VariantDiagnosticProposition":
                statement = DiagnosticStatementNode(
                    has_method=method_node,
                    has_documents=document_nodes,
                    has_strength=strength_node,
                    has_evidence_lines=evidence_line_nodes,
                    has_classification=classification_node,
                    has_condition=condition_node,
                    has_gene=gene_node,
                    has_variant=variant_node,
                    **record["s"],
                )
            case "VariantPrognosticProposition":
                statement = PrognosticStatementNode(
                    has_method=method_node,
                    has_documents=document_nodes,
                    has_strength=strength_node,
                    has_evidence_lines=evidence_line_nodes,
                    has_classification=classification_node,
                    has_condition=condition_node,
                    has_gene=gene_node,
                    has_variant=variant_node,
                    **record["s"],
                )
            case _:
                msg = f"Unrecognized statement node: {record['s']}"
                raise ValueError(msg)
        return statement

    def _get_evidence_line_statement_node(
        self, statement_id: str
    ) -> (
        TherapeuticReponseStatementNode
        | DiagnosticStatementNode
        | PrognosticStatementNode
        | None
    ):
        """Get the DB node model for a statement ID, to be attached to an Evidence Line.

        This gives us a single level of recursion for statements that are supported by
        evidence lines.

        :param statement_id: ID of statement to fetch
        :return: Node model containing all parts of the statement
        """
        result = self.session.execute_read(
            lambda tx, **kwargs: list(
                tx.run(queries_catalog.search_statements(), **kwargs)
            ),
            variation_ids=[],
            therapy_ids=[],
            condition_ids=[],
            gene_ids=[],
            statement_ids=[statement_id],
            start=0,
            limit=9999,
        )
        if len(result) == 0:
            # TODO warning or error?
            return None
        if len(result) >= 2:
            # should be impossible due to uniqueness constraint, how to log?
            raise RuntimeError
        return self._get_statement_node_from_result(result[0])

    def _get_statements_from_results(self, records: list[Record]) -> list[Statement]:
        """Craft a list of GKS-compliant Statement objects given the results of a Neo4j cypher lookup

        A lot of assumptions are being made that the shape/columns of the records are consistent
        between queries. If there are changes to the graph schema, this method will raise a
        lot of errors at runtime.

        :param records:
        :return: list of full statement objects
        """
        statements = []
        for record in records:
            statement = self._get_statement_node_from_result(record)
            statements.append(statement.to_gks())
        return statements

    def search_statements(
        self,
        variation_ids: list[str] | None = None,
        gene_ids: list[str] | None = None,
        therapy_ids: list[str] | None = None,
        disease_ids: list[str] | None = None,
        statement_ids: list[str] | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        """Perform entity-based search over all statements.

        Return all statements matching any item within a given list of entity IDs.

        IE: Given a list for [DrugA, DrugB] and [GeneA, GeneB], return all statements
        that involve both one of the two given drugs AND one of the two given genes.

        Probable future changes
        * Combo-therapy specific search
        * Specific logic for searching diseases/conditionsets
        * Search on source values rather than normalized values

        :param variation_ids: list of normalized variation IDs
        :param gene_ids: list of normalized gene IDs
        :param therapy_ids: list of normalized therapy IDs
        :param disease_ids: list of normalized disease IDs
        :param statement_ids: list of source statement IDs
        :param start: pagination start point
        :param limit: page size
        :return: list of statements matching provided criteria
        """
        if limit is None:
            limit = CYPHER_PAGE_LIMIT
        # IDs args MUST be lists -- can't be null
        result = self.session.execute_read(
            lambda tx, **kwargs: list(
                tx.run(queries_catalog.search_statements(), **kwargs)
            ),
            statement_ids=statement_ids or [],
            variation_ids=variation_ids or [],
            condition_ids=disease_ids or [],
            gene_ids=gene_ids or [],
            therapy_ids=therapy_ids or [],
            start=start,
            limit=limit,
        )
        return self._get_statements_from_results(result)

    def teardown_db(self) -> None:
        """Reset repository storage.

        Delete all nodes/edges and constraints.
        """
        # this is a write query and needs to be in its own transaction
        self.session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
        with self.session.begin_transaction() as tx:
            for query in queries_catalog.teardown():
                tx.run(query)
