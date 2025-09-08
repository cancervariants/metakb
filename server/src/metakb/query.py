"""Provide class/methods/schemas for issuing queries against the database."""

import json
import logging
from copy import copy
from enum import Enum

from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core.models import Extension, MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Direction,
    Document,
    EvidenceLine,
    MembershipOperator,
    Method,
    Statement,
    TherapyGroup,
)
from ga4gh.vrs.models import (
    Allele,
    Expression,
    LiteralSequenceExpression,
    ReferenceLengthExpression,
    SequenceLocation,
)
from neo4j import Driver
from neo4j.graph import Node

from metakb.database import get_driver
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.schemas.api import (
    EntityType,
    NormalizedTerm,
    SearchResult,
    StatementIdTerm,
)

_logger = logging.getLogger(__name__)


class EmptySearchError(Exception):
    """Raise for invalid search parameters (e.g. no parameters given)"""


class PaginationParamError(Exception):
    """Raise for invalid pagination parameters."""


class VariationRelation(str, Enum):
    """Constrain possible values for the relationship between variations and
    categorical variants.
    """

    HAS_MEMBERS = "HAS_MEMBERS"
    HAS_DEFINING_CONTEXT = "HAS_DEFINING_CONTEXT"


class TherapeuticRelation(str, Enum):
    """Constrain possible values for therapeutic relationships."""

    HAS_COMPONENTS = "HAS_COMPONENTS"
    HAS_SUBSTITUTES = "HAS_SUBSTITUTES"


# Proposition types to corresponding class mapping
PROP_TYPE_TO_CLASS = {
    "VariantDiagnosticProposition": VariantDiagnosticStudyStatement,
    "VariantPrognosticProposition": VariantPrognosticStudyStatement,
    "VariantTherapeuticResponseProposition": VariantTherapeuticResponseStudyStatement,
}


def _deserialize_field(node: dict, field_name: str) -> None | dict:
    """Deserialize JSON blob property.

    :param node: Neo4j graph node data
    :param field_name: Name of field to check/deserialize
    :return: property dictionary if available, ``None`` if empty
    """
    field = node.get(field_name)
    if field:
        return json.loads(field)
    return None


class QueryHandler:
    """Primary query-handling class. Wraps database connections and hooks to external
    services such as the concept normalizers.
    """

    def __init__(
        self,
        driver: Driver | None = None,
        normalizers: ViccNormalizers | None = None,
        default_page_limit: int | None = None,
    ) -> None:
        """Initialize neo4j driver and the VICC normalizers.

        All arguments are optional; if not given, resources acquisition will be
        attempted with default parameters.

        >>> from metakb.query import QueryHandler
        >>> qh = QueryHandler()

        Otherwise, pass resources directly to avoid duplication:

        >>> from metakb.database import get_driver
        >>> from metakb.normalizers import ViccNormalizers
        >>> qh = QueryHandler(
        ...     get_driver("bolt://localhost:7687", ("neo4j", "password")),
        ...     ViccNormalizers("http://localhost:8000"),
        ... )

        ``default_page_limit`` sets the default max number of statements to include in
        query responses:

        >>> limited_qh = QueryHandler(default_page_limit=10)
        >>> response = await limited_qh.batch_search_statements(["BRAF V600E"])
        >>> print(len(response.statement_ids))
        10

        This value is overruled by an explicit ``limit`` parameter:

        >>> response = await limited_qh.batch_search_statements(["BRAF V600E"], limit=2)
        >>> print(len(response.statement_ids))
        2

        :param driver: driver instance for graph connection
        :param normalizers: normalizer collection instance
        :param default_page_limit: default number of results per response page (leave
            as ``None`` for no default limit)
        """
        if driver is None:
            driver = get_driver()
        if normalizers is None:
            normalizers = ViccNormalizers()
        self.driver = driver
        self.vicc_normalizers = normalizers
        self._default_page_limit = default_page_limit

    async def search_statements(
        self,
        variation: str | None = None,
        disease: str | None = None,
        therapy: str | None = None,
        gene: str | None = None,
        statement_id: str | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> SearchResult:
        """Get nested statements from queried concepts that match all conditions provided.
        For example, if ``variation`` and ``therapy`` are provided, will return all
        statements that have both the provided ``variation`` and ``therapy``.

        >>> from metakb.query import QueryHandler
        >>> qh = QueryHandler()
        >>> result = qh.search_statements("BRAF V600E")
        >>> result.statement_ids[:3]
        ['moa.assertion:944', 'moa.assertion:911', 'moa.assertion:865']
        >>> result.statements[0].reportedIn[0].urls[0]
        'https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/202429s019lbl.pdf'

        Variation, disease, therapy, and gene terms are resolved via their respective
        :ref:`concept normalization services<normalization>`.

        :param variation: Variation query. Free text variation description, e.g.
            ``"BRAF V600E"``, or GA4GH variation ID, e.g.
            ``"ga4gh:VA.4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO"``. Case-insensitive.
        :param disease: Disease query. Full disease name, e.g. ``"glioblastoma"``,
            common shorthand name, e.g. ``"GBM"``, concept URI, e.g. ``"ncit:C3058"``.
            Case-insensitive.
        :param therapy: Therapy query. Full name, e.g. ``"imatinib"``, trade name, e.g.
            ``"GLEEVEC"``, or concept URI, e.g. ``"chembl:CHEMBL941"``. Case-insensitive.
        :param gene: Gene query. Common shorthand name, e.g. ``"NTRK1"``, or compact URI,
            e.g. ``"ensembl:ENSG00000198400"``.
        :param statement_id: Statement ID query provided by source, e.g. ``"civic.eid:3017"``.
        :param start: Index of first result to fetch. Must be nonnegative.
        :param limit: Max number of results to fetch. Must be nonnegative. Revert to
            default defined at class initialization if not given.
        :return: Results including terms with normalization, and all statements
        :raise EmptySearchError: if no search params given
        :raise PaginationParamError: if either pagination param given is negative
        """
        if not any((variation, disease, therapy, gene, statement_id)):
            raise EmptySearchError
        if start < 0:
            msg = f"Invalid start value: {start}. Must be nonnegative."
            raise PaginationParamError(msg)
        if isinstance(limit, int) and limit < 0:
            msg = f"Invalid limit value: {limit}. Must be nonnegative."
            raise PaginationParamError(msg)

        # attempt normalization of entity terms
        search_terms = []
        (
            normalized_therapy,
            normalized_disease,
            normalized_variation,
            normalized_gene,
        ) = None, None, None, None
        if therapy:
            normalized_therapy = self._get_normalized_therapy(therapy)
            search_terms.append(normalized_therapy)
        if disease:
            normalized_disease = self._get_normalized_disease(disease)
            search_terms.append(normalized_disease)
        if variation:
            normalized_variation = await self._get_normalized_variation(variation)
            search_terms.append(normalized_variation)
        if gene:
            normalized_gene = self._get_normalized_gene(gene)
            search_terms.append(normalized_gene)

        # Check that queried statement_id is valid
        statement, statement_term = None, None
        if statement_id:
            statement = self._get_stmt_by_id(statement_id)
            statement_term = StatementIdTerm(
                term=statement_id,
                validated_statement_id=statement.get("id") if statement else None,
            )
            search_terms.append(statement_term)

        # return early if ANY search terms fail to resolve
        if any(
            (
                normalized_therapy and normalized_therapy.normalized_id is None,
                normalized_disease and normalized_disease.normalized_id is None,
                normalized_variation and normalized_variation.normalized_id is None,
                normalized_gene and normalized_gene.normalized_id is None,
            )
        ) or (statement_term and statement_term.validated_statement_id is None):
            _logger.debug(
                "One or more search terms failed to normalize/validate: %s",
                search_terms,
            )
            return SearchResult(search_terms=search_terms, start=start, limit=limit)

        # get statement data
        if statement:
            statement_nodes = [statement]
        else:
            statement_nodes = self._get_statements(
                normalized_variation=normalized_variation.normalized_id
                if normalized_variation
                else None,
                normalized_therapy=normalized_therapy.normalized_id
                if normalized_therapy
                else None,
                normalized_disease=normalized_disease.normalized_id
                if normalized_disease
                else None,
                normalized_gene=normalized_gene.normalized_id
                if normalized_gene
                else None,
                start=start,
                limit=limit,
            )
        statements = self._get_nested_stmts(statement_nodes)
        return SearchResult(
            search_terms=search_terms, start=start, limit=limit, statements=statements
        )

    def _get_normalized_disease(self, disease: str) -> NormalizedTerm:
        """Get normalized disease concept.

        :param disease: Disease query
        :return: A normalized disease concept if it exists
        """
        _, disease_id = self.vicc_normalizers.normalize_disease(disease)
        return NormalizedTerm(
            term=disease, term_type=EntityType.DISEASE, normalized_id=disease_id
        )

    def _get_normalized_gene(self, gene: str) -> NormalizedTerm:
        """Get normalized gene concept.

        :param gene: Gene query
        :return: A normalized gene concept if it exists
        """
        _, gene_id = self.vicc_normalizers.normalize_gene(gene)
        return NormalizedTerm(
            term=gene, term_type=EntityType.GENE, normalized_id=gene_id
        )

    def _get_normalized_therapy(self, therapy: str) -> NormalizedTerm:
        """Get normalized therapy concept.

        :param therapy: Therapy query
        :return: A normalized therapy concept if it exists
        """
        _, therapy_id = self.vicc_normalizers.normalize_therapy(therapy)
        return NormalizedTerm(
            term=therapy, term_type=EntityType.THERAPY, normalized_id=therapy_id
        )

    async def _get_normalized_terms(
        self,
        variation: str | None,
        disease: str | None,
        therapy: str | None,
        gene: str | None,
    ) -> list[NormalizedTerm]:
        """Find normalized terms for queried concepts.

        :param variation: Variation (subject) query
        :param disease: Disease (object_qualifier) query
        :param therapy: Therapy (object) query
        :param gene: Gene query
        :return: a list of normalization results
        """
        term_results = []
        if therapy:
            _, normalized_therapy_id = self.vicc_normalizers.normalize_therapy(therapy)
            term_results.append(
                NormalizedTerm(
                    term=therapy,
                    term_type=EntityType.THERAPY,
                    normalized_id=normalized_therapy_id,
                )
            )
        if disease:
            _, normalized_disease_id = self.vicc_normalizers.normalize_disease(disease)
            term_results.append(
                NormalizedTerm(
                    term=disease,
                    term_type=EntityType.DISEASE,
                    normalized_id=normalized_disease_id,
                )
            )
        if variation:
            normalized_variation_id = await self._get_normalized_variation(variation)
            term_results.append(
                NormalizedTerm(
                    term=variation,
                    term_type=EntityType.VARIATION,
                    normalized_id=normalized_variation_id,
                )
            )
        if gene:
            _, normalized_gene_id = self.vicc_normalizers.normalize_gene(gene)
            term_results.append(
                NormalizedTerm(
                    term=gene,
                    term_type=EntityType.GENE,
                    normalized_id=normalized_gene_id,
                )
            )

        # If queried concept is given check that it is normalized / valid
        return term_results

    async def _get_normalized_variation(self, variation: str) -> NormalizedTerm:
        """Get normalized variation concept.

        :param variation: Variation query
        :return: A normalized variant concept if it exists
        """
        variant_norm_resp = await self.vicc_normalizers.normalize_variation(variation)
        normalized_variation = variant_norm_resp.id if variant_norm_resp else None

        # Check if VRS variation (allele, copy number change, copy number count)
        # TODO should this happen before the normalizer call?
        if not normalized_variation and variation.startswith(
            ("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")
        ):
            normalized_variation = variation
        return NormalizedTerm(
            term=variation,
            term_type=EntityType.VARIATION,
            normalized_id=normalized_variation,
        )

    def _get_stmt_by_id(self, statement_id: str) -> Node | None:
        """Get a Statement node by ID.

        :param statement_id: Statement ID to retrieve
        :return: Statement node if successful
        """
        query = """
        MATCH (s:Statement)
        WHERE toLower(s.id) = toLower($statement_id)
        RETURN s
        """
        records = self.driver.execute_query(query, statement_id=statement_id).records
        if not records:
            return None
        return records[0]["s"]

    def _get_statements(
        self,
        start: int,
        limit: int | None,
        normalized_variation: str | None = None,
        normalized_therapy: str | None = None,
        normalized_disease: str | None = None,
        normalized_gene: str | None = None,
    ) -> list[Node]:
        """Get statements that match the intersection of provided concepts.

        :param start: Index of first result to fetch. Calling context should've already
            checked that it's nonnegative.
        :param limit: Max number of results to fetch. Calling context should've already
            checked that it's nonnegative.
        :param normalized_variation: VRS Variation ID
        :param normalized_therapy: normalized therapy concept ID
        :param normalized_disease: normalized disease concept ID
        :param normalized_gene: normalized gene concept ID
        :return: List of Statement nodes that match the intersection of the given
            parameters
        """
        query = "MATCH (s:Statement)"
        params: dict[str, str | int] = {}

        if normalized_variation:
            query += """
            MATCH (s) -[:HAS_SUBJECT_VARIANT]-> (cv: CategoricalVariant)
            MATCH (a:Allele { id: $v_id })
            WHERE
                EXISTS {
                    MATCH (cv)-[:HAS_CONSTRAINT]->(con:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->(a)
                }
                OR
                EXISTS {
                    MATCH (cv)-[:HAS_MEMBER]->(a)
                }
            """
            params["v_id"] = normalized_variation

        if normalized_disease:
            query += """
            MATCH (s) -[:HAS_TUMOR_TYPE] -> (c:Condition {normalizer_id:$c_id})
            """
            params["c_id"] = normalized_disease

        if normalized_gene:
            query += """
            MATCH (s) -[:HAS_GENE_CONTEXT] -> (g:Gene {normalizer_id:$g_id})
            """
            params["g_id"] = normalized_gene

        if normalized_therapy:
            query += """
            OPTIONAL MATCH (s) -[:HAS_THERAPEUTIC] -> (tp:Therapy {normalizer_id:$t_id})
            OPTIONAL MATCH (s) -[:HAS_THERAPEUTIC] -> () -[:HAS_SUBSTITUTES|HAS_COMPONENTS] -> (ta:Therapy {normalizer_id:$t_id})
            WITH s, tp, ta
            WHERE tp IS NOT NULL OR ta IS NOT NULL
            """
            params["t_id"] = normalized_therapy

        query += """
        RETURN DISTINCT s
        ORDER BY s.id
        """

        if start:
            query += "\nSKIP $start"
            params["start"] = start
        limit_candidate = limit if limit is not None else self._default_page_limit
        if limit_candidate is not None:
            query += "\nLIMIT $limit"
            params["limit"] = limit_candidate

        return [s[0] for s in self.driver.execute_query(query, params).records]

    def _get_nested_stmts(
        self, statement_nodes: list[Node]
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        """Get a list of nested statements.

        :param statement_nodes: A list of Statement Nodes
        :return: A list of nested statements
        """
        nested_stmts = []
        added_stmts = set()
        for s in statement_nodes:
            s_id = s.get("id")
            if s_id not in added_stmts:
                nested_stmt = self._get_nested_stmt(s)
                if nested_stmt:
                    nested_stmts.append(nested_stmt)
                    added_stmts.add(s_id)
        return nested_stmts

    def _get_nested_stmt(
        self, stmt_node: Node
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ):
        """Get information related to a statement

        :param stmt_node: Neo4j graph node for statement
        :return: Nested statement
        """
        prop_type = stmt_node["propositionType"]
        if prop_type not in PROP_TYPE_TO_CLASS:
            return {}

        if prop_type == "VariantTherapeuticResponseProposition":
            condition_key = "conditionQualifier"
        else:
            condition_key = "objectCondition"

        params = {
            "proposition": {
                "alleleOriginQualifier": {"name": None},
                "predicate": stmt_node["predicate"],
                condition_key: None,
            },
            "strength": None,
            "specifiedBy": None,
        }
        params.update(stmt_node)
        for prop_field in {
            "predicate",
            "alleleOriginQualifier",
            condition_key,
        }:
            params.pop(prop_field, None)

        statement_id = stmt_node["id"]

        # Get relationship and nodes for a statement
        query = """
        MATCH (s:Statement { id: $statement_id })
        OPTIONAL MATCH (s)-[r]-(n)
        RETURN type(r) as r_type, n;
        """
        nodes_and_rels = self.driver.execute_query(
            query, statement_id=statement_id
        ).records

        has_evidence_lines = False  # this is used to determine evidence vs assertion

        for item in nodes_and_rels:
            data = item.data()
            rel_type = data["r_type"]
            node = data["n"]

            if rel_type == "HAS_TUMOR_TYPE":
                params["proposition"][condition_key] = self._get_disease(node)
            elif rel_type == "HAS_SUBJECT_VARIANT":
                params["proposition"]["subjectVariant"] = self._get_cat_var(node)
            elif rel_type == "HAS_GENE_CONTEXT":
                params["proposition"]["geneContextQualifier"] = (
                    self._get_gene_context_qualifier(statement_id)
                )
                params["proposition"]["alleleOriginQualifier"]["name"] = stmt_node.get(
                    "alleleOriginQualifier"
                )
            elif rel_type == "IS_SPECIFIED_BY":
                node["reportedIn"] = self._get_method_document(node["id"])
                params["specifiedBy"] = Method(**node)
            elif rel_type == "IS_REPORTED_IN":
                params["reportedIn"] = [self._get_document(node)]
            elif rel_type == "HAS_STRENGTH":
                for k in ("mappings", "primaryCoding"):
                    if k in node:
                        node[k] = json.loads(node[k])
                params["strength"] = MappableConcept(**node)
            elif rel_type == "HAS_THERAPEUTIC":
                params["proposition"]["objectTherapeutic"] = self._get_therapy_or_group(
                    node
                )
            elif rel_type == "HAS_CLASSIFICATION":
                node["primaryCoding"] = json.loads(node["primaryCoding"])
                params["classification"] = MappableConcept(**node)
            elif rel_type == "HAS_EVIDENCE_LINE":
                has_evidence_lines = True
                params["hasEvidenceLines"] = self._get_evidence_lines(statement_id)

        proposition_type = params.pop("propositionType", None)
        if has_evidence_lines:  # assertions should use AAC 2017 study statements
            return PROP_TYPE_TO_CLASS[prop_type](**params)

        params["proposition"]["type"] = proposition_type
        return Statement(**params)

    def _get_disease(self, node: dict) -> MappableConcept:
        """Get disease data from a node with relationship ``HAS_TUMOR_TYPE``

        :param node: Disease node data
        :return: Disease mappable concept object
        """
        node.pop("normalizer_id")
        node["mappings"] = _deserialize_field(node, "mappings")
        extensions = []
        descr = node.pop("description", None)
        if descr:
            extensions.append(Extension(name="description", value=descr))
        aliases = node.pop("aliases", None)
        if aliases:
            extensions.append(Extension(name="aliases", value=json.loads(aliases)))

        if extensions:
            node["extensions"] = extensions
        return MappableConcept(**node)

    @staticmethod
    def _rebuild_allele(
        allele_node: Node, location_node: Node, state_node: Node
    ) -> Allele:
        """Reconstruct allele from graph nodes

        :param allele_node: allele node
        :param location_node: location node
        :param state_node: state node
        :return: constructed VRS allele
        """
        if state_node.labels == {"SequenceExpression", "LiteralSequenceExpression"}:
            state = LiteralSequenceExpression(sequence=state_node["sequence"])
        elif state_node.labels == {"SequenceExpression", "ReferenceLengthExpression"}:
            state = ReferenceLengthExpression(
                length=state_node["length"],
                repeatSubunitLength=state_node["repeat_subunit_length"],
                sequence=state_node["sequence"],
            )
        else:
            msg = f"Unrecognized set of sequence expression node labels: {state_node.labels}"
            raise ValueError(msg)

        location = SequenceLocation(
            start=location_node["start"],
            end=location_node["end"],
            id=location_node["id"],
            sequenceReference={"refgetAccession": location_node["refget_accession"]},
            sequence=location_node["sequence"],
            digest=location_node.get("digest"),
        )
        expressions = []
        for expression_type, expression in [
            (k, v) for k, v in allele_node.items() if k.startswith("expression")
        ]:
            syntax = expression_type.split("expression_")[-1].replace("_", ".")
            expressions.extend(Expression(syntax=syntax, value=v) for v in expression)
        return Allele(
            state=state,
            location=location,
            id=allele_node["id"],
            digest=allele_node.get("digest"),
            expressions=expressions or None,
            name=allele_node.get("name") or None,
            description=allele_node.get("description"),
            aliases=allele_node.get("aliases"),
            extensions=allele_node.get("extensions"),
        )

    def _get_cat_var(self, node: dict) -> CategoricalVariant:
        """Get categorical variant data from a node with relationship ``HAS_VARIANT``

        :param node: Variant node data. This will be mutated.
        :return: Categorical Variant data
        """
        node["mappings"] = _deserialize_field(node, "mappings")
        node["extensions"] = _deserialize_field(node, "extensions")

        related_alleles_query = """
        MATCH (cv:CategoricalVariant {id: $cv_id})
        MATCH (cv)-[:HAS_CONSTRAINT]->(dac:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->(defining_allele:Allele)
        MATCH (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
        MATCH (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)
        OPTIONAL MATCH
            (cv)-[:HAS_MEMBER]->(member_allele:Allele)-[HAS_LOCATION]->(member_allele_sl:SequenceLocation),
            (member_allele)-[:HAS_STATE]->(member_allele_se:SequenceExpression)

        // if there are member alleles, collect them into joint objects
        WITH
            cv, defining_allele, defining_allele_sl, defining_allele_se, member_allele,
            member_allele_sl, member_allele_se
            WHERE member_allele IS NULL OR (
                member_allele IS NOT NULL
                AND member_allele_sl IS NOT NULL
                AND member_allele_se IS NOT NULL
            )
        WITH
            cv, defining_allele, defining_allele_sl, defining_allele_se,
            COLLECT(CASE
                WHEN member_allele IS NOT NULL THEN {
                    allele: member_allele,
                    location: member_allele_sl,
                    state: member_allele_se
                }
            END) AS members

        RETURN cv, defining_allele, defining_allele_sl, defining_allele_se, members
        """
        record = self.driver.execute_query(
            related_alleles_query, cv_id=node["id"]
        ).records[0]

        constraint = DefiningAlleleConstraint(
            allele=self._rebuild_allele(
                record["defining_allele"],
                record["defining_allele_sl"],
                record["defining_allele_se"],
            )
        )

        members = [
            self._rebuild_allele(r["allele"], r["location"], r["state"])
            for r in record.get("members", [])
        ]
        return CategoricalVariant(
            name=node.get("name"),
            description=node.get("description"),
            extensions=node.get("extensions"),
            aliases=node.get("aliases"),
            constraints=[constraint],
            members=members,
            id=node["id"],
            mappings=node["mappings"],
        )

    def _get_gene_context_qualifier(self, statement_id: str) -> MappableConcept | None:
        """Get gene context qualifier data for a statement

        :param statement_id: ID of statement node
        :return Gene context qualifier data
        """
        query = """
        MATCH (s:Statement { id: $statement_id }) -[:HAS_GENE_CONTEXT] -> (g:Gene)
        RETURN g
        """
        results = self.driver.execute_query(query, statement_id=statement_id)
        if not results.records:
            _logger.error(
                "Unable to complete gene context qualifier lookup for statement_id %s",
                statement_id,
            )
            return None
        if len(results.records) > 1:
            # TODO should this be an error? can statements have multiple gene contexts?
            _logger.error(
                "Encountered multiple matches for gene context qualifier lookup for statement_id %s",
                statement_id,
            )
            return None

        gene_node = results.records[0].data()["g"]
        gene_node["mappings"] = _deserialize_field(gene_node, "mappings")
        extensions = []
        descr = gene_node.pop("description", None)
        if descr:
            extensions.append(Extension(name="description", value=descr))
        aliases = gene_node.pop("aliases", None)
        if aliases:
            extensions.append(Extension(name="aliases", value=json.loads(aliases)))

        if extensions:
            gene_node["extensions"] = extensions

        gene_node.pop("normalizer_id")
        return MappableConcept(**gene_node)

    def _get_method_document(self, method_id: str) -> Document | None:
        """Get document for a given method

        :param method_id: ID for method
        :return: Document
        """
        query = """
        MATCH (m:Method { id: $method_id }) -[:IS_REPORTED_IN] -> (d:Document)
        RETURN d
        """
        records = self.driver.execute_query(query, method_id=method_id).records
        if not records:
            return None

        doc_params = records[0].data()["d"]
        return Document(**doc_params)

    @staticmethod
    def _get_document(node: dict) -> Document:
        """Get document data from a node with relationship ``IS_SPECIFIED_BY``

        :param node: Document node data. This will be mutated
        :return: Document data
        """
        source_type = node.pop("source_type", None)
        if source_type:
            node["extensions"] = [Extension(name="source_type", value=source_type)]
        return Document(**node)

    def _get_therapy_or_group(
        self,
        node: dict,
    ) -> MappableConcept | None:
        """Get therapy or therapy group from a node with relationship ``HAS_THERAPEUTIC``

        :param node: Therapy node data. This will be mutated.
        :return: Therapy if node type is supported.
        """
        node_type = node.get("membershipOperator") or node.get("conceptType")
        if node_type in MembershipOperator.__members__.values():
            moa_therapy_type = node.pop("moa_therapy_type", None)
            if moa_therapy_type:
                node["extensions"] = [
                    Extension(name="moa_therapy_type", value=moa_therapy_type)
                ]

            tp_relation = (
                TherapeuticRelation.HAS_COMPONENTS
                if node_type == MembershipOperator.AND
                else TherapeuticRelation.HAS_SUBSTITUTES
            )
            node["therapies"] = self._get_therapies(
                node["id"],
                tp_relation,
            )
            therapy = TherapyGroup(**node)
        elif node_type == "Therapy":
            therapy = self._get_therapy(node)
        else:
            _logger.warning("node type not supported: %s", node_type)
            therapy = None

        return therapy

    def _get_evidence_lines(self, statement_id: int) -> list[EvidenceLine]:
        """Get EvidenceLine data from a node with relationship ``HAS_CLASSIFICATION``

        :param statement_id: Statement ID to get evidence lines for
        :return: EvidenceLine data for a given ``statement_id``
        """
        evidence_lines = []

        query = f"""
        MATCH (s:StudyStatement {{id: '{statement_id}'}}) -[:HAS_EVIDENCE_LINE] -> (el:EvidenceLine)
        OPTIONAL MATCH (el) -[:HAS_EVIDENCE_ITEM] -> (ev:Statement)
        RETURN DISTINCT el, ev
        """
        results = self.driver.execute_query(query).records
        for r in results:
            r_params = r.data()
            evidence_lines.append(
                EvidenceLine(
                    hasEvidenceItems=[self._get_nested_stmt(r_params["ev"])],
                    directionOfEvidenceProvided=Direction(r_params["el"]["direction"]),
                )
            )

        return evidence_lines

    def _get_therapies(
        self,
        tp_id: str,
        tp_relation: TherapeuticRelation,
    ) -> list[MappableConcept]:
        """Get list of therapies for therapeutic combination or substitutes group

        :param tp_id: ID for combination therapy or therapeutic substitute group
        :param tp_relation: Relationship type for therapies
        :return: List of therapies represented as Mappable Concepts for a combination
            therapy or therapeutic substitute group
        """
        query = f"""
        MATCH (tp:TherapyGroup {{ id: $tp_id }}) -[:{tp_relation.value}]
            -> (ta:Therapy)
        RETURN ta
        """
        therapies = []
        results = self.driver.execute_query(query, tp_id=tp_id).records
        for r in results:
            r_params = r.data()
            ta_params = r_params["ta"]
            ta = self._get_therapy(ta_params)
            therapies.append(ta)
        return therapies

    def _get_therapy(self, in_ta_params: dict) -> MappableConcept:
        """Transform input parameters into Therapy object

        :param in_ta_params: Therapy node properties
        :return: Therapy represented as a mappable concept
        """
        ta_params = copy(in_ta_params)
        ta_params.pop("normalizer_id")
        ta_params["mappings"] = _deserialize_field(ta_params, "mappings")
        extensions = []
        regulatory_approval = ta_params.pop("regulatory_approval", None)
        if regulatory_approval:
            regulatory_approval = json.loads(regulatory_approval)
            extensions.append(
                Extension(name="regulatory_approval", value=regulatory_approval)
            )
        aliases = ta_params.pop("aliases", None)
        if aliases:
            extensions.append(Extension(name="aliases", value=json.loads(aliases)))

        if extensions:
            ta_params["extensions"] = extensions
        return MappableConcept(**ta_params)
