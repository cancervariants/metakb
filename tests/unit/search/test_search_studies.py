"""Test search study methods"""

import pytest
from ga4gh.core.entity_models import Extension

from metakb.query import QueryHandler

from .utils import assert_no_match, find_and_check_study


def _get_normalizer_id(extensions: list[Extension]) -> str | None:
    """Get normalized ID from list of extensions

    :param extensions: List of extensions
    :return: Normalized concept ID if found in extensions
    """
    normalizer_id = None
    for ext in extensions:
        if ext.name == "vicc_normalizer_data":
            normalizer_id = ext.value["id"]
            break
    return normalizer_id


def assert_general_search_studies(response):
    """Check that general search_studies queries return a valid response"""
    len_study_id_matches = len(response.study_ids)
    assert len_study_id_matches > 0
    len_studies = len(response.studies)
    assert len_studies > 0
    assert len_study_id_matches == len_studies


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

    # Case: Handling therapy for single therapeutic agent / combination / substitutes
    resp = await query_handler.search_studies(therapy="Cetuximab")
    assert_general_search_studies(resp)
    expected_therapy_id = "rxcui:318341"
    for study in resp.studies:
        tp = study.objectTherapeutic.root
        if tp.type == "TherapeuticAgent":
            assert _get_normalizer_id(tp.extensions) == expected_therapy_id
        else:
            therapeutics = (
                tp.components if tp.type == "CombinationTherapy" else tp.substitutes
            )

            found_expected = False
            for therapeutic in therapeutics:
                if _get_normalizer_id(therapeutic.extensions) == expected_therapy_id:
                    found_expected = True
                    break
            assert found_expected

    resp = await query_handler.search_studies(gene="VHL")
    assert_general_search_studies(resp)

    # Case: multiple concepts provided
    expected_variation_id = "ga4gh:VA._8jTS8nAvWwPZGOadQuD1o-tbbTQ5g3H"
    expected_disease_id = "ncit:C2926"
    expected_therapy_id = "ncit:C104732"
    resp = await query_handler.search_studies(
        variation=expected_variation_id,
        disease=expected_disease_id,
        therapy=expected_therapy_id,  # Single Therapeutic Agent
    )
    assert_general_search_studies(resp)

    for study in resp.studies:
        assert (
            study.subjectVariant.constraints[0].root.definingContext.root.id
            == expected_variation_id
        )
        assert (
            _get_normalizer_id(study.objectTherapeutic.root.extensions)
            == expected_therapy_id
        )
        assert (
            _get_normalizer_id(study.conditionQualifier.root.extensions)
            == expected_disease_id
        )


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


@pytest.mark.asyncio(scope="module")
async def test_paginate(query_handler: QueryHandler, normalizers):
    """Test pagination parameters."""
    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    full_response = await query_handler.search_studies(variation=braf_va_id)
    paged_response = await query_handler.search_studies(variation=braf_va_id, start=1)
    # should be almost the same, just off by 1
    assert len(paged_response.study_ids) == len(full_response.study_ids) - 1
    assert paged_response.study_ids == full_response.study_ids[1:]

    # check that page limit > response doesn't affect response
    huge_page_response = await query_handler.search_studies(
        variation=braf_va_id, limit=1000
    )
    assert len(huge_page_response.study_ids) == len(full_response.study_ids)
    assert huge_page_response.study_ids == full_response.study_ids

    # get last item
    last_response = await query_handler.search_studies(
        variation=braf_va_id, start=len(full_response.study_ids) - 1
    )
    assert len(last_response.study_ids) == 1
    assert last_response.study_ids[0] == full_response.study_ids[-1]

    # test limit
    min_response = await query_handler.search_studies(variation=braf_va_id, limit=1)
    assert min_response.study_ids[0] == full_response.study_ids[0]

    # test limit and start
    other_min_response = await query_handler.search_studies(
        variation=braf_va_id, start=1, limit=1
    )
    assert other_min_response.study_ids[0] == full_response.study_ids[1]

    # test limit of 0
    empty_response = await query_handler.search_studies(variation=braf_va_id, limit=0)
    assert len(empty_response.study_ids) == 0

    # test raises exceptions
    with pytest.raises(ValueError, match="Can't start from an index of less than 0."):
        await query_handler.search_studies(variation=braf_va_id, start=-1)
    with pytest.raises(
        ValueError, match="Can't limit results to less than a negative number."
    ):
        await query_handler.search_studies(variation=braf_va_id, limit=-1)

    # test default limit
    limited_query_handler = QueryHandler(normalizers=normalizers, default_page_limit=1)
    default_limited_response = await limited_query_handler.search_studies(
        variation=braf_va_id
    )
    assert len(default_limited_response.study_ids) == 1
    assert default_limited_response.study_ids[0] == full_response.study_ids[0]

    # test overrideable
    less_limited_response = await limited_query_handler.search_studies(
        variation=braf_va_id, limit=2
    )
    assert len(less_limited_response.study_ids) == 2
    assert less_limited_response.study_ids == full_response.study_ids[:2]

    # test default limit and skip
    skipped_limited_response = await limited_query_handler.search_studies(
        variation=braf_va_id, start=1
    )
    assert len(skipped_limited_response.study_ids) == 1
    assert skipped_limited_response.study_ids[0] == full_response.study_ids[1]

    limited_query_handler.driver.close()
