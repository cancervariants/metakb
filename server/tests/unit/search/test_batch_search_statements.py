"""Test batch search function."""

import pytest

from metakb.query import QueryHandler
from metakb.schemas.api import NormalizedQuery

from .utils import assert_no_match, find_and_check_stmt


@pytest.mark.asyncio(scope="module")
async def test_batch_search(
    query_handler: QueryHandler,
    assertion_checks,
    civic_eid2997_study_stmt,
    civic_eid816_study_stmt,
):
    """Test batch search statements method."""
    resp = await query_handler.batch_search_statements([])
    assert resp.statements == resp.statement_ids == []
    assert resp.warnings == []

    assert_no_match(await query_handler.batch_search_statements(["gibberish variant"]))

    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    braf_response = await query_handler.batch_search_statements([braf_va_id])
    assert braf_response.query.variations == [
        NormalizedQuery(
            term=braf_va_id,
            normalized_id=braf_va_id,
        )
    ]
    find_and_check_stmt(braf_response, civic_eid816_study_stmt, assertion_checks)

    redundant_braf_response = await query_handler.batch_search_statements(
        [braf_va_id, "NC_000007.13:g.140453136A>T"]
    )
    assert len(redundant_braf_response.query.variations) == 2
    assert (
        NormalizedQuery(
            term=braf_va_id,
            normalized_id=braf_va_id,
        )
        in redundant_braf_response.query.variations
    )
    assert (
        NormalizedQuery(
            term="NC_000007.13:g.140453136A>T",
            normalized_id=braf_va_id,
        )
        in redundant_braf_response.query.variations
    )

    find_and_check_stmt(
        redundant_braf_response, civic_eid816_study_stmt, assertion_checks
    )
    assert len(braf_response.statement_ids) == len(
        redundant_braf_response.statement_ids
    )

    braf_egfr_response = await query_handler.batch_search_statements(
        [braf_va_id, "EGFR L858R"]
    )
    find_and_check_stmt(braf_egfr_response, civic_eid816_study_stmt, assertion_checks)
    find_and_check_stmt(braf_egfr_response, civic_eid2997_study_stmt, assertion_checks)
    assert len(braf_egfr_response.statement_ids) > len(braf_response.statement_ids)


@pytest.mark.asyncio(scope="module")
async def test_paginate(query_handler: QueryHandler, normalizers):
    """Test pagination parameters."""
    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    full_response = await query_handler.batch_search_statements([braf_va_id])
    paged_response = await query_handler.batch_search_statements([braf_va_id], start=1)
    # should be almost the same, just off by 1
    assert len(paged_response.statement_ids) == len(full_response.statement_ids) - 1
    assert paged_response.statement_ids == full_response.statement_ids[1:]

    # check that page limit > response doesn't affect response
    huge_page_response = await query_handler.batch_search_statements(
        [braf_va_id], limit=1000
    )
    assert len(huge_page_response.statement_ids) == len(full_response.statement_ids)
    assert huge_page_response.statement_ids == full_response.statement_ids

    # get last item
    last_response = await query_handler.batch_search_statements(
        [braf_va_id], start=len(full_response.statement_ids) - 1
    )
    assert len(last_response.statement_ids) == 1
    assert last_response.statement_ids[0] == full_response.statement_ids[-1]

    # test limit
    min_response = await query_handler.batch_search_statements([braf_va_id], limit=1)
    assert min_response.statement_ids[0] == full_response.statement_ids[0]

    # test limit and start
    other_min_response = await query_handler.batch_search_statements(
        [braf_va_id], start=1, limit=1
    )
    assert other_min_response.statement_ids[0] == full_response.statement_ids[1]

    # test limit of 0
    empty_response = await query_handler.batch_search_statements([braf_va_id], limit=0)
    assert len(empty_response.statement_ids) == 0

    # test raises exceptions
    with pytest.raises(ValueError, match="Can't start from an index of less than 0."):
        await query_handler.batch_search_statements([braf_va_id], start=-1)
    with pytest.raises(
        ValueError, match="Can't limit results to less than a negative number."
    ):
        await query_handler.batch_search_statements([braf_va_id], limit=-1)

    # test default limit
    limited_query_handler = QueryHandler(normalizers=normalizers, default_page_limit=1)
    default_limited_response = await limited_query_handler.batch_search_statements(
        [braf_va_id]
    )
    assert len(default_limited_response.statement_ids) == 1
    assert default_limited_response.statement_ids[0] == full_response.statement_ids[0]

    # test overrideable
    less_limited_response = await limited_query_handler.batch_search_statements(
        [braf_va_id], limit=2
    )
    assert len(less_limited_response.statement_ids) == 2
    assert less_limited_response.statement_ids == full_response.statement_ids[:2]

    # test default limit and skip
    skipped_limited_response = await limited_query_handler.batch_search_statements(
        [braf_va_id], start=1
    )
    assert len(skipped_limited_response.statement_ids) == 1
    assert skipped_limited_response.statement_ids[0] == full_response.statement_ids[1]

    limited_query_handler.driver.close()
