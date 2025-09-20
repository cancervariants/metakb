"""Provide search services."""

import logging
from enum import Enum

from metakb.normalizers import ViccNormalizers
from metakb.repository.base import AbstractRepository
from metakb.schemas.api import SearchResult, SearchTerm, SearchTermType

_logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Type of entity being searched."""

    VARIATION = "variation"
    DISEASE = "disease"
    THERAPY = "therapy"
    GENE = "gene"


class EmptySearchError(Exception):
    """Raise for invalid search parameters (e.g. no parameters given)"""


class PaginationParamError(Exception):
    """Raise for invalid pagination parameters."""


def _get_normalized_disease(normalizer: ViccNormalizers, disease: str) -> SearchTerm:
    """Get normalized disease concept.

    :param normalizer:
    :param disease: Disease query
    :return: A normalized disease concept if it exists
    """
    _, disease_id = normalizer.normalize_disease(disease)
    return SearchTerm(
        term=disease, term_type=SearchTermType.DISEASE, resolved_id=disease_id
    )


def _get_normalized_gene(normalizer: ViccNormalizers, gene: str) -> SearchTerm:
    """Get normalized gene concept.

    :param normalizer:
    :param gene: Gene query
    :return: A normalized gene concept if it exists
    """
    _, gene_id = normalizer.normalize_gene(gene)
    return SearchTerm(term=gene, term_type=SearchTermType.GENE, resolved_id=gene_id)


def _get_normalized_therapy(normalizer: ViccNormalizers, therapy: str) -> SearchTerm:
    """Get normalized therapy concept.

    :param normalizer:
    :param therapy: Therapy query
    :return: A normalized therapy concept if it exists
    """
    _, therapy_id = normalizer.normalize_therapy(therapy)
    return SearchTerm(
        term=therapy, term_type=SearchTermType.THERAPY, resolved_id=therapy_id
    )


async def _get_normalized_variation(
    normalizer: ViccNormalizers, variation: str
) -> SearchTerm:
    """Get normalized variation concept.

    :param normalizer:
    :param variation: Variation query
    :return: A normalized variant concept if it exists
    """
    # Check if VRS variation (allele, copy number change, copy number count)
    if variation.startswith(("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")):
        normalized_variation = variation
    else:
        variant_norm_resp = await normalizer.normalize_variation(variation)
        normalized_variation = variant_norm_resp.id if variant_norm_resp else None

    return SearchTerm(
        term=variation,
        term_type=SearchTermType.VARIATION,
        resolved_id=normalized_variation,
    )


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

    :param repository:
    :param normalizer:
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
        normalized_therapy = _get_normalized_therapy(normalizer, therapy)
        search_terms.append(normalized_therapy)
    if disease:
        normalized_disease = _get_normalized_disease(normalizer, disease)
        search_terms.append(normalized_disease)
    if variation:
        normalized_variation = await _get_normalized_variation(normalizer, variation)
        search_terms.append(normalized_variation)
    if gene:
        normalized_gene = _get_normalized_gene(normalizer, gene)
        search_terms.append(normalized_gene)

    # Check that queried statement_id is valid
    # TODO figure out how to implement
    statement, statement_term = None, None
    if statement_id:
        statement = repository.get_statement(statement_id)
        statement_term = SearchTerm(
            term=statement_id,
            term_type=SearchTermType.STATEMENT_ID,
            resolved_id=statement.id if statement else None,
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

    if statement:
        statements = [statement]
    else:
        statements = repository.search_statements(
            normalized_variation.resolved_id if normalized_variation else None,
            normalized_gene.resolved_id if normalized_gene else None,
            normalized_therapy.resolved_id if normalized_therapy else None,
            normalized_disease.resolved_id if normalized_disease else None,
            statement_id=None,
            start=start,
            limit=limit,
        )
    return SearchResult(
        search_terms=search_terms, start=start, limit=limit, statements=statements
    )
