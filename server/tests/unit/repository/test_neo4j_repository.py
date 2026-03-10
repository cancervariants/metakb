"""Test Neo4j repository implementation."""

import json
from pathlib import Path

import pytest
from ga4gh.core.models import Coding, MappableConcept, code
from ga4gh.va_spec.base import Statement

from metakb.repository.neo4j_repository import Neo4jRepository, get_driver


@pytest.fixture(scope="module")
def repository():
    """Provide a new repository session. Wipe all existing DB data and re-initialize."""
    driver = get_driver()
    session = driver.session()

    repository = Neo4jRepository(session)
    repository.teardown_db()
    repository.initialize()
    yield repository

    session.close()
    driver.close()


@pytest.fixture
def cdm(test_data_dir: Path):
    with (test_data_dir / "repository" / "cdm.json").open() as f:
        data = json.load(f)
        data["statements"] = [Statement(**s) for s in data["statements"]]
    return data


@pytest.mark.ci_only
def test_basic_statement_roundtrip(repository: Neo4jRepository, cdm: dict):
    """Test roundtripping of a ... TODO

    * subject variant has a DefiningAlleleConstraint
    """
    statement: Statement = cdm["statements"][0]
    for line in statement.hasEvidenceLines:
        for item in line.hasEvidenceItems:
            repository.load_statement(item)
    repository.load_statement(statement)

    statement_id = "metakb.assertion:WRdtjMzgdMFsPX2i4MgN-BTFz_C3ITZQ"
    catvar_id = "metakb.cv:PSQ.VA.sMA9h8fzDi0RvweMlxtD0_Oi8B-JZ1V-"
    disease_id = "metakb.disease:ncit_C2926"
    gene_id = "metakb.gene:hgnc_3236"
    therapy_id = "metakb.therapy:rxcui_337525"
    allele_id = "ga4gh:VA.sMA9h8fzDi0RvweMlxtD0_Oi8B-JZ1V-"

    eid_result = repository.search_statements(statement_ids=[statement_id])
    assert len(eid_result) == 1
    assert eid_result[0].id == statement_id
    assert eid_result[0].proposition.subjectVariant.id == catvar_id
    assert (
        eid_result[0].proposition.objectTherapeutic.root.id
        == "metakb.therapy:rxcui_337525"
    )
    assert eid_result[0].proposition.conditionQualifier.root.id == disease_id
    assert eid_result[0].proposition.geneContextQualifier.id == gene_id

    therapy_result = repository.search_statements(therapy_ids=[therapy_id])
    assert therapy_result == eid_result

    gene_result = repository.search_statements(gene_ids=[gene_id])
    assert gene_result == eid_result

    disease_result = repository.search_statements(disease_ids=[disease_id])
    assert disease_result == eid_result

    var_result = repository.search_statements(variation_ids=[allele_id])
    assert var_result == eid_result

    all_combo_result = repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
        variation_ids=[allele_id],
        statement_ids=[statement_id],
    )
    assert all_combo_result == eid_result

    entity_combo_result = repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
        variation_ids=[allele_id],
    )
    assert entity_combo_result == eid_result

    partial_combo_result = repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
    )
    assert partial_combo_result == eid_result


@pytest.mark.ci_only
def test_feature_context_statement_roundtrip(repository: Neo4jRepository, cdm: dict):
    """Test roundtripping of a statement that uses a gene mutation subject: MOA assertion 120

    * prognostic proposition
    * subject variant has a FeatureContextConstraint ("ARID1A mutation")
    """
    statement: Statement = cdm["statements"][1]
    for line in statement.hasEvidenceLines:
        for item in line.hasEvidenceItems:
            repository.load_statement(item)
    repository.load_statement(statement)

    assertion_id = "metakb.assertion:zk-WDclkxtcOEnxIH6VClRKRqbPXEURy"
    catvar_id = "metakb.cv:FC.hgnc_11110"
    gene_id = "metakb.gene:hgnc_11110"
    disease_id = "metakb.disease:ncit_C8294"

    eid_result = repository.search_statements(statement_ids=[assertion_id])
    assert len(eid_result) == 1
    assert eid_result[0].id == assertion_id
    assert eid_result[0].proposition.subjectVariant.id == catvar_id
    assert eid_result[0].proposition.objectCondition.root.id == disease_id
    assert eid_result[0].proposition.geneContextQualifier.id == gene_id

    gene_result = repository.search_statements(gene_ids=[gene_id])
    assert gene_result == eid_result

    disease_result = repository.search_statements(disease_ids=[disease_id])
    assert disease_result == eid_result

    all_combo_result = repository.search_statements(
        gene_ids=[gene_id],
        disease_ids=[disease_id],
        statement_ids=[assertion_id],
    )
    assert all_combo_result == eid_result

    entity_combo_result = repository.search_statements(
        gene_ids=[gene_id],
        disease_ids=[disease_id],
    )
    assert entity_combo_result == eid_result


@pytest.mark.ci_only
def test_get_stats(repository: Neo4jRepository):
    # If we had a robust test dataset, we could meaningfully check for specific expected counts
    # for now this just checks that they respond
    stats = repository.get_stats()
    for k, v in stats.model_dump().items():
        assert v, f"Count of {k} is {v}"


@pytest.mark.ci_only
def test_get_all_assertion_ids(repository: Neo4jRepository):
    all_ids = repository.get_all_assertion_ids()
    assert set(all_ids) == {
        "metakb.assertion:WRdtjMzgdMFsPX2i4MgN-BTFz_C3ITZQ",
        "metakb.assertion:zk-WDclkxtcOEnxIH6VClRKRqbPXEURy",
    }


@pytest.mark.ci_only
def test_update_assertion(repository: Neo4jRepository, cdm: dict):
    assertion_id = "metakb.assertion:WRdtjMzgdMFsPX2i4MgN-BTFz_C3ITZQ"
    new_strength = MappableConcept(
        primaryCoding=Coding(
            code=code("fake_code"), system="AMP/ASCO/CAP (AAC) Guidelines, 2017"
        )
    )
    repository.update_assertion_strength(assertion_id, new_strength)

    new_assertion_copy = repository.search_statements(statement_ids=[assertion_id])[0]
    assert new_assertion_copy.strength.model_dump(
        exclude_none=True
    ) == new_strength.model_dump(exclude_none=True)

    old_strength = cdm["statements"][0].strength
    repository.update_assertion_strength(assertion_id, old_strength)

    new_assertion_copy = repository.search_statements(statement_ids=[assertion_id])[0]
    assert new_assertion_copy.strength.model_dump(
        exclude_none=True
    ) == old_strength.model_dump(exclude_none=True)
