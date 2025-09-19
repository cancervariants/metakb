"""Provide class/methods/schemas for issuing queries against the database."""

import json
import logging
from enum import Enum

from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from neo4j import Driver

from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.repository.neo4j_repository import Neo4jRepository, get_driver
from metakb.schemas.api import (
    SearchResult,
    SearchTerm,
    SearchTermType,
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
        self.repository = Neo4jRepository(driver)
        if normalizers is None:
            normalizers = ViccNormalizers()
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
        statement, statement_term = None, None
        if statement_id:
            statement = self._get_stmt_by_id(statement_id)
            statement_term = SearchTerm(
                term=statement_id,
                term_type=SearchTermType.STATEMENT_ID,
                resolved_id=statement.get("id") if statement else None,
            )
            search_terms.append(statement_term)
        statements = self.repository.search_statements(
            variation_id=normalized_variation,
            gene_id=normalized_gene,
            disease_id=normalized_disease,
            therapy_id=normalized_therapy,
            start=start,
            limit=limit,
        )
        response["statements"] = statements

        if not response["statements"]:
            response["warnings"].append(
                "No statements found with the provided query parameters."
            )

        return SearchStatementsService(**response)

    def _get_normalized_disease(self, disease: str) -> SearchTerm:
        """Get normalized disease concept.

        :param disease: Disease query
        :return: A normalized disease concept if it exists
        """
        _, disease_id = self.vicc_normalizers.normalize_disease(disease)
        return SearchTerm(
            term=disease, term_type=SearchTermType.DISEASE, resolved_id=disease_id
        )

    def _get_normalized_gene(self, gene: str) -> SearchTerm:
        """Get normalized gene concept.

        :param gene: Gene query
        :return: A normalized gene concept if it exists
        """
        _, gene_id = self.vicc_normalizers.normalize_gene(gene)
        return SearchTerm(term=gene, term_type=SearchTermType.GENE, resolved_id=gene_id)

    def _get_normalized_therapy(self, therapy: str) -> SearchTerm:
        """Get normalized therapy concept.

        :param therapy: Therapy query
        :return: A normalized therapy concept if it exists
        """
        _, therapy_id = self.vicc_normalizers.normalize_therapy(therapy)
        return SearchTerm(
            term=therapy, term_type=SearchTermType.THERAPY, resolved_id=therapy_id
        )

    async def _get_normalized_variation(self, variation: str) -> SearchTerm:
        """Get normalized variation concept.

        :param variation: Variation query
        :return: A normalized variant concept if it exists
        """
        # Check if VRS variation (allele, copy number change, copy number count)
        if variation.startswith(("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")):
            normalized_variation = variation
        else:
            variant_norm_resp = await self.vicc_normalizers.normalize_variation(
                variation
            )
            normalized_variation = variant_norm_resp.id if variant_norm_resp else None

        return SearchTerm(
            term=variation,
            term_type=SearchTermType.VARIATION,
            resolved_id=normalized_variation,
        )

    async def _get_normalized_terms(
        self,
        variation: str | None,
        disease: str | None,
        therapy: str | None,
        gene: str | None,
        statement_id: str | None,
        response: dict,
    ) -> tuple | None:
        """Find normalized terms for queried concepts.

        :param variation: Variation (subject) query
        :param disease: Disease (object_qualifier) query
        :param therapy: Therapy (object) query
        :param gene: Gene query
        :param statement_id: Statement ID query
        :param response: The response for the query
        :return: A tuple containing the normalized concepts
        """
        if therapy:
            response["query"]["therapy"] = therapy
            normalized_therapy = self._get_normalized_therapy(
                therapy.strip(), response["warnings"]
            )
        else:
            normalized_therapy = None
        if disease:
            response["query"]["disease"] = disease
            normalized_disease = self._get_normalized_disease(
                disease.strip(), response["warnings"]
            )
        else:
            normalized_disease = None
        if variation:
            response["query"]["variation"] = variation
            normalized_variation = await self._get_normalized_variation(
                variation, response["warnings"]
            )
        else:
            normalized_variation = None
        if gene:
            response["query"]["gene"] = gene
            normalized_gene = self._get_normalized_gene(gene, response["warnings"])
        else:
            normalized_gene = None

        # Check that queried statement_id is valid
        valid_statement_id = None
        statement = None
        if statement_id:
            response["query"]["statement_id"] = statement_id
            statement = self._get_stmt_by_id(statement_id)
            if statement:
                valid_statement_id = statement.get("id")
            else:
                response["warnings"].append(
                    f"Statement: {statement_id} does not exist."
                )

        # If queried concept is given check that it is normalized / valid
        if (
            (variation and not normalized_variation)
            or (therapy and not normalized_therapy)
            or (disease and not normalized_disease)
            or (gene and not normalized_gene)
            or (statement_id and not valid_statement_id)
        ):
            return None

        return (
            normalized_variation,
            normalized_disease,
            normalized_therapy,
            normalized_gene,
            statement,
            valid_statement_id,
=======
        # Check that queried statement_id is valid
        statement, statement_term = None, None
        if statement_id:
            statement = self._get_stmt_by_id(statement_id)
            statement_term = SearchTerm(
                term=statement_id,
                term_type=SearchTermType.STATEMENT_ID,
                resolved_id=statement.get("id") if statement else None,
            )
            search_terms.append(statement_term)

        # return early if ANY search terms fail to resolve
        if any(
            obj and obj.resolved_id is None
            for obj in (
                normalized_therapy,
                normalized_disease,
                normalized_variation,
                statement_term,
            )
        ):
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
                normalized_variation=normalized_variation.resolved_id
                if normalized_variation
                else None,
                normalized_therapy=normalized_therapy.resolved_id
                if normalized_therapy
                else None,
                normalized_disease=normalized_disease.resolved_id
                if normalized_disease
                else None,
                normalized_gene=normalized_gene.resolved_id
                if normalized_gene
                else None,
                start=start,
                limit=limit,
            )
        statements = self._get_nested_stmts(statement_nodes)
        return SearchResult(
            search_terms=search_terms, start=start, limit=limit, statements=statements
>>>>>>> staging
        )

    def _get_normalized_disease(self, disease: str) -> SearchTerm:
        """Get normalized disease concept.

        :param disease: Disease query
        :return: A normalized disease concept if it exists
        """
        _, disease_id = self.vicc_normalizers.normalize_disease(disease)
        return SearchTerm(
            term=disease, term_type=SearchTermType.DISEASE, resolved_id=disease_id
        )

    def _get_normalized_gene(self, gene: str) -> SearchTerm:
        """Get normalized gene concept.

        :param gene: Gene query
        :return: A normalized gene concept if it exists
        """
        _, gene_id = self.vicc_normalizers.normalize_gene(gene)
        return SearchTerm(term=gene, term_type=SearchTermType.GENE, resolved_id=gene_id)

    def _get_normalized_therapy(self, therapy: str) -> SearchTerm:
        """Get normalized therapy concept.

        :param therapy: Therapy query
        :return: A normalized therapy concept if it exists
        """
        _, therapy_id = self.vicc_normalizers.normalize_therapy(therapy)
        return SearchTerm(
            term=therapy, term_type=SearchTermType.THERAPY, resolved_id=therapy_id
        )

    async def _get_normalized_variation(self, variation: str) -> SearchTerm:
        """Get normalized variation concept.

        :param variation: Variation query
        :return: A normalized variant concept if it exists
        """
        # Check if VRS variation (allele, copy number change, copy number count)
        if variation.startswith(("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")):
            normalized_variation = variation
        else:
            variant_norm_resp = await self.vicc_normalizers.normalize_variation(
                variation
            )
            normalized_variation = variant_norm_resp.id if variant_norm_resp else None

        return SearchTerm(
            term=variation,
            term_type=SearchTermType.VARIATION,
            resolved_id=normalized_variation,
        )

    async def batch_search_statements(
        self,
        variations: list[str] | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> SearchResult:
        """Fetch all statements associated with any of the provided variation description
        strings.

        Because this method could be expanded to include other kinds of search terms,
        ``variations`` is optionally nullable.

        >>> from metakb.query import QueryHandler
        >>> qh = QueryHandler()
        >>> response = await qh.batch_search_statements(["EGFR L858R"])
        >>> response.statement_ids[:3]
        ['civic.eid:229', 'civic.eid:3811', 'moa.assertion:268']

        All terms are normalized, so redundant terms don't alter search results:

        >>> redundant_response = await qh.batch_search_statements(
        ...     ["EGFR L858R", "NP_005219.2:p.Leu858Arg"]
        ... )
        >>> len(response.statement_ids) == len(redundant_response.statement_ids)
        True

        :param variations: a list of variation description strings, e.g.
            ``["BRAF V600E"]``
        :param start: Index of first result to fetch. Must be nonnegative.
        :param limit: Max number of results to fetch. Must be nonnegative. Revert to
            default defined at class initialization if not given.
        :return: response object including all matching statements
        :raise ValueError: if ``start`` or ``limit`` are nonnegative
        :raise EmptySearchError: if no search params given
        :raise PaginationParamError: if either pagination param given is negative
        """
        if start < 0:
            msg = f"Invalid start value: {start}. Must be nonnegative."
            raise PaginationParamError(msg)
        if isinstance(limit, int) and limit < 0:
            msg = f"Invalid limit value: {limit}. Must be nonnegative."
            raise PaginationParamError(msg)

        if not variations:
            return SearchResult(
                search_terms=[], start=start, limit=limit, statements=[]
            )

        search_terms = [
            await self._get_normalized_variation(v) for v in set(variations)
        ]
        variation_ids = [t.resolved_id for t in search_terms]
        if not all(variation_ids):
            return SearchResult(
                search_terms=search_terms, start=start, limit=limit, statements=[]
            )

        raise NotImplementedError
