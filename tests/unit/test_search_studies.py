"""Test search study methods"""
import pytest
from ga4gh.core._internal.models import Extension

from metakb.query import QueryHandler
from metakb.schemas.api import (
    BatchSearchStudiesService,
    NormalizedQuery,
    SearchStudiesService,
)


@pytest.fixture(scope="module")
def query_handler(normalizers):
    """Create query handler test fixture"""
    qh = QueryHandler(normalizers=normalizers)
    yield qh
    qh.driver.close()


def _get_normalizer_id(extensions: list[Extension]) -> str | None:
    """Get normalized ID from list of extensions

    :param extensions: List of extensions
    :return: Normalized concept ID if found in extensions
    """
    normalizer_id = None
    for ext in extensions:
        if ext.name.endswith("_normalizer_id"):
            normalizer_id = ext.value
            break
    return normalizer_id


def assert_general_search_studies_intersect(response):
    """Check that general search_studies_intersect queries return a valid response"""
    len_study_id_matches = len(response.study_ids)
    assert len_study_id_matches > 0
    len_studies = len(response.studies)
    assert len_studies > 0
    assert len_study_id_matches == len_studies


def assert_no_match(response):
    """No match assertions for queried concepts in search_studies_intersect."""
    assert response.studies == response.study_ids == []
    assert len(response.warnings) > 0


def find_and_check_study(
    resp: SearchStudiesService | BatchSearchStudiesService,
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
    """Test that search_studies_intersect method works correctly for CIViC EID2997"""
    resp = await query_handler.search_studies_intersect(
        study_id=civic_eid2997_study["id"]
    )
    assert resp.study_ids == [civic_eid2997_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid2997_study])
    assert resp.warnings == []

    resp = await query_handler.search_studies_intersect(variation="EGFR L858R")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(
        variation="ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"
    )
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    # genomic query
    resp = await query_handler.search_studies_intersect(variation="7-55259515-T-G")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(therapy="ncit:C66940")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(gene="EGFR")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(disease="nsclc")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks)

    # We should not find CIViC EID2997 using these queries
    resp = await query_handler.search_studies_intersect(study_id="civic.eid:3017")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(variation="BRAF V600E")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(therapy="imatinib")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(gene="BRAF")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(disease="DOID:9253")
    find_and_check_study(resp, civic_eid2997_study, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_civic816(query_handler, civic_eid816_study, assertion_checks):
    """Test that search_studies_intersect method works correctly for CIViC EID816"""
    resp = await query_handler.search_studies_intersect(
        study_id=civic_eid816_study["id"]
    )
    assert resp.study_ids == [civic_eid816_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid816_study])
    assert resp.warnings == []

    # Try querying based on therapies in substitutes
    resp = await query_handler.search_studies_intersect(therapy="Cetuximab")
    find_and_check_study(resp, civic_eid816_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(therapy="Panitumumab")
    find_and_check_study(resp, civic_eid816_study, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_civic9851(query_handler, civic_eid9851_study, assertion_checks):
    """Test that search_studies_intersect method works correctly for CIViC EID9851"""
    resp = await query_handler.search_studies_intersect(
        study_id=civic_eid9851_study["id"]
    )
    assert resp.study_ids == [civic_eid9851_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [civic_eid9851_study])
    assert resp.warnings == []

    # Try querying based on therapies in components
    resp = await query_handler.search_studies_intersect(therapy="Encorafenib")
    find_and_check_study(resp, civic_eid9851_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(therapy="Cetuximab")
    find_and_check_study(resp, civic_eid9851_study, assertion_checks)


@pytest.mark.asyncio(scope="module")
async def test_moa_66(query_handler, moa_aid66_study, assertion_checks):
    """Test that search_studies_intersect method works correctly for MOA Assertion 66"""
    resp = await query_handler.search_studies_intersect(study_id=moa_aid66_study["id"])
    assert resp.study_ids == [moa_aid66_study["id"]]
    resp_studies = [s.model_dump(exclude_none=True) for s in resp.studies]
    assertion_checks(resp_studies, [moa_aid66_study])
    assert resp.warnings == []

    resp = await query_handler.search_studies_intersect(variation="ABL1 Thr315Ile")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(
        variation="ga4gh:VA.D6NzpWXKqBnbcZZrXNSXj4tMUwROKbsQ"
    )
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(therapy="rxcui:282388")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(gene="ncbigene:25")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    resp = await query_handler.search_studies_intersect(disease="CML")
    find_and_check_study(resp, moa_aid66_study, assertion_checks)

    # We should not find MOA Assertion 67 using these queries
    resp = await query_handler.search_studies_intersect(study_id="moa.assertion:71")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(variation="BRAF V600E")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(therapy="Afatinib")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(gene="ABL2")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)

    resp = await query_handler.search_studies_intersect(disease="ncit:C2926")
    find_and_check_study(resp, moa_aid66_study, assertion_checks, False)


@pytest.mark.asyncio(scope="module")
async def test_general_search_studies(query_handler):
    """Test that queries do not return errors"""
    resp = await query_handler.search_studies_intersect(variation="BRAF V600E")
    assert_general_search_studies_intersect(resp)

    resp = await query_handler.search_studies_intersect(variation="EGFR L858R")
    assert_general_search_studies_intersect(resp)

    resp = await query_handler.search_studies_intersect(disease="cancer")
    assert_general_search_studies_intersect(resp)

    # Case: Handling therapy for single therapeutic agent / combination / substitutes
    resp = await query_handler.search_studies_intersect(therapy="Cetuximab")
    assert_general_search_studies_intersect(resp)
    expected_therapy_id = "rxcui:318341"
    for study in resp.studies:
        tp = study.therapeutic.root
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

    resp = await query_handler.search_studies_intersect(gene="VHL")
    assert_general_search_studies_intersect(resp)

    # Case: multiple concepts provided
    expected_variation_id = "ga4gh:VA._8jTS8nAvWwPZGOadQuD1o-tbbTQ5g3H"
    expected_disease_id = "ncit:C2926"
    expected_therapy_id = "ncit:C104732"
    resp = await query_handler.search_studies_intersect(
        variation=expected_variation_id,
        disease=expected_disease_id,
        therapy=expected_therapy_id,  # Single Therapeutic Agent
    )
    assert_general_search_studies_intersect(resp)

    for study in resp.studies:
        assert study.variant.root.definingContext.id == expected_variation_id
        assert (
            _get_normalizer_id(study.therapeutic.root.extensions) == expected_therapy_id
        )
        assert (
            _get_normalizer_id(study.tumorType.root.extensions) == expected_disease_id
        )


@pytest.mark.asyncio(scope="module")
async def test_no_matches(query_handler):
    """Test invalid queries"""
    # invalid vrs variation prefix (digest is correct)
    resp = await query_handler.search_studies_intersect(
        variation="ga4gh:variation.TAARa2cxRHmOiij9UBwvW-noMDoOq2x9"
    )
    assert_no_match(resp)

    # invalid id
    resp = await query_handler.search_studies_intersect(
        disease="ncit:C292632425235321524352435623462"
    )
    assert_no_match(resp)

    # empty query
    resp = await query_handler.search_studies_intersect()
    assert_no_match(resp)

    # valid queries, but no matches with combination
    resp = await query_handler.search_studies_intersect(
        variation="BRAF V600E", gene="EGFR"
    )
    assert_no_match(resp)


@pytest.mark.asyncio(scope="module")
async def test_batch_search(
    query_handler: QueryHandler,
    assertion_checks,
    civic_eid2997_study,
    civic_eid816_study,
):
    """Test batch search studies method."""
    assert_no_match(await query_handler.batch_search_studies([]))
    assert_no_match(await query_handler.batch_search_studies(["gibberish variant"]))

    braf_va_id = "ga4gh:VA.Otc5ovrw906Ack087o1fhegB4jDRqCAe"
    braf_response = await query_handler.batch_search_studies([braf_va_id])
    assert braf_response.query.variations == [
        NormalizedQuery(
            term=braf_va_id,
            normalized_id=braf_va_id,
        )
    ]
    find_and_check_study(braf_response, civic_eid816_study, assertion_checks)

    redundant_braf_response = await query_handler.batch_search_studies(
        [braf_va_id, "NC_000007.13:g.140453136A>T"]
    )
    assert redundant_braf_response.query.variations == [
        NormalizedQuery(
            term=braf_va_id,
            normalized_id=braf_va_id,
        ),
        NormalizedQuery(
            term="NC_000007.13:g.140453136A>T",
            normalized_id=braf_va_id,
        ),
    ]
    find_and_check_study(redundant_braf_response, civic_eid816_study, assertion_checks)
    assert len(braf_response.study_ids) == len(redundant_braf_response.study_ids)

    braf_egfr_response = await query_handler.batch_search_studies(
        [braf_va_id, "EGFR L858R"]
    )
    find_and_check_study(braf_egfr_response, civic_eid816_study, assertion_checks)
    find_and_check_study(braf_egfr_response, civic_eid2997_study, assertion_checks)
    assert len(braf_egfr_response.study_ids) > len(braf_response.study_ids)
