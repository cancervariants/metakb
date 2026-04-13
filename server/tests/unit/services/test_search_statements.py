"""Test search statement methods"""

import re

import pytest

from metakb.repository.base import AbstractRepository
from metakb.services.search import (
    PaginationParamError,
    batch_search_statements,
    search_statements,
)


@pytest.mark.asyncio(scope="module")
async def test_search(repository, normalizers):
    pass  # TODO fill in some basics


@pytest.mark.asyncio(scope="module")
async def test_batch_search(repository, normalizers):
    pass  # TODO fill in some basics


@pytest.mark.asyncio(scope="module")
async def test_paginate_search(repository, normalizers):
    braf_va_id = "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"
    full_response = await search_statements(
        repository, normalizers, variation=braf_va_id
    )
    paged_response = await search_statements(
        repository, normalizers, variation=braf_va_id, start=1
    )
    # should be almost the same, just off by 1
    assert len(paged_response.statements) == len(full_response.statements) - 1
    assert paged_response.statements == full_response.statements[1:]

    # check that page limit > response doesn't affect response
    huge_page_response = await search_statements(
        repository, normalizers, variation=braf_va_id, limit=1000
    )
    assert len(huge_page_response.statements) == len(full_response.statements)
    assert huge_page_response.statements == full_response.statements

    # get last item
    last_response = await search_statements(
        repository,
        normalizers,
        variation=braf_va_id,
        start=len(full_response.statements) - 1,
    )
    assert len(last_response.statements) == 1
    assert last_response.statements[0] == full_response.statements[-1]

    # test limit
    min_response = await search_statements(
        repository, normalizers, variation=braf_va_id, limit=1
    )
    assert min_response.statements[0] == full_response.statements[0]

    # test limit and start
    other_min_response = await search_statements(
        repository, normalizers, variation=braf_va_id, start=1, limit=1
    )
    assert other_min_response.statements[0] == full_response.statements[1]

    # test limit of 0
    empty_response = await search_statements(
        repository, normalizers, variation=braf_va_id, limit=0
    )
    assert len(empty_response.statements) == 0

    # test raises exceptions
    with pytest.raises(
        PaginationParamError,
        match=re.escape("Invalid start value: -1. Must be nonnegative."),
    ):
        await search_statements(repository, normalizers, variation=braf_va_id, start=-1)
    with pytest.raises(
        PaginationParamError,
        match=re.escape("Invalid limit value: -1. Must be nonnegative."),
    ):
        await search_statements(repository, normalizers, variation=braf_va_id, limit=-1)


@pytest.mark.asyncio(scope="module")
async def test_paginate_batch_search(repository: AbstractRepository, normalizers):
    """Test pagination parameters."""
    braf_va_id = "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"
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
        PaginationParamError,
        match=re.escape("Invalid start value: -1. Must be nonnegative."),
    ):
        await batch_search_statements(repository, normalizers, [braf_va_id], start=-1)
    with pytest.raises(
        PaginationParamError,
        match=re.escape("Invalid limit value: -1. Must be nonnegative."),
    ):
        await batch_search_statements(repository, normalizers, [braf_va_id], limit=-1)
