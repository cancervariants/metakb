"""Test the MetaKB search method."""
from metakb.query import QueryHandler
import pytest

# TODO:
#  Commented out tests to be fixed after first pass
#  Load DB with test data


@pytest.fixture(scope='module')
def query_handler():
    """Create query handler test fixture."""
    class QueryGetter:

        def __init__(self):
            self.query_handler = QueryHandler(uri="bolt://localhost:7687",
                                              credentials=("neo4j", "admin"))

        def search(self, variation='', disease='', therapy='', gene=''):
            response = self.query_handler.search(variation=variation,
                                                 disease=disease,
                                                 therapy=therapy, gene=gene)
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
        "proposition": "proposition:148",
        "variation_descriptor": "civic:vid33",
        "therapy_descriptor": "civic:tid146",
        "disease_descriptor": "civic:did8",
        "method": "method:001",
        "supported_by": ["pmid:23982599"]
    }


@pytest.fixture(scope='module')
def eid2997_proposition():
    """Create a test fixture for EID2997 proposition."""
    return {
        "id": "proposition:148",
        "predicate": "predicts_sensitivity_to",
        "variation_origin": "somatic",
        "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
        "object_qualifier": "ncit:C2926",
        "object": "ncit:C66940",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def eid1409_proposition():
    """Create test fixture for EID1409 proposition."""
    return {
        "id": "proposition:702",
        "predicate": "predicts_sensitivity_to",
        "variation_origin": "somatic",
        "subject": "ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr",
        "object_qualifier": "ncit:C3510",
        "object": "ncit:C64768",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def civic_eid1409():
    """Create test fixture for CIViC Evidence 1406."""
    return {
        "id": "civic:eid1409",
        "description": "Phase 3 randomized clinical trial comparing vemurafenib with dacarbazine in 675 patients with previously untreated, metastatic melanoma with the BRAF V600E mutation. At 6 months, overall survival was 84% (95% confidence interval [CI], 78 to 89) in the vemurafenib group and 64% (95% CI, 56 to 73) in the dacarbazine group. A relative reduction of 63% in the risk of death and of 74% in the risk of either death or disease progression was observed with vemurafenib as compared with dacarbazine (P<0.001 for both comparisons).",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": "proposition:702",
        "variation_descriptor": "civic:vid12",
        "therapy_descriptor": "civic:tid4",
        "disease_descriptor": "civic:did206",
        "method": "method:001",
        "supported_by": ["pmid:21639808"],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def civic_aid6():
    """Create CIViC AID 6 test fixture."""
    return {
        "id": "civic:aid6",
        "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved, and is recommended (category 1) by NCCN guidelines along with erlotinib, gefitinib and osimertinib as first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
        "evidence_level": "civic.amp_level:tier_i_-_level_a",
        "direction": "supports",
        "proposition": "proposition:148",
        "variation_descriptor": "civic:vid33",
        "therapy_descriptor": "civic:tid146",
        "disease_descriptor": "civic:did8",
        "method": "method:002",
        "supported_by": ["civic:eid2629", "civic:eid883", "civic:eid968",
                         "civic:eid982", "civic:eid879", "civic:eid2997",
                         "document:001"],
        "type": "Statement"
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
            if key == 'supported_by':
                assert_same_keys_list_items(actual_data[key], test_data[key])
            elif isinstance(actual_data[key], list):
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


def return_statement(query_handler, statement_id, **kwargs):
    """Return the statement given ID if it exists."""
    response = query_handler.search(**kwargs)
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
    statement_id = 'civic:eid2997'

    # Test search by Subject
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR')
    assertions(civic_eid2997, s)

    # Test search by Object
    s = return_statement(query_handler, statement_id, therapy='ncit:C66940')
    assertions(civic_eid2997, s)

    # Test search by Object Qualifier
    s = return_statement(query_handler, statement_id, disease='ncit:C2926')
    assertions(civic_eid2997, s)

    # Test search by Gene Descriptor
    # HGNC ID
    s = return_statement(query_handler, statement_id, gene='hgnc:3236')
    assertions(civic_eid2997, s)

    # Label
    s = return_statement(query_handler, statement_id, gene='EGFR')
    assertions(civic_eid2997, s)

    # Alt label
    s = return_statement(query_handler, statement_id, gene='ERBB1')
    assertions(civic_eid2997, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s = return_statement(query_handler, statement_id, variation='EGFR L858R')
    assertions(civic_eid2997, s)

    # Sequence ID
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE'
                         )
    assertions(civic_eid2997, s)

    # Alt Label
    # s = return_statement(query_handler, statement_id,
    # variation='egfr Leu858ARG')
    # assertions(civic_eid2997, s)

    # HGVS Expression
    s = return_statement(query_handler, statement_id,
                         variation='NP_005219.2:p.Leu858Arg')
    assertions(civic_eid2997, s)

    # Test search by Therapy Descriptor
    # Label
    s = return_statement(query_handler, statement_id, therapy='Afatinib')
    assertions(civic_eid2997, s)

    # Alt Label
    s = return_statement(query_handler, statement_id, therapy='BIBW2992')
    assertions(civic_eid2997, s)

    # Test search by Disease Descriptor
    # Label
    s = return_statement(query_handler, statement_id,
                         disease='Lung Non-small Cell Carcinoma')
    assertions(civic_eid2997, s)


def test_civic_eid1409(query_handler, civic_eid1409):
    """Test search on CIViC Evidence Item 1409."""
    statement_id = 'civic:eid1409'

    # Test search by Subject
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr',
                         )
    assertions(civic_eid1409, s)

    # Test search by Object
    s = return_statement(query_handler, statement_id, therapy='ncit:C64768')
    assertions(civic_eid1409, s)

    # Test search by Object Qualifier
    s = return_statement(query_handler, statement_id, disease='ncit:C3510')
    assertions(civic_eid1409, s)

    # Test search by Gene Descriptor
    # HGNC ID
    s = return_statement(query_handler, statement_id, gene='hgnc:1097')
    assertions(civic_eid1409, s)

    # Label
    s = return_statement(query_handler, statement_id, gene='BRAF')
    assertions(civic_eid1409, s)

    # TODO: Not found in gene normalizer
    # # Alt label
    # s = return_statement(query_handler, statement_id, gene='NS7')
    # assertions(civic_eid1409, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    # s = return_statement(query_handler, statement_id, variation='BRAF V600E')
    # assertions(civic_eid1409, s)

    # Sequence ID
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y'
                         )
    assertions(civic_eid1409, s)

    # # Alt Label
    # s = return_statement(query_handler, statement_id,
    # variation='braf val600glu')
    # assertions(civic_eid1409, s)

    # HGVS Expression
    s = return_statement(query_handler, statement_id,
                         variation='NP_004324.2:p.Val600Glu')
    assertions(civic_eid1409, s)

    # Test search by Therapy Descriptor
    # Label
    s = return_statement(query_handler, statement_id, therapy='Vemurafenib')
    assertions(civic_eid1409, s)

    # # Alt Label
    # s = return_statement(query_handler,
    #                      'BRAF(V600E) Kinase Inhibitor RO5185426',
    #                      statement_id)
    # assertions(civic_eid1409, s)

    # Label
    s = return_statement(query_handler, statement_id, disease='Skin Melanoma')
    assertions(civic_eid1409, s)


def test_civic_aid6(query_handler, civic_aid6):
    """Test search on CIViC Evidence Item 6."""
    statement_id = 'civic:aid6'

    # Test search by Subject
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR')
    assertions(civic_aid6, s)

    # Test search by Object
    s = return_statement(query_handler, statement_id, therapy='ncit:C66940')
    assertions(civic_aid6, s)

    # Test search by Object Qualifier
    s = return_statement(query_handler, statement_id, disease='ncit:C2926')
    assertions(civic_aid6, s)

    # Test search by Gene Descriptor
    # HGNC ID
    s = return_statement(query_handler, statement_id, gene='hgnc:3236')
    assertions(civic_aid6, s)

    # Label
    s = return_statement(query_handler, statement_id, gene='EGFR')
    assertions(civic_aid6, s)

    # Alt label
    s = return_statement(query_handler, statement_id, gene='ERBB1')
    assertions(civic_aid6, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    # s = return_statement(query_handler, statement_id, variation='EGFR L858R')
    # assertions(civic_aid6, s)

    # Sequence ID
    s = return_statement(query_handler, statement_id,
                         variation='ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE')
    assertions(civic_aid6, s)

    # Alt Label
    # s = return_statement(query_handler, statement_id,
    # variation='egfr leu858arg')
    # assertions(civic_aid6, s)

    # HGVS Expression
    s = return_statement(query_handler, statement_id,
                         variation='NP_005219.2:p.leu858arg')
    assertions(civic_aid6, s)

    # Label
    s = return_statement(query_handler, statement_id, therapy='afatinib')
    assertions(civic_aid6, s)

    # Alt Label
    s = return_statement(query_handler, statement_id, therapy='BIBW 2992')
    assertions(civic_aid6, s)

    # Label
    s = return_statement(query_handler, statement_id,
                         disease='Lung Non-small Cell Carcinoma    ')
    assertions(civic_aid6, s)


def test_multiple_parameters(query_handler):
    """Test that multiple parameter searches work correctly."""
    # Test no match
    response = query_handler.search(variation=' braf v600e', gene='egfr',
                                    disease='cancer', therapy='cisplatin')
    assert response['statements'] == []

    response = query_handler.search(therapy='cisplatin', disease='4dfadfafas')
    assert response['statements'] == []

    # Test EID2997 queries
    object_qualifier = 'ncit:C2926'
    subject = 'ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR'
    object = 'ncit:C66940'
    response = query_handler.search(
        variation='NP_005219.2:p.Leu858Arg',
        disease='NSCLC',
        therapy='Afatinib'
    )
    for s in response['propositions']:
        assert s['object_qualifier'] == object_qualifier
        assert s['subject'] == subject
        assert s['object'] == object

    # Wrong gene
    response = query_handler.search(
        variation='NP_005219.2:p.Leu858Arg',
        disease='NSCLC',
        therapy='Afatinib',
        gene='braf'
    )
    assert response['statements'] == []

    # Test eid1409 queries
    object_qualifier = 'ncit:C3510'
    subject = 'ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr'
    response = query_handler.search(
        variation='ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr',
        disease='malignant trunk melanoma'
    )
    for s in response['propositions']:
        assert s['object_qualifier'] == object_qualifier
        assert s['subject'] == subject
        assert s['object']


def test_no_matches(query_handler):
    """Test invalid query matches."""
    # GA instead of VA
    response = query_handler.search('ga4gh:GA.WyOqFMhc8a'
                                    'OnMFgdY0uM7nSLNqxVPAiR')
    assert response['statements'] == []

    # Invalid ID
    response = \
        query_handler.search(disease='ncit:C292632425235321524352435623462')
    assert response['statements'] == []

    # Empty query
    response = query_handler.search(disease='')
    assert response['statements'] == []

    response = query_handler.search(gene='', therapy='', variation='',
                                    disease='')
    assert response['statements'] == []
    assert response['warnings'] == ['No parameters were entered.']

    # Invalid variation
    response = query_handler.search(variation='v600e')
    assert response['statements'] == []
