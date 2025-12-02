"""Test Neo4j repository implementation."""

import pytest
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


@pytest.mark.ci_only
def test_statement_roundtrip(
    repository: Neo4jRepository, civic_eid2997_study_stmt: dict
):
    statement = Statement(**civic_eid2997_study_stmt)
    repository.load_statement(statement)

    eid_result = repository.search_statements(statement_ids=["civic.eid:2997"])
    assert len(eid_result) == 1
    assert eid_result[0].id == "civic.eid:2997"
    assert eid_result[0].proposition.subjectVariant.id == "civic.mpid:33"
    assert eid_result[0].proposition.objectTherapeutic.root.id == "civic.tid:146"
    assert eid_result[0].proposition.conditionQualifier.root.id == "civic.did:8"
    assert eid_result[0].proposition.geneContextQualifier.id == "civic.gid:19"

    therapy_result = repository.search_statements(therapy_ids=["rxcui:1430438"])
    assert therapy_result == eid_result

    gene_result = repository.search_statements(gene_ids=["hgnc:3236"])
    assert gene_result == eid_result

    disease_result = repository.search_statements(disease_ids=["ncit:C2926"])
    assert disease_result == eid_result

    var_result = repository.search_statements(
        variation_ids=["ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"]
    )
    assert var_result == eid_result

    all_combo_result = repository.search_statements(
        therapy_ids=["rxcui:1430438"],
        gene_ids=["hgnc:3236"],
        disease_ids=["ncit:C2926"],
        variation_ids=["ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"],
        statement_ids=["civic.eid:2997"],
    )
    assert all_combo_result == eid_result

    entity_combo_result = repository.search_statements(
        therapy_ids=["rxcui:1430438"],
        gene_ids=["hgnc:3236"],
        disease_ids=["ncit:C2926"],
        variation_ids=["ga4gh:VA.S41CcMJT2bcd8R4-qXZWH1PoHWNtG2PZ"],
    )
    assert entity_combo_result == eid_result

    partial_combo_result = repository.search_statements(
        therapy_ids=["rxcui:1430438"],
        gene_ids=["hgnc:3236"],
        disease_ids=["ncit:C2926"],
    )
    assert partial_combo_result == eid_result


@pytest.mark.ci_only
def test_therapygroup_statement_roundtrip(
    repository: Neo4jRepository, civic_eid816_study_stmt: dict
):
    """Test that statement based on a TherapyGroup roundtrips correctly"""
    statement = Statement(**civic_eid816_study_stmt)
    repository.load_statement(statement)

    eid_result = repository.search_statements(statement_ids=["civic.eid:816"])
    assert len(eid_result) == 1
    assert eid_result[0].id == "civic.eid:816"
    assert eid_result[0].proposition.subjectVariant.id == "civic.mpid:12"
    assert (
        sorted(
            eid_result[0].proposition.objectTherapeutic.root.therapies,
            key=lambda th: th.id,
        )[0].id
        == "civic.tid:16"
    )
    assert (
        sorted(
            eid_result[0].proposition.objectTherapeutic.root.therapies,
            key=lambda th: th.id,
        )[1].id
        == "civic.tid:28"
    )
    assert eid_result[0].proposition.conditionQualifier.root.id == "civic.did:11"
    assert eid_result[0].proposition.geneContextQualifier.id == "civic.gid:5"

    therapy_result = repository.search_statements(therapy_ids=["rxcui:318341"])
    assert therapy_result == eid_result
    therapy_result = repository.search_statements(therapy_ids=["rxcui:263034"])
    assert therapy_result == eid_result

    gene_result = repository.search_statements(gene_ids=["hgnc:1097"])
    assert gene_result == eid_result

    disease_result = repository.search_statements(disease_ids=["ncit:C4978"])
    assert disease_result == eid_result

    var_result = repository.search_statements(
        variation_ids=["ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"]
    )
    assert var_result == eid_result

    all_combo_result = repository.search_statements(
        therapy_ids=["rxcui:318341", "rxcui:263034"],
        gene_ids=["hgnc:1097"],
        disease_ids=["ncit:C4978"],
        variation_ids=["ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"],
        statement_ids=["civic.eid:816"],
    )
    assert all_combo_result == eid_result

    entity_combo_result = repository.search_statements(
        therapy_ids=["rxcui:318341"],
        gene_ids=["hgnc:1097"],
        disease_ids=["ncit:C4978"],
        variation_ids=["ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L"],
    )
    assert entity_combo_result == eid_result

    partial_combo_result = repository.search_statements(
        therapy_ids=["rxcui:263034"],
        gene_ids=["hgnc:1097"],
        disease_ids=["ncit:C4978"],
    )
    assert partial_combo_result == eid_result


@pytest.mark.ci_only
def test_get_stats(repository: Neo4jRepository):
    """If we had a robust test dataset, we could check for specific expected counts, but for now this just checks that they're nonzero"""
    stats = repository.get_stats()
    for k, v in stats.model_dump().items():
        assert v, f"Count of {k} is {v}"
