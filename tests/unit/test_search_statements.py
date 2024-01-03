"""Test the MetaKB search_studies method"""
import pytest


def assert_general_search_studies(response):
    """Check that general search_studies queries return a valid response"""
    len_study_id_matches = len(response.study_ids)
    assert len_study_id_matches > 0
    len_studies = len(response.studies)
    assert len_studies > 0
    assert len_study_id_matches == len_studies


def assert_no_match(response):
    """No match assertions for queried concepts in search_studies."""
    assert response.studies == response.study_ids == []
    assert len(response.warnings) > 0


@pytest.mark.asyncio
async def test_civic_eid2997(query_handler, civic_eid2997_study, assertion_checks):
    """Test that search_studies method works correctly for CIVIC EID2997"""
    resp = await query_handler.search_studies(study_id=civic_eid2997_study["id"])
    assert resp.study_ids == [civic_eid2997_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid2997_study])
    assert resp.warnings == []


@pytest.mark.asyncio
async def test_moa(query_handler, moa_aid67_study, assertion_checks):
    """Test that search_studies method works correctly for MOA Assertion 67"""
    resp = await query_handler.search_studies(study_id=moa_aid67_study["id"])
    assert resp.study_ids == [moa_aid67_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [moa_aid67_study])
    assert resp.warnings == []


@pytest.mark.asyncio
async def test_general_search_studies(query_handler):
    """Test that queries do not return errors"""
    resp = await query_handler.search_studies(variation="BRAF V600E")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(variation="EGFR L858R")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(disease="cancer")
    assert_general_search_studies(resp)


@pytest.mark.asyncio
async def test_no_matches(query_handler):
    """Test invalid queries"""
    # invalid vrs variation prefix (digest is correct)
    resp = await query_handler.search_studies(
        variation="ga4gh:variation.TAARa2cxRHmOiij9UBwvW-noMDoOq2x9"
    )
    assert_no_match(resp)

    # invalid id
    resp = await query_handler.search_studies(
        disease="ncit:C292632425235321524352435623462"
    )
    assert_no_match(resp)

    # empty query
    resp = await query_handler.search_studies()
    assert_no_match(resp)
