"""Test PMKB transformation to common data model"""
import pytest
from metakb.transform.pmkb import PMKBTransform
from metakb import PROJECT_ROOT
import json


TRANSFORMED_FILE = f"{PROJECT_ROOT}/tests/data/transform/pmkb_cdm.json"


@pytest.fixture(scope='module')
def data():
    """Create PMKB transformation test fixture."""
    file_path = PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'pmkb_harvester.json'  # noqa: E501
    pmkb = PMKBTransform(file_path=file_path)
    pmkb.transform()
    pmkb._create_json(pmkb_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform')
    with open(TRANSFORMED_FILE, 'r') as f:
        data = json.load(f)
    return data


def test_pmkb_cdm(data,
                  pmkb_statement_113, pmkb_proposition,
                  pmkb_vod_adenocarcinoma, pmkb_vod_variant_217,
                  pmkb_vod_ctnnb1, pmkb_vod_therapeutic_procedure, pmkb_method,
                  pmkb_docs, check_statement, check_proposition,
                  check_variation_descriptor, check_descriptor, check_document,
                  check_method, check_transformed_cdm):
    """Check PMKB transformation output."""
    check_transformed_cdm(data, [pmkb_statement_113], [pmkb_proposition],
                          [pmkb_vod_variant_217], [pmkb_vod_ctnnb1],
                          [pmkb_vod_adenocarcinoma],
                          [pmkb_vod_therapeutic_procedure], [pmkb_method],
                          pmkb_docs, check_statement,
                          check_proposition, check_variation_descriptor,
                          check_descriptor, check_document,
                          check_method, TRANSFORMED_FILE)
