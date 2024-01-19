"""Test CIViC Harvester class"""
import json
import os

import pytest
from metakb import APP_ROOT, PROJECT_ROOT
from metakb.harvesters import CIViCHarvester

TEST_DATA_PATH = PROJECT_ROOT / "tests" / "data" / "harvesters" / "civic"
TEST_CIVICPY_CACHE_PATH = list(sorted(TEST_DATA_PATH.glob("civicpy_cache_*.pkl")))[-1]


@pytest.fixture(scope="module")
def harvester():
    """Create test fixture for CIViCHarvester"""
    return CIViCHarvester(local_cache_path=TEST_CIVICPY_CACHE_PATH)


@pytest.fixture(scope="module")
def harvested_variants(harvester):
    """Create test fixture for harvested CIViC variants"""
    return harvester.harvest_variants()


@pytest.fixture(scope="module")
def harvested_molecular_profiles(harvester):
    """Create test fixture for harvested CIViC molecular profiles"""
    return harvester.harvest_molecular_profiles()


@pytest.fixture(scope="module")
def harvested_genes(harvester):
    """Create test fixture for harvested CIViC genes"""
    return harvester.harvest_genes()


@pytest.fixture(scope="module")
def harvested_evidence(harvester):
    """Create test fixture for harvested CIViC evidence"""
    return harvester.harvest_evidence()


@pytest.fixture(scope="module")
def harvested_assertions(harvester):
    """Create test fixture for harvested CIViC assertions"""
    return harvester.harvest_assertions()


@pytest.fixture(scope="module")
def civic_variant_12():
    """Create test fixture for CIViC Variant 12"""
    with open(TEST_DATA_PATH / "civic_variant_12.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def civic_molecular_profile_12():
    """Create test fixture for CIViC Molecular Profile 12"""
    with open(TEST_DATA_PATH / "civic_molecular_profile_12.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def civic_gene_5():
    """Create test fixture for CIViC Gene 5"""
    with open(TEST_DATA_PATH / "civic_gene_5.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def civic_eid_3017():
    """Create test fixture for CIViC EID 3017"""
    with open(TEST_DATA_PATH / "civic_eid_3017.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def civic_aid_7():
    """Create test fixture for CIViC AID 7"""
    with open(TEST_DATA_PATH / "civic_aid_7.json", "r") as f:
        return json.load(f)


def test_harvest(harvester):
    """Test that CIViC harvest method works correctly"""
    fn = "test_civic_harvester.json"
    assert harvester.harvest(filename=fn)
    file_path = APP_ROOT / "data" / "civic" / "harvester" / fn
    assert file_path.exists()
    os.remove(file_path)
    assert not file_path.exists()


def test_harvest_variants(harvested_variants, civic_variant_12):
    """Test that CIViC Variants are harvested correctly."""
    assert harvested_variants
    checked = False
    for v in harvested_variants:
        if v["id"] == 12:
            assert v == civic_variant_12
            checked = True
    assert checked, "CIViC Variant 12 not in harvested variants"


def test_harvest_molecular_profiles(
    harvested_molecular_profiles, civic_molecular_profile_12
):
    """Test that CIViC Molecular Profiles are harvested correctly."""
    assert harvested_molecular_profiles
    checked = False
    for mp in harvested_molecular_profiles:
        if mp["id"] == 12:
            assert mp == civic_molecular_profile_12
            checked = True
    assert checked, "CIViC Molecular Profile 12 not in harvested molecular profiles"


def test_civic_genes(harvested_genes, civic_gene_5):
    """Test that CIViC Genes are harvested correctly."""
    assert harvested_genes
    checked = False
    for g in harvested_genes:
        if g["id"] == 5:
            assert g == civic_gene_5
            checked = True
    assert checked, "CIViC Gene 5 not in harvested genes"


def test_civic_evidence(harvested_evidence, civic_eid_3017):
    """Test that CIViC Evidence are harvested correctly."""
    assert harvested_evidence
    checked = []
    for e in harvested_evidence:
        if e["id"] == 3017:
            assert e == civic_eid_3017
            checked.append(e["id"])
        elif e["id"] == 6178:
            assert e["assertion_ids"] == [12, 7]
            checked.append(e["id"])
    assert (
        len(checked) == 2
    ), f"Expected to check CIViC Evidence Items 3017 and 6178, but only checked {checked}"
    assert checked, "CIViC Evidence Item 3017 not in harvested evidence"


def test_civic_assertion(harvested_assertions, civic_aid_7):
    """Test that CIViC Assertions are harvested correctly."""
    assert harvested_assertions
    checked = False
    for a in harvested_assertions:
        if a["id"] == 7:
            assert a == civic_aid_7
            checked = True
    assert checked, "CIViC Assertion 7 not in harvested assertions"
