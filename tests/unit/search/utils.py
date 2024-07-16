from metakb.schemas.api import BatchSearchStudiesService, SearchStudiesService


def assert_no_match(response):
    """No match assertions for queried concepts in search_studies."""
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
