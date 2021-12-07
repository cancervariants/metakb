"""Test the MetaKB search statements method"""
from metakb.query import QueryHandler
import pytest
import copy


@pytest.fixture(scope="module")
def query_handler():
    """Create query handler test fixture"""
    return QueryHandler()


@pytest.fixture(scope="module")
def civic_vid33_with_gene(civic_vid33, civic_gid19):
    """Create civic vid 33 test fixture"""
    vid33 = copy.deepcopy(civic_vid33)
    vid33["gene_context"] = civic_gid19
    return vid33


@pytest.fixture(scope="module")
def civic_eid2997(civic_eid2997_proposition, civic_vid33_with_gene,
                  civic_tid146, civic_did8, method001, pmid_23982599):
    """Create test fixture for CIViC EID2997"""
    return {
        "id": "civic.eid:2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": civic_eid2997_proposition,
        "variation_origin": "somatic",
        "variation_descriptor": civic_vid33_with_gene,
        "therapy_descriptor": civic_tid146,
        "disease_descriptor": civic_did8,
        "method": method001,
        "supported_by": [pmid_23982599]
    }


def test_civic_eid2997(query_handler, civic_eid2997):
    """Test that search_statements works correctly for CIVIC EID2997"""
    statement_id = "civic.eid:2997"
    resp = query_handler.search_statements(statement_id=statement_id)
    assert resp["statements"] == [civic_eid2997]
    assert resp["warnings"] == []
