"""Neo4j implementation of the repository abstraction."""

import logging
from typing import NamedTuple
from urllib.parse import urlparse, urlunparse

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    Document,
    EvidenceLine,
    Method,
    Statement,
    Strength,
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
from metakb.repository.base import AbstractRepository, RepositoryStats
from metakb.repository.neo4j_models import (
    AlleleNode,
    CategoricalVariantNode,
    ClassificationNode,
    ConditionSetNode,
    DefiningAlleleConstraintNode,
    DiagnosticStatementNode,
    DiseaseNode,
    DocumentNode,
    DrugNode,
    EvidenceLineNode,
    FeatureContextConstraintNode,
    GeneNode,
    LiteralSequenceExpressionNode,
    MethodNode,
    PhenotypeNode,
    PrognosticStatementNode,
    ReferenceLengthExpressionNode,
    SequenceLocationNode,
    StrengthNode,
    TherapeuticResponseStatementNode,
    TherapyGroupNode,
)
from metakb.repository.queries import catalog as queries_catalog
from metakb.schemas.api import ServiceEnvironment

_logger = logging.getLogger(__name__)


CYPHER_PAGE_LIMIT = 999999999


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
    """Get a Neo4j DB connection using a resolved url.

    Connection URL resolved in the following order:

    * If a connection string is provided via the ``url`` argument, use it
    * Otherwise, fall back on ``METAKB_DB_URL`` environment variable

    This function intentionally avoids any direct dependency on AWS services.
    In deployed environments, ``METAKB_DB_URL`` is expected to be provided by infrastructure
    (e.g. CloudFormation) based on stored secrets.

    :param url: connection string for Neo4j DB. Formatted as ``bolt://<username>:<password>@<hostname>:<port>``
    :return: Neo4j driver instance
    :raises Neo4jCredentialsError: If no valid connection URL can be resolved
    """
    configs = get_config()

    # log overrides in deployed environments
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
        elif configs.db_url:
            _logger.warning(
                "Overriding DB connection string from env variable because %s environment is declared",
                configs.env,
            )
        else:
            _logger.error(
                "No DB connection URL provided in %s environment; "
                "METAKB_DB_URL is expected to be set",
                configs.env,
            )

    # determine connection url
    if url:
        resolved_url = url
    elif configs.db_url:
        resolved_url = configs.db_url
    else:
        err_msg = "Neo4j connection requires METAKB_DB_URL to be set"
        raise Neo4jCredentialsError(err_msg)
    connection_params = _parse_connection_params(resolved_url)
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

    def _add_catvar(self, tx: Transaction, catvar: CategoricalVariant) -> None:
        """Add categorical variant to DB

        Currently validates that the constraint property, if it exists, has a length of
        exactly 1.

        :param tx: Neo4j transaction
        :param catvar: a full Categorical Variant object
        :raise NotImplementedError: if unrecognized type of constraint is provided
        """
        catvar_node = CategoricalVariantNode.from_gks(catvar)
        if catvar.constraints and len(catvar.constraints) == 1:
            constraint = catvar.constraints[0]
            if constraint.root.type == "DefiningAlleleConstraint":
                query = queries_catalog.load_dac_catvar()
            elif constraint.root.type == "FeatureContextConstraint":
                query = queries_catalog.load_fcc_catvar()
            else:
                raise NotImplementedError
        else:
            query = queries_catalog.load_text_catvar()
        tx.run(query, cv=catvar_node.model_dump(mode="json"))

    def _add_document(self, tx: Transaction, document: Document) -> None:
        """Add document to DB

        :param tx: Neo4j transaction
        :param document: VA-Spec document
        """
        document_node = DocumentNode.from_gks(document)
        tx.run(
            queries_catalog.load_document(),
            doc=document_node.model_dump(mode="json"),
        )

    def _add_gene(
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

    def _add_condition(self, tx: Transaction, condition: Condition) -> None:
        """Add condition to DB.

        :param tx: Neo4j transaction
        :param condition: VA-Spec condition (disease, phenotype, or conditionset)
        :raises TypeError: If invalid condition type or conceptType
        """
        cond = getattr(condition, "root", condition)
        if isinstance(cond, ConditionSet):
            node = ConditionSetNode.from_gks(cond)
            tx.run(
                queries_catalog.load_condition_set(),
                condition_set=node.model_dump(mode="json"),
            )

            for child in cond.conditions:
                self._add_condition(tx, child)
            return

        if not isinstance(cond, MappableConcept):
            msg = f"Unrecognized condition type: {cond}"
            raise TypeError(msg)

        if cond.conceptType == "Disease":
            disease_node = DiseaseNode.from_gks(cond)
            tx.run(
                queries_catalog.load_disease(),
                disease=disease_node.model_dump(mode="json"),
            )
        elif cond.conceptType == "Phenotype":
            phenotype_node = PhenotypeNode.from_gks(cond)
            tx.run(
                queries_catalog.load_phenotype(),
                phenotype=phenotype_node.model_dump(mode="json"),
            )
        else:
            msg = f"Unrecognized conceptType: {cond}"
            raise TypeError(msg)

    def _add_therapeutic(self, tx: Transaction, therapeutic: Therapeutic) -> None:
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

    def _add_method(self, tx: Transaction, method: Method) -> None:
        """Add a Method object.

        :param tx: Neo4j transaction
        :param method: VA-Spec method object
        """
        tx.run(
            queries_catalog.load_method(),
            method=MethodNode.from_gks(method).model_dump(mode="json"),
        )

    def _add_strength(self, tx: Transaction, strength: Strength) -> None:
        """Load a strength object

        :param tx: Neo4j transaction
        :param strength: VA-Spec strength object
        """
        tx.run(
            queries_catalog.load_strength(),
            strength=StrengthNode.from_gks(strength).model_dump(mode="json"),
        )

    def _add_evidence_line(self, tx: Transaction, evidence_line: EvidenceLine) -> None:
        """Load an evidence line + everything that it contains

        :param tx: neo4j transaction
        :param evidence_line: GKS evidence line
        """
        if not evidence_line.hasEvidenceItems:
            msg = f"Evidence line has no evidence ({evidence_line=})"
            _logger.error(msg)
            raise ValueError(msg)
        for item in evidence_line.hasEvidenceItems:
            if isinstance(item, EvidenceLine):
                self._add_evidence_line(tx, item)
            elif isinstance(item, Statement):
                self._add_statement(tx, item)
            else:
                raise TypeError
        if evidence_line.strengthOfEvidenceProvided:
            self._add_strength(tx, evidence_line.strengthOfEvidenceProvided)
            strength_id = evidence_line.strengthOfEvidenceProvided.id
        else:
            strength_id = None

        evline_node = EvidenceLineNode.from_gks(evidence_line)
        tx.run(
            queries_catalog.load_evidence_line(),
            evidence_line=evline_node.model_dump(mode="json"),
            strength_id=strength_id,
            item_ids=[i.id for i in evline_node.has_evidence_items],
        )

    def _add_statement(self, tx: Transaction, statement: Statement) -> None:
        """Add an individual statement, as well as any contained evidence, to the DB

        Note that this function gets used BOTH for loading higher-order assertions
        AND loading the statements they contain.

        :param tx: neo4j transaction
        :param statement: va-spec statement
        """
        if statement.hasEvidenceLines:
            for ev_line in statement.hasEvidenceLines:
                self._add_evidence_line(tx, ev_line)

        proposition = statement.proposition
        self._add_catvar(tx, proposition.subjectVariant)
        self._add_gene(tx, proposition.geneContextQualifier)
        # handle proposition-specific properties
        if proposition.type == "VariantTherapeuticResponseProposition":
            self._add_condition(tx, proposition.conditionQualifier)
            self._add_therapeutic(tx, proposition.objectTherapeutic)
        elif proposition.type in {
            "VariantDiagnosticProposition",
            "VariantPrognosticProposition",
        }:
            self._add_condition(tx, proposition.objectCondition)
        else:
            raise NotImplementedError(proposition)
        if statement.reportedIn:
            for document in statement.reportedIn:
                if isinstance(document, Document):
                    self._add_document(tx, document)

        if isinstance(statement.specifiedBy.reportedIn, Document):
            self._add_document(tx, statement.specifiedBy.reportedIn)
        self._add_strength(tx, statement.strength)
        self._add_method(tx, statement.specifiedBy)
        match statement.proposition:
            case VariantTherapeuticResponseProposition():
                statement_node = TherapeuticResponseStatementNode.from_gks(statement)
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

    def _recursive_delete_ev_line(self, tx: Transaction, ev_line: EvidenceLine) -> None:
        """Delete an evidence line and any evidence lines that it contains

        This saves us the effort of manually moving edges around when evidence structure
        changes. Recursivity means it needs to be factored out into its own method.

        :param tx: neo4j transaction
        :param assertion:
        """
        if not ev_line.hasEvidenceItems:
            _logger.error(
                "No evidence items under evidence line (%s)-- something has gone wrong",
                ev_line,
            )
            raise ValueError
        for item in ev_line.hasEvidenceItems:
            if isinstance(item, EvidenceLine):
                self._recursive_delete_ev_line(tx, item)
        tx.run(queries_catalog.delete_evidence_line(), evidence_line_id=ev_line.id)

    def load_assertion(self, assertion: Statement) -> None:
        """Add or update a complete assertion object to the DB

        :param assertion: metakb assertion
        """
        with self.session.begin_transaction() as tx:
            for line in assertion.hasEvidenceLines:
                self._recursive_delete_ev_line(tx, line)
            self._add_statement(tx, assertion)

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

    def _build_condition_set_record(
        self,
        condition_set: Node,
        cond_rels: list[list],
    ) -> dict:
        """Build a condition set record

        :param condition_set: Condition set node
        :param cond_rels: HAS_CONDITION relationships
        :return: Condition set to be passed to ``_make_condition_node``
        """

        def build(node: Node) -> dict:
            """Build a nested condition set"""
            return {
                "condition_set": node,
                "conditions": [
                    build(child) if "ConditionSet" in child.labels else child
                    for child in children_map.get(node["id"], {}).values()
                ],
            }

        # condition set ID -> child condition nodes
        children_map: dict[str, dict[str, Node]] = {}

        for rel_path in cond_rels:
            for rel in rel_path:
                parent_id = rel.start_node["id"]
                child = rel.end_node
                children_map.setdefault(parent_id, {})[child["id"]] = child

        return build(condition_set)

    def _make_condition_node(
        self, condition_set_record: dict | None, condition_record: Node | None
    ) -> ConditionSetNode | DiseaseNode | PhenotypeNode:
        """Build a VA Condition Node from the raw Neo4j node results

        Attempts to build standalone condition first. If null, attempts to build
        condition set record.

        :param condition_set_record: Neo4j condition set record
        :param condition_record: Neo4j condition record
        :return: Repository ConditionSetNode, DiseaseNode, or PhenotypeNode
        :raises ValueError: For unexpected condition records or if neither
            ``condition_set_record`` or ``condition_record`` provided
        """

        def build(
            record: dict | Node,
        ) -> ConditionSetNode | DiseaseNode | PhenotypeNode | None:
            """Recursively build a condition node from neo4j record"""
            if isinstance(record, dict):
                set_node = record["condition_set"]
                children = [
                    child
                    for child in (build(c) for c in record.get("conditions") or [])
                    if child is not None
                ]

                if not children:
                    return None

                if len(children) == 1:
                    return children[0]

                return ConditionSetNode(
                    id=set_node["id"],
                    membership_operator=set_node["membership_operator"],
                    extensions=set_node.get("extensions"),
                    conditions=children,
                )

            if isinstance(record, Node):
                node_labels = record.labels

                if "ConditionSet" in node_labels:
                    # Skip standalone ConditionSet nodes, they must be handled by dict wrapper
                    return None

                if "Disease" in node_labels:
                    return DiseaseNode(**dict(record))

                if "Phenotype" in node_labels:
                    return PhenotypeNode(**dict(record))

            msg = f"Unexpected condition record: {record}"
            raise ValueError(msg)

        if condition_record:
            return build(condition_record)

        if condition_set_record:
            return build(condition_set_record)

        msg = "Must provide either `condition_set_record` or `condition_record`"
        raise ValueError(msg)

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

    def get_statement(self, statement_id: str) -> Statement | None:
        """Retrieve a statement

        :param statement_id: ID of the statement minted by the source
        :return: complete statement if available
        """
        results = self._execute_statement_search(
            [], [], [], [], [statement_id], 0, CYPHER_PAGE_LIMIT
        )
        if statement_id == "metakb.assertion:hJ0lRzYLWxl9o1t1Qk2EFaouRgG5adct":
            import ipdb

            ipdb.set_trace()
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ValueError
        return self._get_statement_node_from_result(results[0]).to_gks()

    @staticmethod
    def _renest_evidence_line_chains(chains: list[dict]) -> list[dict]:
        """Reconstruct nested evidence lines from flattened root-to-leaf chains."""
        roots: dict[str, dict] = {}

        for entry in chains or []:
            chain = entry.get("chain", [])
            if not chain:
                continue

            root_vals = chain[0]
            root = roots.setdefault(
                root_vals["id"], {**root_vals, "has_evidence_items": []}
            )
            current = root

            for line_vals in chain[1:]:
                existing = next(
                    (
                        child
                        for child in current["has_evidence_items"]
                        if isinstance(child, dict)
                        and child.get("id") == line_vals["id"]
                    ),
                    None,
                )
                if existing is None:
                    existing = {**line_vals, "has_evidence_items": []}
                    current["has_evidence_items"].append(existing)
                current = existing

            current["has_evidence_items"] = chain[-1].get("has_evidence_items", [])

        return list(roots.values())

    def _build_evidence_line_node(self, ev_line: dict) -> EvidenceLineNode:
        """Convert nested evidence line dict into an EvidenceLineNode."""
        item_nodes = []

        for item in ev_line.get("has_evidence_items", []):
            if "chain" in item:
                # defensive only; ideally these should already be re-nested
                msg = "Unexpected flattened evidence chain during conversion"
                raise ValueError(msg)
            if isinstance(item, Record) and "s" in item.keys():  # noqa: SIM118
                # fetched Neo4j record-like mapping for a statement
                item_nodes.append(self._get_statement_node_from_result(item))
            elif isinstance(item, dict):
                # nested evidence line dict
                item_nodes.append(self._build_evidence_line_node(item))
            else:
                _logger.error(
                    "Encountered unexpected evidence item: %s of type %s",
                    item,
                    type(item),
                )
                msg = f"Unexpected evidence item type: {type(item)!r}"
                raise ValueError(msg)
        return EvidenceLineNode(
            id=ev_line["id"],
            direction=ev_line["direction"],
            has_evidence_items=item_nodes,
            has_strength=StrengthNode(**ev_line["has_strength"]),
            extensions=ev_line.get("extensions", []),
            evidence_outcome=ev_line["evidence_outcome"],
        )

    def _build_evidence_line_nodes(self, chains: list[dict]) -> list[EvidenceLineNode]:
        """Convert flattened evidence-line chains into nested EvidenceLineNodes."""
        nested_lines = self._renest_evidence_line_chains(chains)
        return [self._build_evidence_line_node(line) for line in nested_lines]

    def _get_statement_node_from_result(
        self, record: Record
    ) -> (
        DiagnosticStatementNode
        | PrognosticStatementNode
        | TherapeuticResponseStatementNode
    ):
        """Given an individual Neo4j result row, produce the repository statement node

        :param record: Neo4j result row
        :return: A statement node with all entities/supporting data filled in
        """
        if record.get("defining_allele"):
            defining_allele_node = self._make_allele_node(
                record["defining_allele"],
                record["defining_allele_sl"],
                record["defining_allele_se"],
            )
            constraint_node = DefiningAlleleConstraintNode(
                has_defining_allele=defining_allele_node, **record["constraint"]
            )
        elif feature_context_vals := record.get("feature_context"):
            feature_context_node = GeneNode(**feature_context_vals)
            constraint_node = FeatureContextConstraintNode(
                has_feature_context=feature_context_node, **record["constraint"]
            )
        else:
            constraint_node = None
        member_nodes = [
            self._make_allele_node(m["allele"], m["location"], m["state"])
            for m in record["members"]
        ]
        variant_node = CategoricalVariantNode(
            has_constraint=constraint_node, has_members=member_nodes, **record["cv"]
        )
        gene_node = GeneNode(**record["g"])

        if condition_set := record.get("condition_set"):
            condition_set_record = self._build_condition_set_record(
                condition_set,
                record["condition_rels"],
            )
        else:
            condition_set_record = None

        condition_node = self._make_condition_node(
            condition_set_record=condition_set_record,
            condition_record=record.get("condition"),
        )

        method_node = MethodNode(
            has_document=DocumentNode(**record["method_doc"]), **record["method"]
        )
        document_nodes = [DocumentNode(**d) for d in record["documents"]]
        strength_node = StrengthNode(**record["str"])
        evidence_line_nodes = self._build_evidence_line_nodes(record["evidence_lines"])
        classification_node = (
            ClassificationNode(**record["classification"])
            if record["classification"]
            else None
        )

        match record["s"]["proposition_type"]:
            case "VariantTherapeuticResponseProposition":
                statement = TherapeuticResponseStatementNode(
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

    def _execute_statement_search(
        self,
        variation_ids: list[str],
        gene_ids: list[str],
        therapy_ids: list[str],
        disease_ids: list[str],
        statement_ids: list[str],
        start: int,
        limit: int,
    ) -> list[Record]:
        """TODO

        factored out to support recursion

        IDs args MUST be lists -- can't be null or the Cypher query will error out

        """
        search_results = self.session.execute_read(
            lambda tx, **kwargs: list(
                tx.run(queries_catalog.search_statements(), **kwargs)
            ),
            statement_ids=statement_ids,
            variation_ids=variation_ids,
            condition_ids=disease_ids,
            gene_ids=gene_ids,
            therapy_ids=therapy_ids,
            start=start,
            limit=limit,
        )
        pending_statement_ids = self._get_pending_statement_ids(search_results)
        if pending_statement_ids:
            fetched = self._execute_statement_search(
                variation_ids=[],
                gene_ids=[],
                therapy_ids=[],
                disease_ids=[],
                statement_ids=pending_statement_ids,
                start=0,
                limit=CYPHER_PAGE_LIMIT,
            )
            self._resolve_pending_statement_refs(search_results, fetched)

        return search_results

    @staticmethod
    def _get_pending_statement_ids(results: list[Record]) -> list[str]:
        """Collect unique unresolved statement IDs from evidence line chains."""
        pending_ids: list[str] = []

        for record in results:
            for ev_chain in record["evidence_lines"]:
                chain = ev_chain.get("chain", [])
                if not chain:
                    continue
                pending_ids.extend(
                    item
                    for item in chain[-1]["has_evidence_items"]
                    if isinstance(item, str)
                )

        return list(dict.fromkeys(pending_ids))

    @staticmethod
    def _fill_evidence_item_refs(
        results: list[Record], fetched_map: dict[str, Record]
    ) -> None:
        """Replace leaf statement ID refs in evidence line chains with fetched records."""
        for record in results:
            for ev_chain in record["evidence_lines"]:
                chain = ev_chain.get("chain", [])
                if not chain:
                    continue

                leaf_items = chain[-1].get("has_evidence_items", [])
                for i, item in enumerate(leaf_items):
                    if isinstance(item, str) and item in fetched_map:
                        leaf_items[i] = fetched_map[item]

    def _resolve_pending_statement_refs(
        self, search_results: list[Record], fetched: list[Record]
    ) -> None:
        """Fill in pending statement refs in evidence lines with newly-fetched Records

        :param search_results: initial search results from user-query, updated in-place
        :param fetched: just-fetched statements to resolve pending statement references
        """
        fetched_map = {r["s"]["id"]: r for r in fetched}
        for record in search_results:
            for ev_chain in record["evidence_lines"]:
                chain = ev_chain.get("chain", [])
                if not chain:
                    continue
                leaf_items = chain[-1].get("has_evidence_items", [])
                for i, item in enumerate(leaf_items):
                    if isinstance(item, str) and item in fetched_map:
                        leaf_items[i] = fetched_map[item]

    def search_statements(
        self,
        variation_ids: list[str] | None = None,
        gene_ids: list[str] | None = None,
        therapy_ids: list[str] | None = None,
        disease_ids: list[str] | None = None,
        statement_ids: list[str] | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> list[Statement]:
        """Perform entity-based search over all statements.

        Return all statements matching any item within a given list of entity IDs.

        IE: Given a list for [DrugA, DrugB] and [GeneA, GeneB], return all statements
        that involve both one of the two given drugs AND one of the two given genes.

        Probable future changes
        * Combo-therapy specific search
        * Specific logic for searching diseases/conditionsets
        * Search on source values rather than normalized values
        * Searching non-allele catvars (e.g. feature context catvars)

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

        search_results = self._execute_statement_search(
            variation_ids or [],
            gene_ids or [],
            therapy_ids or [],
            disease_ids or [],
            statement_ids or [],
            start,
            limit,
        )

        return self._get_statements_from_results(search_results)

    def get_stats(self) -> RepositoryStats:
        """Fetch counts for entities

        :return: structured stats data class
        """
        result = self.session.execute_read(
            lambda tx: list(tx.run(queries_catalog.get_counts()))
        )
        return RepositoryStats(
            **{i["info"]["label"]: i["info"]["count"] for i in result}
        )

    def teardown_db(self) -> None:
        """Reset repository storage.

        Delete all nodes/edges and constraints.
        """
        # this is a write query and needs to be in its own transaction
        self.session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
        with self.session.begin_transaction() as tx:
            for query in queries_catalog.teardown():
                tx.run(query)

    def get_all_assertion_ids(self) -> list[str]:
        """Return all assertion IDs"""
        result = self.session.execute_read(
            lambda tx: list(tx.run(queries_catalog.get_all_assertion_ids()))
        )
        return [r["s.id"] for r in result]
