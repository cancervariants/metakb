"""Provide search services."""

from enum import Enum
from typing import Literal

from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Statement
from pydantic import BaseModel

from metakb.normalizers import ViccNormalizers
from metakb.repository.base import AbstractRepository


class EntityType(str, Enum):
    """Type of entity being searched."""

    VARIATION = "variation"
    DISEASE = "disease"
    THERAPY = "therapy"
    GENE = "gene"


class NormalizedTerm(BaseModel):
    """Normalized biomedical entity search term.

    Include user-provided input, the kind of entity, and the ID it normalizes to.
    """

    type: Literal["NormalizedTerm"] = "NormalizedTerm"
    term: str
    term_type: EntityType
    normalized_id: str | None = None


class StatementIdTerm(BaseModel):
    """Statement ID search term."""

    type: Literal["StatementIdTerm"] = "StatementIdTerm"
    term: str
    term_type: Literal["statement_id"] = "statement_id"
    validated_statement_id: str | None


class SearchResult(BaseModel):
    """Results of a search.

    Includes both processed search terms and all statements.
    """

    search_terms: list[NormalizedTerm | StatementIdTerm]
    statements: list[
        Statement
        | VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = []
    start: int = 0
    limit: int | None = None


class EmptySearchError(Exception):
    """Raise for invalid search parameters (e.g. no parameters given)"""


class PaginationParamError(Exception):
    """Raise for invalid pagination parameters."""


async def search_statements(
    repository: AbstractRepository,
    normalizer: ViccNormalizers,
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
        statement = self._get_stmt_by_id(statement_id)  # TODO not sure what to do here
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
            normalized_gene=normalized_gene.normalized_id if normalized_gene else None,
            start=start,
            limit=limit,
        )
    statements = self._get_nested_stmts(statement_nodes)
    return SearchResult(
        search_terms=search_terms, start=start, limit=limit, statements=statements
    )
