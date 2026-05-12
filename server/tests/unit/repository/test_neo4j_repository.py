"""Test Neo4j repository implementation."""

import json
from pathlib import Path

import pytest
import pytest_asyncio
from ga4gh.va_spec.base import Statement

from metakb.repository.neo4j_repository import Neo4jRepository, get_driver


@pytest_asyncio.fixture(scope="module")
async def repository():
    """Provide a new repository session. Wipe all existing DB data and re-initialize."""
    driver = get_driver()
    session = driver.session()

    repository = Neo4jRepository(session)
    await repository.teardown_db()
    await repository.initialize()

    yield repository

    await session.close()
    await driver.close()


@pytest.fixture
def assertions(test_data_dir: Path):
    with (test_data_dir / "repository" / "assertions.json").open() as f:
        data = json.load(f)
        return {k: Statement(**v) for k, v in data.items()}


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_add_additional_assertion(repository: Neo4jRepository, assertions: dict):
    """Test adding a civic-based assertion, then a MOA-based assertion for the same proposition"""
    assertion = assertions["metakb.assertion:UYyEPTPQPtrMEQjTbat9Ka396w5YKrCi_civic"]
    await repository.load_assertion(assertion)

    assertion_id = "metakb.assertion:UYyEPTPQPtrMEQjTbat9Ka396w5YKrCi"
    catvar_id = "metakb.cv:PSQ.VA.pfWn9x9oFBRzGda1xXcOrE-BrX0R__N8"
    disease_id = "metakb.disease:ncit_C3224"
    gene_id = "metakb.gene:hgnc_1097"
    therapy_id = "metakb.therapy:rxcui_1425098"

    search_result = await repository.search_statements(statement_ids=[assertion_id])
    assert len(search_result) == 1
    assert search_result[0].id == assertion_id
    assert search_result[0].proposition.subjectVariant.id == catvar_id
    assert search_result[0].proposition.objectTherapeutic.root.id == therapy_id
    assert search_result[0].proposition.conditionQualifier.root.id == disease_id
    assert search_result[0].proposition.geneContextQualifier.id == gene_id
    assert [
        ext.value["primaryCoding"]["code"]
        for ext in search_result[0].extensions
        if ext.name == "metakb_star_rating"
    ] == ["1_star"]
    assert search_result[0].direction == "supports"
    assert search_result[0].strength.id == "vicc:e000005"
    assert len(search_result[0].hasEvidenceLines) == 1
    assert len(search_result[0].hasEvidenceLines[0].hasEvidenceItems) == 1
    assert (
        search_result[0].hasEvidenceLines[0].hasEvidenceItems[0].id == "civic.eid:2506"
    )

    # now load a MOA item for the same assertion
    assertion = assertions["metakb.assertion:UYyEPTPQPtrMEQjTbat9Ka396w5YKrCi_moa"]
    await repository.load_assertion(assertion)

    # check that aggregate values update
    search_result = await repository.search_statements(statement_ids=[assertion_id])
    assert len(search_result) == 1
    assert search_result[0].id == assertion_id
    assert [
        ext.value["primaryCoding"]["code"]
        for ext in search_result[0].extensions
        if ext.name == "metakb_star_rating"
    ] == ["4_star"]
    assert search_result[0].direction == "supports"
    assert search_result[0].strength.id == "vicc:e000002"
    assert len(search_result[0].hasEvidenceLines) == 2


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_feature_context_assertion_roundtrip(
    repository: Neo4jRepository, assertions: dict
):
    """Test roundtripping of a statement that uses a gene mutation subject: MOA assertion 120

    * therapeutic response proposition
    * subject variant has a FeatureContextConstraint ("BRAF mutation")
    * combo therapy
    """
    assertion = assertions["BRAF mutation"]
    await repository.load_assertion(assertion)

    assertion_id = "metakb.assertion:RXgu1CLSyUKNM3c7-YfTF_lh5meCOnSM"
    catvar_id = "metakb.cv:FC.metakb.gene_hgnc_1097"
    disease_id = "metakb.disease:ncit_C3224"
    gene_id = "metakb.gene:hgnc_1097"
    therapy_id = "metakb.tg:JgptHcUAwUcXajKEtKy7elEoRLldjZN3"

    assertion_id_result = await repository.search_statements(
        statement_ids=[assertion_id]
    )
    assert len(assertion_id_result) == 1
    assert assertion_id_result[0].id == assertion_id
    assert assertion_id_result[0].proposition.subjectVariant.id == catvar_id
    assert assertion_id_result[0].proposition.objectTherapeutic.root.id == therapy_id
    assert assertion_id_result[0].proposition.conditionQualifier.root.id == disease_id
    assert assertion_id_result[0].proposition.geneContextQualifier.id == gene_id
    assert [
        ext.value["primaryCoding"]["code"]
        for ext in assertion_id_result[0].extensions
        if ext.name == "metakb_star_rating"
    ] == ["1_star"]
    assert assertion_id_result[0].direction == "supports"
    assert assertion_id_result[0].strength.id == "vicc:e000009"
    assert len(assertion_id_result[0].hasEvidenceLines) == 1
    assert len(assertion_id_result[0].hasEvidenceLines[0].hasEvidenceItems) == 1
    assert (
        assertion_id_result[0].hasEvidenceLines[0].hasEvidenceItems[0].id
        == "moa.assertion:166"
    )

    therapy_result = await repository.search_statements(therapy_ids=[therapy_id])
    assert therapy_result == assertion_id_result

    gene_result = await repository.search_statements(gene_ids=[gene_id])
    assert [r for r in gene_result if r.id == assertion_id] == assertion_id_result

    disease_result = await repository.search_statements(disease_ids=[disease_id])
    assert [r for r in disease_result if r.id == assertion_id] == assertion_id_result

    all_combo_result = await repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
        variation_ids=[],
        statement_ids=[assertion_id],
    )
    assert all_combo_result == assertion_id_result

    entity_combo_result = await repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
        variation_ids=[],
    )
    assert entity_combo_result == assertion_id_result

    partial_combo_result = await repository.search_statements(
        therapy_ids=[therapy_id],
        gene_ids=[gene_id],
        disease_ids=[disease_id],
    )
    assert partial_combo_result == assertion_id_result


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_assertion_update(repository: Neo4jRepository, assertions: dict):
    """Test an assertion update that alters the evidence line structure

    Ideally just find two 1-star pieces of evidence so that merging them creates a grouped ev line
    """
    # TODO


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_diagnostic_assertion(repository: Neo4jRepository, assertions: dict):
    assertion_id = "metakb.assertion:Bc6f65XfxIgXv77i5sNsJh0lLaLRIPyz"
    assertion = assertions[assertion_id]
    await repository.load_assertion(assertion)

    assertion_id_result = await repository.search_statements(
        statement_ids=[assertion_id]
    )
    assert len(assertion_id_result) == 1
    assert assertion_id_result[0].id == assertion_id
    assert (
        assertion_id_result[0].proposition.subjectVariant.id
        == "metakb.cv:PSQ.VA.UAquUsb5z-WfBxmE_eqEu3txfseQoRqU"
    )
    assert (
        assertion_id_result[0].proposition.geneContextQualifier.id
        == "metakb.gene:hgnc_1092"
    )
    assert (
        assertion_id_result[0].proposition.objectCondition.root.id
        == "metakb.disease:ncit_C4862"
    )
    assert len(assertion_id_result[0].hasEvidenceLines) == 1
    assert (
        assertion_id_result[0].hasEvidenceLines[0].hasEvidenceItems[0].id
        == "civic.eid:6034"
    )


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_get_stats(repository: Neo4jRepository):
    # If we had a robust test dataset, we could meaningfully check for specific expected counts
    # for now this just checks that they respond
    stats = await repository.get_stats()
    for k, v in stats.model_dump().items():
        assert v, f"Count of {k} is {v}"


@pytest.mark.ci_only
@pytest.mark.asyncio
async def test_get_all_assertion_ids(repository: Neo4jRepository):
    all_ids = await repository.get_all_assertion_ids()
    assert set(all_ids) == {
        "metakb.assertion:RXgu1CLSyUKNM3c7-YfTF_lh5meCOnSM",
        "metakb.assertion:UYyEPTPQPtrMEQjTbat9Ka396w5YKrCi",
        "metakb.assertion:Bc6f65XfxIgXv77i5sNsJh0lLaLRIPyz",
    }
