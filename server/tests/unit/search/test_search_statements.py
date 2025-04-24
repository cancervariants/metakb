"""Test search statement methods"""

import pytest
from tests.conftest import get_mappings_normalizer_id

from metakb.query import QueryHandler

from .utils import assert_no_match, find_and_check_stmt


def assert_general_search_stmts(response):
    """Check that general search_statements queries return a valid response"""
    len_stmt_id_matches = len(response.statement_ids)
    assert len_stmt_id_matches > 0
    len_stmts = len(response.statements)
    assert len_stmts > 0
    assert len_stmt_id_matches == len_stmts


@pytest.mark.asyncio(scope="module")
async def test_civic_eid2997(query_handler, civic_eid2997_study_stmt, assertion_checks):
    """Test that search_statements method works correctly for CIViC EID2997"""
    resp = await query_handler.search_statements(
        statement_id=civic_eid2997_study_stmt["id"]
    )
    assert resp.statement_ids == [civic_eid2997_study_stmt["id"]]
    resp_stmts = [s.model_dump(exclude_none=True) for s in resp.statements]
    assertion_checks(resp_stmts, [civic_eid2997_study_stmt])
    assert resp.warnings == []

    resp = await query_handler.search_statements(variation="EGFR L858R")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(
        variation="ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"
    )
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    # genomic query
    resp = await query_handler.search_statements(variation="7-55259515-T-G")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(therapy="ncit:C66940")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(gene="EGFR")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(disease="nsclc")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks)

    # We should not find CIViC EID2997 using these queries
    resp = await query_handler.search_statements(statement_id="civic.eid:3017")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(variation="BRAF V600E")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(therapy="imatinib")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(gene="BRAF")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(disease="DOID:9253")
    find_and_check_stmt(resp, civic_eid2997_study_stmt, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_civic816(query_handler, civic_eid816_study_stmt, assertion_checks):
    """Test that search_statements method works correctly for CIViC EID816"""
    resp = await query_handler.search_statements(
        statement_id=civic_eid816_study_stmt["id"]
    )
    assert resp.statement_ids == [civic_eid816_study_stmt["id"]]
    resp_stmts = [s.model_dump(exclude_none=True) for s in resp.statements]
    assertion_checks(resp_stmts, [civic_eid816_study_stmt])
    assert resp.warnings == []

    # Try querying based on therapies in substitutes
    resp = await query_handler.search_statements(therapy="Cetuximab")
    find_and_check_stmt(resp, civic_eid816_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(therapy="Panitumumab")
    find_and_check_stmt(resp, civic_eid816_study_stmt, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_civic9851(query_handler, civic_eid9851_study_stmt, assertion_checks):
    """Test that search_statements method works correctly for CIViC EID9851"""
    resp = await query_handler.search_statements(
        statement_id=civic_eid9851_study_stmt["id"]
    )
    assert resp.statement_ids == [civic_eid9851_study_stmt["id"]]
    resp_stmts = [s.model_dump(exclude_none=True) for s in resp.statements]
    assertion_checks(resp_stmts, [civic_eid9851_study_stmt])
    assert resp.warnings == []

    # Try querying based on therapies in components
    resp = await query_handler.search_statements(therapy="Encorafenib")
    find_and_check_stmt(resp, civic_eid9851_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(therapy="Cetuximab")
    find_and_check_stmt(resp, civic_eid9851_study_stmt, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_civic_assertion(query_handler, civic_aid6_statement, assertion_checks):
    """Test that search_statements method works correctly for civic assertions"""
    resp = await query_handler.search_statements(
        statement_id=civic_aid6_statement["id"]
    )
    assert resp.statement_ids == [civic_aid6_statement["id"]]
    resp_stmts = [s.model_dump(exclude_none=True) for s in resp.statements]
    assert len(resp_stmts) == 1
    # Test fixture only has one evidence line, but actual has 6
    actual_civic_aid6 = resp_stmts[0]
    assert len(actual_civic_aid6["hasEvidenceLines"]) == 6
    expected_evidence_lines = []
    expected_evidence_item_ids = {
        "civic.eid:982",
        "civic.eid:2997",
        "civic.eid:879",
        "civic.eid:883",
        "civic.eid:968",
        "civic.eid:2629",
    }
    for el in actual_civic_aid6["hasEvidenceLines"]:
        for ev in el["hasEvidenceItems"]:
            assert ev["id"] in expected_evidence_item_ids

            if ev["id"] == "civic.eid:2997":
                expected_evidence_lines.append(el)

    actual_civic_aid6["hasEvidenceLines"] = expected_evidence_lines
    assertion_checks(resp_stmts, [civic_aid6_statement])
    assert resp.warnings == []


@pytest.mark.asyncio(scope="module")
async def test_moa_66(query_handler, moa_aid66_study_stmt, assertion_checks):
    """Test that search_statements method works correctly for MOA Assertion 66"""
    resp = await query_handler.search_statements(
        statement_id=moa_aid66_study_stmt["id"]
    )
    assert resp.statement_ids == [moa_aid66_study_stmt["id"]]
    resp_stmts = [s.model_dump(exclude_none=True) for s in resp.statements]
    assertion_checks(resp_stmts, [moa_aid66_study_stmt])
    assert resp.warnings == []

    resp = await query_handler.search_statements(variation="ABL1 Thr315Ile")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(
        variation="ga4gh:VA.D6NzpWXKqBnbcZZrXNSXj4tMUwROKbsQ"
    )
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(therapy="rxcui:282388")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(gene="ncbigene:25")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks)

    resp = await query_handler.search_statements(disease="CML")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks)

    # We should not find MOA Assertion 67 using these queries
    resp = await query_handler.search_statements(statement_id="moa.assertion:71")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(variation="BRAF V600E")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(therapy="Afatinib")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(gene="ABL2")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks, False)

    resp = await query_handler.search_statements(disease="ncit:C2926")
    find_and_check_stmt(resp, moa_aid66_study_stmt, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_general_search_statements(query_handler):
    """Test that queries do not return errors"""
    resp = await query_handler.search_statements(variation="BRAF V600E")
    assert_general_search_stmts(resp)

    resp = await query_handler.search_statements(variation="EGFR L858R")
    assert_general_search_stmts(resp)

    resp = await query_handler.search_statements(disease="cancer")
    assert_general_search_stmts(resp)

    # Case: Handling therapy for single therapy / combination / substitutes
    resp = await query_handler.search_statements(therapy="Cetuximab")
    assert_general_search_stmts(resp)
    expected_therapy_id = "rxcui:318341"
    for statement in resp.statements:
        tp = statement.proposition.objectTherapeutic.root

        if hasattr(tp, "conceptType"):
            assert get_mappings_normalizer_id(tp.mappings) == expected_therapy_id
        else:
            found_expected = False
            for therapeutic in tp.therapies:
                if (
                    get_mappings_normalizer_id(therapeutic.mappings)
                    == expected_therapy_id
                ):
                    found_expected = True
                    break
            assert found_expected

    resp = await query_handler.search_statements(gene="VHL")
    assert_general_search_stmts(resp)

    # Case: multiple concepts provided
    expected_variation_id = "ga4gh:VA._8jTS8nAvWwPZGOadQuD1o-tbbTQ5g3H"
    expected_disease_id = "ncit:C2926"
    expected_therapy_id = "ncit:C104732"
    resp = await query_handler.search_statements(
        variation=expected_variation_id,
        disease=expected_disease_id,
        therapy=expected_therapy_id,  # Single Therapy
    )
    assert_general_search_stmts(resp)

    for statement in resp.statements:
        assert (
            statement.proposition.subjectVariant.constraints[0].root.allele.id
            == expected_variation_id
        )
        assert (
            get_mappings_normalizer_id(
                statement.proposition.objectTherapeutic.root.mappings
            )
            == expected_therapy_id
        )
        assert (
            get_mappings_normalizer_id(
                statement.proposition.conditionQualifier.root.mappings
            )
            == expected_disease_id
        )


@pytest.mark.asyncio(scope="module")
async def test_no_matches(query_handler):
    """Test invalid queries"""
    # invalid vrs variation prefix (digest is correct)
    resp = await query_handler.search_statements(
        variation="ga4gh:variation.TAARa2cxRHmOiij9UBwvW-noMDoOq2x9"
    )
    assert_no_match(resp)

    # invalid id
    resp = await query_handler.search_statements(
        disease="ncit:C292632425235321524352435623462"
    )
    assert_no_match(resp)

    # empty query
    resp = await query_handler.search_statements()
    assert_no_match(resp)

    # valid queries, but no matches with combination
    resp = await query_handler.search_statements(variation="BRAF V600E", gene="EGFR")
    assert_no_match(resp)


@pytest.mark.asyncio(scope="module")
async def test_paginate(query_handler: QueryHandler, normalizers):
    """Test pagination parameters."""
    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    full_response = await query_handler.search_statements(variation=braf_va_id)
    paged_response = await query_handler.search_statements(
        variation=braf_va_id, start=1
    )
    # should be almost the same, just off by 1
    assert len(paged_response.statement_ids) == len(full_response.statement_ids) - 1
    assert paged_response.statement_ids == full_response.statement_ids[1:]

    # check that page limit > response doesn't affect response
    huge_page_response = await query_handler.search_statements(
        variation=braf_va_id, limit=1000
    )
    assert len(huge_page_response.statement_ids) == len(full_response.statement_ids)
    assert huge_page_response.statement_ids == full_response.statement_ids

    # get last item
    last_response = await query_handler.search_statements(
        variation=braf_va_id, start=len(full_response.statement_ids) - 1
    )
    assert len(last_response.statement_ids) == 1
    assert last_response.statement_ids[0] == full_response.statement_ids[-1]

    # test limit
    min_response = await query_handler.search_statements(variation=braf_va_id, limit=1)
    assert min_response.statement_ids[0] == full_response.statement_ids[0]

    # test limit and start
    other_min_response = await query_handler.search_statements(
        variation=braf_va_id, start=1, limit=1
    )
    assert other_min_response.statement_ids[0] == full_response.statement_ids[1]

    # test limit of 0
    empty_response = await query_handler.search_statements(
        variation=braf_va_id, limit=0
    )
    assert len(empty_response.statement_ids) == 0

    # test raises exceptions
    with pytest.raises(ValueError, match="Can't start from an index of less than 0."):
        await query_handler.search_statements(variation=braf_va_id, start=-1)
    with pytest.raises(
        ValueError, match="Can't limit results to less than a negative number."
    ):
        await query_handler.search_statements(variation=braf_va_id, limit=-1)

    # test default limit
    limited_query_handler = QueryHandler(normalizers=normalizers, default_page_limit=1)
    default_limited_response = await limited_query_handler.search_statements(
        variation=braf_va_id
    )
    assert len(default_limited_response.statement_ids) == 1
    assert default_limited_response.statement_ids[0] == full_response.statement_ids[0]

    # test overrideable
    less_limited_response = await limited_query_handler.search_statements(
        variation=braf_va_id, limit=2
    )
    assert len(less_limited_response.statement_ids) == 2
    assert less_limited_response.statement_ids == full_response.statement_ids[:2]

    # test default limit and skip
    skipped_limited_response = await limited_query_handler.search_statements(
        variation=braf_va_id, start=1
    )
    assert len(skipped_limited_response.statement_ids) == 1
    assert skipped_limited_response.statement_ids[0] == full_response.statement_ids[1]

    limited_query_handler.driver.close()
