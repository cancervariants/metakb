"""Test batch search function."""

import pytest

from metakb.repository.base import AbstractRepository
from metakb.schemas.api import SearchTerm, SearchTermType
from metakb.services.search import PaginationParamError, batch_search_statements

from .utils import assert_no_match, find_and_check_stmt


@pytest.mark.asyncio(scope="module")
async def test_batch_search(
    repository: AbstractRepository,
    normalizers,
    assertion_checks,
    civic_eid2997_study_stmt,
    civic_eid816_study_stmt,
):
    """Test batch search statements method."""
    resp = await batch_search_statements(repository, normalizers, variations=[])
    assert resp.statements == []

    assert_no_match(
        await batch_search_statements(repository, normalizers, ["gibberish variant"])
    )

    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    braf_response = await batch_search_statements(repository, normalizers, [braf_va_id])
    assert braf_response.search_terms == [
        SearchTerm(
            term=braf_va_id,
            term_type=SearchTermType.VARIATION,
            resolved_id=braf_va_id,
        )
    ]
    find_and_check_stmt(braf_response, civic_eid816_study_stmt, assertion_checks)

    redundant_braf_response = await batch_search_statements(
        repository, normalizers, [braf_va_id, "NC_000007.13:g.140453136A>T"]
    )
    assert len(redundant_braf_response.search_terms) == 2
    assert (
        SearchTerm(
            term=braf_va_id,
            term_type=SearchTermType.VARIATION,
            resolved_id=braf_va_id,
        )
        in redundant_braf_response.search_terms
    )
    assert (
        SearchTerm(
            term="NC_000007.13:g.140453136A>T",
            term_type=SearchTermType.VARIATION,
            resolved_id=braf_va_id,
        )
        in redundant_braf_response.search_terms
    )

    find_and_check_stmt(
        redundant_braf_response, civic_eid816_study_stmt, assertion_checks
    )
    assert len(braf_response.statements) == len(redundant_braf_response.statements)

    braf_egfr_response = await batch_search_statements(
        repository, normalizers, [braf_va_id, "EGFR L858R"]
    )
    find_and_check_stmt(braf_egfr_response, civic_eid816_study_stmt, assertion_checks)
    find_and_check_stmt(braf_egfr_response, civic_eid2997_study_stmt, assertion_checks)
    assert len(braf_egfr_response.statements) > len(braf_response.statements)


@pytest.mark.asyncio(scope="module")
async def test_paginate(repository: AbstractRepository, normalizers):
    """Test pagination parameters."""
    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    full_response = await batch_search_statements(repository, normalizers, [braf_va_id])
    paged_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], start=1
    )
    # should be almost the same, just off by 1
    assert len(paged_response.statements) == len(full_response.statements) - 1
    assert paged_response.statements == full_response.statements[1:]

    # check that page limit > response doesn't affect response
    huge_page_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], limit=1000
    )
    assert len(huge_page_response.statements) == len(full_response.statements)
    assert huge_page_response.statements == full_response.statements

    # get last item
    last_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], start=len(full_response.statements) - 1
    )
    assert len(last_response.statements) == 1
    assert last_response.statements[0] == full_response.statements[-1]

    # test limit
    min_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], limit=1
    )
    assert min_response.statements[0] == full_response.statements[0]

    # test limit and start
    other_min_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], start=1, limit=1
    )
    assert other_min_response.statements[0] == full_response.statements[1]

    # test limit of 0
    empty_response = await batch_search_statements(
        repository, normalizers, [braf_va_id], limit=0
    )
    assert len(empty_response.statements) == 0

    # test raises exceptions
    with pytest.raises(
        PaginationParamError, match="Invalid start value: -1. Must be nonnegative."
    ):
        await batch_search_statements(repository, normalizers, [braf_va_id], start=-1)
    with pytest.raises(
        PaginationParamError, match="Invalid limit value: -1. Must be nonnegative."
    ):
        await batch_search_statements(repository, normalizers, [braf_va_id], limit=-1)
