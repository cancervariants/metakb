"""Test the MetaKB search_studies method"""

import pytest

from metakb.query import QueryHandler
from metakb.schemas.api import SearchStudiesService
from metakb.schemas.app import SourceName


@pytest.fixture(scope="module")
def query_handler(normalizers):
    """Create query handler test fixture"""
    return QueryHandler(normalizers=normalizers)


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


def find_and_check_study(
    resp: SearchStudiesService,
    expected_study: dict,
    assertion_checks: callable,
    should_find_match: bool = True,
):
    """Check that expected study is or is not in response"""
    if should_find_match:
        assert expected_study["id"] in resp.study_ids
    else:
        assert expected_study["id"] not in resp.study_ids

    actual_study = None
    for study in resp.studies:
        if study.id == expected_study["id"]:
            actual_study = study
            break

    if should_find_match:
        assert actual_study, f"Did not find study ID {expected_study['id']} in studies"
        resp_studies = [actual_study.model_dump(exclude_none=True)]
        assertion_checks(resp_studies, [expected_study])
    else:
        assert actual_study is None


@pytest.mark.asyncio(scope="module")
async def test_civic_eid2997(query_handler, civic_eid2997_study, assertion_checks):
    """Test that search_studies method works correctly for CIViC EID2997"""
    resp = await query_handler.search_studies(study_id=civic_eid2997_study["id"])
    assert resp.study_ids == [civic_eid2997_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid2997_study])
    assert resp.warnings == []

    resp = await query_handler.search_studies(variation="EGFR L858R")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies(
        variation="ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"
    )
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    # genomic query
    resp = await query_handler.search_studies(variation="7-55259515-T-G")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)
    # At the moment, MOA cannot be queried via related genomic queries
    # only civic stores genomic members
    assert not [s_id for s_id in resp.study_ids if s_id.startswith(SourceName.MOA)]

    resp = await query_handler.search_studies(therapy="ncit:C66940")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies(gene="EGFR")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies(disease="nsclc")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    # We should not find CIViC EID2997 using these queries
    resp = await query_handler.search_studies(study_id="civic.eid:3017")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies(variation="BRAF V600E")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies(therapy="imatinib")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies(gene="BRAF")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies(disease="DOID:9253")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_civic816(query_handler, civic_eid816_study, assertion_checks):
    """Test that search_studies method works correctly for CIViC EID816"""
    resp = await query_handler.search_studies(study_id=civic_eid816_study["id"])
    assert resp.study_ids == [civic_eid816_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid816_study])
    assert resp.warnings == []

    # Try querying based on therapies in substitutes
    resp = await query_handler.search_studies(therapy="Cetuximab")
    find_and_check_study(resp, civic_eid816_study, assertion_checks)

    resp = await query_handler.search_studies(therapy="Panitumumab")
    find_and_check_study(resp, civic_eid816_study, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_civic9851(query_handler, civic_eid9851_study, assertion_checks):
    """Test that search_studies method works correctly for CIViC EID9851"""
    resp = await query_handler.search_studies(study_id=civic_eid9851_study["id"])
    assert resp.study_ids == [civic_eid9851_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid9851_study])
    assert resp.warnings == []

    # Try querying based on therapies in components
    resp = await query_handler.search_studies(therapy="Encorafenib")
    find_and_check_study(resp, civic_eid9851_study, assertion_checks)

    resp = await query_handler.search_studies(therapy="Cetuximab")
    find_and_check_study(resp, civic_eid9851_study, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_moa_66(query_handler, moa_aid66_study, assertion_checks):
    """Test that search_studies method works correctly for MOA Assertion 66"""
    resp = await query_handler.search_studies(study_id=moa_aid66_study["id"])
    assert resp.study_ids == [moa_aid66_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [moa_aid66_study])
    assert resp.warnings == []

    resp = await query_handler.search_studies(variation="ABL1 Thr315Ile")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies(
        variation="ga4gh:VA.D6NzpWXKqBnbcZZrXNSXj4tMUwROKbsQ"
    )
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies(therapy="rxcui:282388")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies(gene="ncbigene:25")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies(disease="CML")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    # We should not find MOA Assertion 67 using these queries
    resp = await query_handler.search_studies(study_id="moa.assertion:71")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies(variation="BRAF V600E")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies(therapy="Afatinib")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies(gene="ABL2")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies(disease="ncit:C2926")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_general_search_studies(query_handler):
    """Test that queries do not return errors"""
    resp = await query_handler.search_studies(variation="BRAF V600E")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(variation="EGFR L858R")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(disease="cancer")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(therapy="Cetuximab")
    assert_general_search_studies(resp)

    resp = await query_handler.search_studies(gene="VHL")
    assert_general_search_studies(resp)


@pytest.mark.asyncio(scope="module")
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

    # valid queries, but no matches with combination
    resp = await query_handler.search_studies(variation="BRAF V600E", gene="EGFR")
    assert_no_match(resp)
