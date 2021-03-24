"""Test the MetaKB search method."""
from metakb.query import QueryHandler
import pytest


@pytest.fixture(scope='module')
def query_handler():
    """Create query handler test fixture."""
    class QueryGetter:

        def __init__(self):
            self.query_handler = QueryHandler(uri="bolt://localhost:7687",
                                              credentials=("neo4j", "admin"))

        def search(self, query_str):
            response = self.query_handler.search(query_str)
            return response
    return QueryGetter()


@pytest.fixture(scope='module')
def civic_eid2997():
    """Create CIVIC Evidence Item 2997 test fixture."""
    return {
        "id": "civic:eid2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": {
            "predicate": "predicts_sensitivity_to",
            "variation_origin": "somatic",
            "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
            "object_qualifier": "ncit:C2926",
            "object": "ncit:C66940",
            "type": "therapeutic_response_proposition"
        },
        "variation_descriptor": "civic:vid33",
        "therapy_descriptor": "civic:tid146",
        "disease_descriptor": "civic:did8",
        "method": {
            "label": "Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
            "url": "https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x",  # noqa: E501
            "version": {
                "year": 2019,
                "month": 11,
                "day": 29
            },
            "reference": "Danos, A.M., Krysiak, K., Barnell, E.K. et al."
        },
        "support_evidence": [
            {
                "id": "pmid:23982599",
                "label": "Dungo et al., 2013, Drugs",
                "description": "Afatinib: first global approval.",
                "xrefs": []
            }
        ]
    }


@pytest.fixture(scope='module')
def subject1():
    """Create test fixture for Variation/Allele ID."""
    return {

    }


def assert_same_keys_list_items(actual, test):
    """Assert that keys in a dict are same or items in list are same."""
    assert len(list(test)) == len(list(actual))
    for item in list(actual):
        assert item in test


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        assert test == actual


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        assert_same_keys_list_items(actual_data.keys(), test_data.keys())
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(test_data[key]) == set(actual_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        assert_same_keys_list_items(actual_data, test_data)
        for item in actual_data:
            if isinstance(item, list):
                assert set(test_data) == set(actual_data)
            else:
                assert_non_lists(actual_data, test_data)


def return_statement(query_handler, query, statement_id):
    """Return the statement given ID if it exists."""
    response = query_handler.search(query)
    statements = response['statements']
    assert len(statements) != 0
    s = None
    for statement in statements:
        if statement['id'] == statement_id:
            s = statement
            break
    return s


def test_civic_eid2997(query_handler, civic_eid2997):
    """Test search on CIViC Evidence Item 2997."""
    # Test search by Statement ID works
    response = query_handler.search('CIVIC:EID2997')
    statements = response['statements']
    assert len(statements) == 1
    assertions(civic_eid2997, statements[0])

    statement_id = 'civic:eid2997'

    # Test search by Subject
    s = return_statement(query_handler,
                         'ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR',
                         statement_id)
    assertions(civic_eid2997, s)

    # Test search by Object
    s = return_statement(query_handler, 'ncit:C66940', statement_id)
    assertions(civic_eid2997, s)

    # Test search by Object Qualifier
    s = return_statement(query_handler, 'ncit:C2926', statement_id)
    assertions(civic_eid2997, s)

    # Test search by Variation Descriptor
    # ID
    s = return_statement(query_handler, 'civic:vid33', statement_id)
    assertions(civic_eid2997, s)

    # Gene Symbol + Variant Name
    s = return_statement(query_handler, 'EGFR L858R', statement_id)
    assertions(civic_eid2997, s)

    # Label
    s = return_statement(query_handler, 'L858R', statement_id)
    assertions(civic_eid2997, s)

    # Sequence ID
    s = return_statement(query_handler,
                         'ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE',
                         statement_id)
    assertions(civic_eid2997, s)

    # XREF
    s = return_statement(query_handler, 'clinvar:16609', statement_id)
    assertions(civic_eid2997, s)

    # Alt Label
    s = return_statement(query_handler, 'Leu858ARG', statement_id)
    assertions(civic_eid2997, s)

    # HGVS Expression
    s = return_statement(query_handler, 'NP_005219.2:p.Leu858Arg',
                         statement_id)
    assertions(civic_eid2997, s)

    # Test search by Therapy Descriptor
    # ID
    s = return_statement(query_handler, 'civic:tid146', statement_id)
    assertions(civic_eid2997, s)

    # Label
    s = return_statement(query_handler, 'Afatinib', statement_id)
    assertions(civic_eid2997, s)

    # Alt Label
    s = return_statement(query_handler, 'BIBW2992', statement_id)
    assertions(civic_eid2997, s)

    # Test search by Disease Descriptor
    # ID
    s = return_statement(query_handler, 'civic:did8', statement_id)
    assertions(civic_eid2997, s)

    # Label
    s = return_statement(query_handler, 'Lung Non-small Cell Carcinoma',
                         statement_id)
    assertions(civic_eid2997, s)


def test_no_matches(query_handler):
    """Test invalid query matches."""
    # GA instead of VA
    response = query_handler.search('ga4gh:GA.WyOqFMhc8a'
                                    'OnMFgdY0uM7nSLNqxVPAiR')
    assert response['statements'] == []

    # Invalid ID
    response = query_handler.search('ncit:C292632425235321524352435623462')
    assert response['statements'] == []

    # Empty query
    response = query_handler.search('')
    assert response['statements'] == []
