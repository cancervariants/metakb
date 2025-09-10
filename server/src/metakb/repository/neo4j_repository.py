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
from neo4j import Driver, GraphDatabase, Record, Transaction
from neo4j.graph import Node

from metakb.config import get_config
from metakb.repository.base import AbstractRepository, is_loadable_statement
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
from metakb.repository.queries import CypherCatalog
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


class _Neo4jConnectionParams(NamedTuple):
    username: str
    password: str
    url: str
    db_name: str | None


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
    if not all([username, password, port, hostname]):
        _logger.error("Unable to parse Neo4j credentials from URL %s", url)
        raise Neo4jCredentialsError

    clean_netloc = f"{hostname}:{port}"
    new_url = urlunparse(parsed._replace(netloc=clean_netloc))
    db_name = parsed.path.lstrip("/") if parsed.path else None
    return _Neo4jConnectionParams(
        username=username, password=password, url=new_url, db_name=db_name
    )


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
    configs = get_config()
    if configs.env == ServiceEnvironment.PROD:
        # overrule ANY provided configs and get connection url from AWS secrets
        secret = ast.literal_eval(_get_secret())
        url = f"bolt://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
    elif url:
        pass  # use argument if given
    else:
        url = configs.db_url
    connection_params = _parse_connection_params(url)
    driver = GraphDatabase.driver(
        connection_params.url,
        auth=(connection_params.username, connection_params.password),
    )
    # TODO add initialization
    # if initialize:
    #     with driver.session() as session:
    #         session.execute_write(_create_constraints)
    return driver


class Neo4jRepository(AbstractRepository):
    """Neo4j implementation of a repository abstraction."""

    def __init__(self, driver: Driver) -> None:
        """Initialize. TODO create driver? session? idk"""
        self.driver = driver
        self.queries = CypherCatalog()
        # TODO not sure if initialize always?
        with self.driver.session().begin_transaction() as tx:
            for query in self.queries.initialize:
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
                    self.queries.load_dac_catvar, cv=catvar_node.model_dump(mode="json")
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
        tx.run(self.queries.load_document, doc=document_node.model_dump(mode="json"))

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
        tx.run(self.queries.load_gene, gene=gene_node.model_dump(mode="json"))

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
                self.queries.load_disease, disease=disease_node.model_dump(mode="json")
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
            tx.run(self.queries.load_drug, drug=drug_node.model_dump(mode="json"))
        elif isinstance(root, TherapyGroup):
            therapy_group_node = TherapyGroupNode.from_gks(root)
            tx.run(
                self.queries.load_therapy_group,
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
            self.queries.load_method,
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
            self.queries.load_statement,
            statement=statement_node.model_dump(mode="json"),
        )

    def add_transformed_data(self, data: TransformedData) -> None:
        """Add a chunk of transformed data to the database.

        :param data: data grouped by GKS entity type
        """
        # since methods are particularly redundant (usually ~1 per source)
        # we might as well just track whether a method has been added and only
        # do so once
        loaded_methods = set()
        # load evidence first so that assertions can be merged into them
        for statement in data.statements_evidence + data.statements_assertions:
            if not is_loadable_statement(statement):
                continue
            with self.driver.session().begin_transaction() as tx:
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
                if statement.specifiedBy.id not in loaded_methods:
                    self.add_document(tx, statement.specifiedBy.reportedIn)
                    self.add_method(tx, statement.specifiedBy)
                    loaded_methods.add(statement.specifiedBy.id)
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

        # TODO holy god this will be interesting
        #
        # I think we need to collect statement IDs associated with nodes
        # and add them to some kind of query tracker thing
        # and then do a `get_statements()` fetch to get all of them separately by ID
        # and then add them back in here
        # evidence_line_nodes = [EvidenceLineNode(has_evidence_items=) for el in ]  # TODO just None for now
        evidence_line_item_ids = [
            item_id
            for line in record["evidence_lines"]
            for item_id in line["evidence_item_ids"]
        ]
        evidence_line_nodes = [
            EvidenceLineNode(
                id=record_line["direction"],
                direction=record_line["direction"],
                has_evidence_items=[
                    self.get_evidence_item(statement_id)
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
        """Perform entity-based search over all statements.

        Return all statements matching all provided entity parameters.

        Probable future changes
        * Search by list of entities
        * Combo-therapy specific search
        * ConditionSet based search

        :param variation_id: GA4GH variation ID
        :param gene_id: normalized gene ID
        :param therapy_id: normalized drug ID
        :param disease_id: normalized condition ID
        :param start: page start
        :param limit: length of page
        :return: list of matching statements
        """
        if limit is None:
            # arbitrary page size default -- this value can't be null
            limit = 999999999
        result = self.driver.execute_query(
            self.queries.search_statements,
            variation_id=variation_id,
            condition_id=disease_id,
            gene_id=gene_id,
            therapy_id=therapy_id,
            start=start,
            limit=limit,
        )
        return self._get_statements_from_results(result.records)

    def teardown_db(self) -> None:
        """Reset repository storage.

        Delete all nodes/edges and constraints.
        """
        # this is a write query and needs to be in its own transaction
        self.driver.execute_query("MATCH (n) DETACH DELETE n")
        with self.driver.session().begin_transaction() as tx:
            for query in self.queries.teardown:
                tx.run(query)
