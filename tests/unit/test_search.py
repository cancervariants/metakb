"""Test the MetaKB search method."""
from metakb.query import QueryHandler
import pytest

# TODO: Commented out tests to be fixed after first pass


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
def civic_eid1409():
    """Create test fixture for CIViC Evidence 1406."""
    return {
        "id": "civic:eid1409",
        "description": "Phase 3 randomized clinical trial comparing vemurafenib with dacarbazine in 675 patients with previously untreated, metastatic melanoma with the BRAF V600E mutation. At 6 months, overall survival was 84% (95% confidence interval [CI], 78 to 89) in the vemurafenib group and 64% (95% CI, 56 to 73) in the dacarbazine group. A relative reduction of 63% in the risk of death and of 74% in the risk of either death or disease progression was observed with vemurafenib as compared with dacarbazine (P<0.001 for both comparisons).",  # noqa: E501
        "direction": "supports",
        "evidence_level": "civic.evidence_level:A",
        "proposition": {
            "predicate": "predicts_sensitivity_to",
            "variation_origin": "somatic",
            "subject": "ga4gh:VA.mJbjSsW541oOsOtBoX36Mppr6hMjbjFr",
            "object_qualifier": "ncit:C3510",
            "object": "ncit:C64768",
            "type": "therapeutic_response_proposition"
        },
        "variation_descriptor": "civic:vid12",
        "therapy_descriptor": "civic:tid4",
        "disease_descriptor": "civic:did206",
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
                "id": "pmid:21639808",
                "label": "Chapman et al., 2011, N. Engl. J. Med.",
                "description": "Improved survival with vemurafenib in melanoma with BRAF V600E mutation.",  # noqa: E501
                "xrefs": [
                    "pmc:PMC3549296"
                ]
            }
        ],
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
            "label": "Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",  # noqa: E501
            "url": "https://pubmed.ncbi.nlm.nih.gov/27993330/",
            "version": {
                "year": 2017,
                "month": 1,
                "day": None
            },
            "reference": "Li MM, Datto M, Duncavage EJ, et al."
        },
        "support_evidence": [
            {
                "id": "civic:eid2629",
                "label": "EID2629",
                "description": "In an in vitro study using NCI-H1666 cells (wildtype EGFR) and NCI-H3255 cells (EGFR-L858R), inhibition of cell growth was used as an assay to determine sensitivity to irreversible tyrosine kinase inhibitor (TKI) drugs. Cells with an EGFR L858R mutation demonstrated an improved response to afatinib (IC50: 0.7nM vs. 60nM) compared to wildtype EGFR cells.",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "civic:eid883",
                "label": "EID883",
                "description": "In a phase 2 study of patients with lung adenocarcinoma (stage IIIb with pleural effusion or stage IV) and EGFR mutations, treated with afatinib were assessed by objective response. 129 patients were treated with afatinib. 66% of the 106 patients with two common activating EGFR mutations (deletion 19 or L858R) had an objective response compared to 39% of 23 patients with less common mutations.",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "civic:eid968",
                "label": "EID968",
                "description": "Cells harboring L858R were sensitive to afatinib. This study performed drug response assays using five human NSCLC cell lines with various combinations of EGFR mutations. In order to directly compare the sensitivity of multiple EGFR mutations to EGFR-TKIs the authors also generated multiple EGFR transduced Ba/F3 stable cell lines and evaluated sensitivity to EGFR-TKIs by MTS assay.",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "civic:eid982",
                "label": "EID982",
                "description": "Afatinib is an irreversible covalent inhibitor of EGFR (second generation). This Phase III clinical trial (LUX-Lung 6; NCT01121393) was performed in Asian patients with EGFR mutant advanced NSCLC. 364 eligible patients with EGFR mutations were assigned to afatinib (n=242) or gemcitabine and cisplatin (n=122) treatment. The trial observed significantly longer median progression-free survival with afatinib vs. gemcitabine and cisplatin treatment (11.0 vs. 5.6 months). Afatinib/Chemotherapy group compositions: 51.2/50.8 % del 19; 38/37.7 % Leu858Arg; 10.8/11.5 % Uncommon.",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "civic:eid879",
                "label": "EID879",
                "description": "A phase III clinical trial (NCT00949650) found that median progression free survival among patients with exon 19 deletions or L858R EGFR mutations (n = 308) was 13.6 months for afatinib and 6.9 months for chemotherapy (HR, 0.47; 95% CI, 0.34 to 0.65; P = 0.001).",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "civic:eid2997",
                "label": "EID2997",
                "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                "xrefs": []
            },
            {
                "id": "https://www.nccn.org/professionals/physician_gls/default.aspx",  # noqa: #501
                "label": "NCCN Guidelines: Non-Small Cell Lung Cancer version 3.2018",  # noqa: #501
                "description": None,
                "xrefs": []
            }
        ],
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
            if key == 'support_evidence':
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
    for s in response['statements']:
        assert s['proposition']['object_qualifier'] == object_qualifier
        assert s['proposition']['subject'] == subject
        assert s['proposition']['object'] == object

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
    for s in response['statements']:
        assert s['proposition']['object_qualifier'] == object_qualifier
        assert s['proposition']['subject'] == subject
        assert s['proposition']['object']


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
