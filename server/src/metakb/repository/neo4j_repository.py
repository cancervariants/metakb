"""Neo4j implementation of the repository abstraction."""

import logging
import os
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
from neo4j import Driver, GraphDatabase, ManagedTransaction
from neo4j.graph import Node

from metakb.config import get_configs
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


def is_loadable_statement(statement: Statement) -> bool:
    """Check whether statement can be loaded to DB

    * All entity terms need to have normalized
    * For variations, that means the catvar must have a constraint
    * For StudyStatements that are supported by other statements via evidence lines,
        all supporting statements must be loadable for the overarching StudyStatement
        to be loadable
    """
    if evidence_lines := statement.hasEvidenceLines:
        for evidence_line in evidence_lines:
            for evidence_item in evidence_line.hasEvidenceItems:
                if not is_loadable_statement(evidence_item):
                    return False
    proposition = statement.proposition
    if not proposition.subjectVariant.constraints:
        return False
    match proposition:
        case VariantTherapeuticResponseProposition():
            if extensions := proposition.conditionQualifier.root.extensions:
                for extension in extensions:
                    if extension.name == "vicc_normalizer_failure" and extension.value:
                        return False
            if therapeutic := proposition.objectTherapeutic:
                match therapeutic.root:
                    case MappableConcept():
                        if extensions := therapeutic.root.extensions:
                            for extension in extensions:
                                if (
                                    extension.name == "vicc_normalizer_failure"
                                    and extension.value
                                ):
                                    return False
                    case TherapyGroup():
                        for drug in therapeutic.root.therapies:
                            if extensions := drug.extensions:
                                for extension in extensions:
                                    if (
                                        extension.name == "vicc_normalizer_failure"
                                        and extension.value
                                    ):
                                        return False
                    case _:
                        raise TypeError
        case VariantDiagnosticProposition() | VariantPrognosticProposition():
            if extensions := proposition.objectCondition.root.extensions:
                for extension in extensions:
                    if extension.name == "vicc_normalizer_failure" and extension.value:
                        return False
        case _:
            msg = f"Unsupported proposition type: {proposition.type}"
            raise NotImplementedError(msg)
    if gene_extensions := proposition.geneContextQualifier.extensions:
        for extension in gene_extensions:
            if extension.name == "vicc_normalizer_failure" and extension.value:
                return False
    return True


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


class Neo4jRepository(AbstractRepository):
    """Neo4j implementation of a repository abstraction."""

    def __init__(self, driver: Driver) -> None:
        """Initialize. TODO create driver? session? idk"""
        self.driver = driver
        self.queries = CypherCatalog()
        # TODO not sure if initialize always?
        with self.driver.session() as session:
            for query in self.queries.initialize:
                session.execute_write(lambda tx: tx.run(query))

    def add_catvar(self, tx: ManagedTransaction, catvar: CategoricalVariant) -> None:
        """Add categorical variant to DB

        Currently validates that the constraint property exists and has a length of
        exactly 1.

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

    def add_document(self, tx: ManagedTransaction, document: Document) -> None:
        """Add document to DB

        :param document:
        """
        document_node = DocumentNode.from_gks(document)
        tx.run(self.queries.load_document, doc=document_node.model_dump(mode="json"))

    def add_gene(
        self,
        tx: ManagedTransaction,
        gene: MappableConcept,  # TODO double check
    ) -> None:
        gene_node = GeneNode.from_gks(gene)
        tx.run(self.queries.load_gene, gene=gene_node.model_dump(mode="json"))

    def add_condition(self, tx: ManagedTransaction, condition: Condition) -> None:
        root = condition.root
        if isinstance(root, MappableConcept) and root.conceptType == "Disease":
            disease_node = DiseaseNode.from_gks(root)
            tx.run(
                self.queries.load_disease, disease=disease_node.model_dump(mode="json")
            )
        else:
            msg = f"Unsupported condition type: {condition}"
            raise NotImplementedError(msg)

    def add_therapeutic(self, tx: ManagedTransaction, therapeutic: Therapeutic) -> None:
        """Add a therapeutic -- either an individual Drug or a group."""
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

    def add_method(self, tx: ManagedTransaction, method: Method) -> None:
        """Add a Method object."""
        tx.run(
            self.queries.load_method,
            method=MethodNode.from_gks(method).model_dump(mode="json"),
        )

    def add_statement(self, tx: ManagedTransaction, statement: Statement) -> None:
        """Add a Statement object.

        Also add supporting documents and evidence lines, when included.
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
        # we should track whether or not they've been added already
        loaded_methods = set()
        # load evidence first so that assertions can be merged into them
        for statement in data.statements_evidence + data.statements_assertions:
            if not is_loadable_statement(statement):
                continue
            with self.driver.session() as session:
                proposition = statement.proposition
                session.execute_write(self.add_catvar, proposition.subjectVariant)
                session.execute_write(self.add_gene, proposition.geneContextQualifier)
                # handle proposition-specific properties
                match proposition:
                    case VariantTherapeuticResponseProposition():
                        session.execute_write(
                            self.add_condition, proposition.conditionQualifier
                        )
                        session.execute_write(
                            self.add_therapeutic,
                            proposition.objectTherapeutic,
                        )
                    case (
                        VariantDiagnosticProposition() | VariantPrognosticProposition()
                    ):
                        session.execute_write(
                            self.add_condition, proposition.objectCondition
                        )
                    case _:
                        raise NotImplementedError(proposition)
                if statement.reportedIn:
                    for document in statement.reportedIn:
                        session.execute_write(self.add_document, document)
                if statement.specifiedBy.id not in loaded_methods:
                    session.execute_write(
                        self.add_document, statement.specifiedBy.reportedIn
                    )
                    session.execute_write(self.add_method, statement.specifiedBy)
                    loaded_methods.add(statement.specifiedBy.id)
                session.execute_write(self.add_statement, statement)

    @staticmethod
    def _make_allele_node(
        allele_record: Node, sl_record: Node, se_record: Node
    ) -> AlleleNode:
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
        """TODO describe this"""
        result = self.driver.execute_query(
            self.queries.search_statements,
            variation_id=variation_id,
            condition_id=disease_id,
            gene_id=gene_id,
            therapy_id=therapy_id,
        )

        statements = []
        for record in result.records:
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
            evidence_line_nodes = []  # TODO just None for now
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
            statements.append(statement.to_gks())
        return statements

    def get_statement(
        self, statement_id: str
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ):
        """Given a single statement ID, get it back.

        TODO: write this as "get statements" -- give list of statement IDs

        :param statement_id: the ID of a statement
        :raise KeyError: if unable to retrieve it
        """
        raise NotImplementedError

    def teardown_db(self) -> None:
        """Reset repository storage."""
        with self.driver.session() as session:
            for query in self.queries.teardown:
                session.execute_write(lambda tx: tx.run(query))
