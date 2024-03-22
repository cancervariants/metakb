"""Test the MetaKB search method."""
import pytest

from metakb.version import __version__, LAST_UPDATED

# TODO:
#  Commented out tests to be fixed after first pass
#  Load DB with test data


@pytest.mark.asyncio
async def return_response(query_handler, statement_id, **kwargs):
    """Return the statement given ID if it exists."""
    response = await query_handler.search(**kwargs)
    statements = response['statements']
    propositions = response['propositions']
    assert len(statements) != 0
    assert len(propositions) != 0
    assert len(response['matches']['statements']) != 0
    assert len(response['matches']['propositions']) != 0
    s = None
    for statement in statements:
        if statement['id'] == statement_id:
            s = statement
            break

    p = None
    for proposition in propositions:
        if s['proposition'] == proposition['id']:
            p = proposition
            break
    return s, p


def assert_no_match(response):
    """No match assertions for queried concepts in search."""
    assert response['statements'] == []
    assert response['propositions'] == []
    assert len(response['warnings']) > 0


def assert_no_match_id(response):
    """No match assertions for search by id."""
    assert len(response.keys()) == 3
    assert len(response['warnings']) > 0


def assert_keys_for_detail_false(response_keys):
    """Check that keys aren't in response when detail is false."""
    assert 'variation_descriptors' not in response_keys
    assert 'gene_descriptors' not in response_keys
    assert 'therapy_descriptors' not in response_keys
    assert 'disease_descriptors' not in response_keys
    assert 'methods' not in response_keys
    assert 'documents' not in response_keys


def assert_keys_for_detail_true(response_keys, response, is_evidence=True,
                                tr_response=True):
    """Check that keys are in response when detail is false."""
    fields = ['variation_descriptors', 'gene_descriptors',
              'disease_descriptors', 'methods',
              'documents', 'statements', 'propositions']
    if tr_response:
        fields += ['therapy_descriptors']
    for field in fields:
        assert field in response_keys
        if is_evidence:
            # Evidence only does not have supported_by with other statements
            assert len(response[field]) == 1
        else:
            assert len(response[field]) > 1


def assert_response_items(response, statement, proposition,
                          variation_descriptor, gene_descriptor,
                          disease_descriptor, method,
                          document, therapy_descriptor,
                          check_statement, check_proposition,
                          check_variation_descriptor,
                          check_descriptor, check_method, check_document
                          ):
    """Check that search response match expected values."""
    if therapy_descriptor:
        assert_keys_for_detail_true(response.keys(), response)
    else:
        assert_keys_for_detail_true(response.keys(), response,
                                    tr_response=False)

    response_statement = response['statements'][0]
    response_proposition = response['propositions'][0]
    response_variation_descriptor = response['variation_descriptors'][0]
    response_gene_descriptor = response['gene_descriptors'][0]
    if therapy_descriptor:
        response_therapy_descriptor = response['therapy_descriptors'][0]
    else:
        response_therapy_descriptor = None
    response_disease_descriptor = response['disease_descriptors'][0]
    response_method = response['methods'][0]
    response_document = response['documents'][0]

    check_statement(response_statement, statement)
    check_proposition(response_proposition, proposition)
    check_variation_descriptor(response_variation_descriptor,
                               variation_descriptor)
    check_descriptor(gene_descriptor, response_gene_descriptor)
    check_descriptor(disease_descriptor, response_disease_descriptor)
    if therapy_descriptor:
        check_descriptor(therapy_descriptor, response_therapy_descriptor)
    check_method(response_method, method)
    check_document(response_document, document)

    # Assert that IDs match in response items
    assert response_statement['proposition'] == response_proposition['id']
    assert response_statement['variation_descriptor'] == \
           response_variation_descriptor['id']
    if therapy_descriptor:
        assert response_statement['therapy_descriptor'] == \
               response_therapy_descriptor['id']
    assert response_statement['disease_descriptor'] == \
           response_disease_descriptor['id']
    assert response_statement['method'] == response_method['id']
    assert response_statement['supported_by'][0] == response_document['id']

    assert proposition['subject'] == \
           response_variation_descriptor['variation_id']
    assert proposition['object_qualifier'] == \
           response_disease_descriptor['disease_id']
    if therapy_descriptor:
        assert proposition['object'] == \
               response_therapy_descriptor['therapy_id']

    assert response_variation_descriptor['gene_context'] == \
           response_gene_descriptor['id']


def assert_general_search_queries(response):
    """Check for general search queries."""
    assert response['matches']
    len_statement_matches = len(response['matches']['statements'])
    assert len_statement_matches > 0
    assert len(response['matches']['propositions']) > 0
    len_statements = len(response['statements'])
    assert len_statements > 0
    assert len_statement_matches == len_statements
    assert len(response['propositions']) > 0
    assert len(response['methods']) > 0
    assert len(response['documents']) > 0


def test_search_id(query_handler):
    """Test that search id method works correctly."""
    resp = query_handler.search_by_id(
        "proposition:xsTCVDo1bo2P_6Sext0Y3ibU3MPbiyXE"
    )
    assert resp["proposition"]
    assert not resp["warnings"]
    assert query_handler.search_by_id("proposition:001")["warnings"]
    assert query_handler.search_by_id("proposition:0")["warnings"]
    assert query_handler.search_by_id("proposition:1")["warnings"]


@pytest.mark.asyncio
async def test_general_search_queries(query_handler):
    """Test that queries do not return errors."""
    response = await query_handler.search(variation='braf v600e', detail=True)
    assert_general_search_queries(response)

    response = await query_handler.search(variation='egfr l858r', detail=True)
    assert_general_search_queries(response)

    response = await query_handler.search(disease='cancer', detail=True)
    assert_general_search_queries(response)


@pytest.mark.asyncio
async def test_civic_eid2997(query_handler, civic_eid2997_statement,
                             civic_eid2997_proposition, check_statement,
                             check_proposition):
    """Test search on CIViC Evidence Item 2997."""
    statement_id = 'civic.eid:2997'

    # Test search by Subject
    s, p = await return_response(query_handler, statement_id,
                                 variation='ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Object
    s, p = await return_response(query_handler, statement_id, therapy='rxcui:1430438')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Object Qualifier
    s, p = await return_response(query_handler, statement_id, disease='ncit:C2926')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = await return_response(query_handler, statement_id, gene='hgnc:3236')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Label
    s, p = await return_response(query_handler, statement_id, gene='EGFR')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Alt label
    s, p = await return_response(query_handler, statement_id, gene='ERBB1')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = await return_response(query_handler, statement_id, variation='EGFR L858R')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Alt Label
    s, p = await return_response(query_handler, statement_id,
                                 variation='egfr Leu858ARG')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # HGVS Expression
    s, p = await return_response(query_handler, statement_id,
                                 variation='NP_005219.2:p.Leu858Arg')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Therapy Descriptor
    # Label
    s, p = await return_response(query_handler, statement_id, therapy='Afatinib')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Alt Label
    s, p = await return_response(query_handler, statement_id, therapy='BIBW2992')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)

    # Test search by Disease Descriptor
    # Label
    s, p = await return_response(query_handler, statement_id,
                                 disease='Lung Non-small Cell Carcinoma')
    check_statement(s, civic_eid2997_statement)
    check_proposition(p, civic_eid2997_proposition)


@pytest.mark.asyncio
async def test_civic_eid1409_statement(query_handler, civic_eid1409_statement,
                                       check_statement):
    """Test search on CIViC Evidence Item 1409."""
    statement_id = 'civic.eid:1409'

    # Test search by Subject
    s, p = await return_response(query_handler, statement_id,
                                 variation='ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO')
    check_statement(s, civic_eid1409_statement)

    # Test search by Object
    s, p = await return_response(query_handler, statement_id, therapy='ncit:C64768')
    check_statement(s, civic_eid1409_statement)

    # Test search by Object Qualifier
    s, p = await return_response(query_handler, statement_id, disease='ncit:C3510')
    check_statement(s, civic_eid1409_statement)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = await return_response(query_handler, statement_id, gene='hgnc:1097')
    check_statement(s, civic_eid1409_statement)

    # Label
    s, p = await return_response(query_handler, statement_id, gene='BRAF')
    check_statement(s, civic_eid1409_statement)

    # TODO: Not found in gene normalizer
    # # Alt label
    # s, p = await return_response(query_handler,
    # statement_id, gene='NS7')
    # assertions(civic_eid1409_statement, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = await return_response(query_handler, statement_id, variation='BRAF V600E')
    check_statement(s, civic_eid1409_statement)

    # # Alt Label
    s, p = await return_response(query_handler, statement_id,
                                 variation='braf val600glu')
    check_statement(s, civic_eid1409_statement)

    # HGVS Expression
    s, p = await return_response(query_handler, statement_id,
                                 variation='NP_004324.2:p.Val600Glu')
    check_statement(s, civic_eid1409_statement)

    # Test search by Therapy Descriptor
    # Label
    s, p = await return_response(query_handler, statement_id, therapy='Vemurafenib')
    check_statement(s, civic_eid1409_statement)

    # # Alt Label
    s, p = await return_response(query_handler, statement_id,
                                 therapy='BRAF(V600E) Kinase Inhibitor RO5185426')
    check_statement(s, civic_eid1409_statement)

    # Label
    s, p = await return_response(query_handler, statement_id, disease='Skin Melanoma')
    check_statement(s, civic_eid1409_statement)


@pytest.mark.asyncio
async def test_civic_aid6(query_handler, civic_aid6_statement, check_statement):
    """Test search on CIViC Evidence Item 6."""
    statement_id = 'civic.aid:6'

    # Test search by Subject
    s, p = await return_response(query_handler, statement_id,
                                 variation='ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA')
    check_statement(s, civic_aid6_statement)

    # Test search by Object
    s, p = await return_response(query_handler, statement_id, therapy='rxcui:1430438')
    check_statement(s, civic_aid6_statement)

    # Test search by Object Qualifier
    s, p = await return_response(query_handler, statement_id, disease='ncit:C2926')
    check_statement(s, civic_aid6_statement)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = await return_response(query_handler, statement_id, gene='hgnc:3236')
    check_statement(s, civic_aid6_statement)

    # Label
    s, p = await return_response(query_handler, statement_id, gene='EGFR')
    check_statement(s, civic_aid6_statement)

    # Alt label
    s, p = await return_response(query_handler, statement_id, gene='ERBB1')
    check_statement(s, civic_aid6_statement)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = await return_response(query_handler, statement_id, variation='EGFR L858R')
    check_statement(s, civic_aid6_statement)

    # Alt Label
    s, p = await return_response(query_handler, statement_id,
                                 variation='egfr leu858arg')
    check_statement(s, civic_aid6_statement)

    # HGVS Expression
    s, p = await return_response(query_handler, statement_id,
                                 variation='NP_005219.2:p.leu858arg')
    check_statement(s, civic_aid6_statement)

    # Label
    s, p = await return_response(query_handler, statement_id, therapy='afatinib')
    check_statement(s, civic_aid6_statement)

    # Alt Label
    s, p = await return_response(query_handler, statement_id, therapy='BIBW 2992')
    check_statement(s, civic_aid6_statement)

    # Label
    s, p = await return_response(query_handler, statement_id,
                                 disease='Lung Non-small Cell Carcinoma    ')
    check_statement(s, civic_aid6_statement)


@pytest.mark.asyncio
async def test_multiple_parameters(query_handler):
    """Test that multiple parameter searches work correctly."""
    # Test no match
    response = await query_handler.search(variation=' braf v600e', gene='egfr',
                                          disease='cancer', therapy='cisplatin')
    assert_no_match(response)

    response = await query_handler.search(therapy='cisplatin', disease='4dfadfafas')
    assert_no_match(response)

    # Test EID2997 queries
    object_qualifier = 'ncit:C2926'
    subject = 'ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA'
    object = 'rxcui:1430438'
    response = await query_handler.search(
        variation='NP_005219.2:p.Leu858Arg',
        disease='NSCLC',
        therapy='Afatinib'
    )
    for p in response['propositions']:
        if p['id'] in response['matches']['propositions']:
            assert p['object_qualifier'] == object_qualifier
            assert p['subject'] == subject
            assert p['object'] == object

    # Wrong gene
    response = await query_handler.search(
        variation='NP_005219.2:p.Leu858Arg',
        disease='NSCLC',
        therapy='Afatinib',
        gene='braf'
    )
    assert_no_match(response)

    # Test eid1409 queries
    object_qualifier = 'ncit:C3510'
    subject = 'ga4gh:VA.ZDdoQdURgO2Daj2NxLj4pcDnjiiAsfbO'
    response = await query_handler.search(
        variation=subject,
        disease='malignant trunk melanoma'
    )
    for p in response['propositions']:
        if p['id'] in response['matches']['propositions']:
            assert p['object_qualifier'] == object_qualifier
            assert p['subject'] == subject
            assert p['object']

    # No Match for statement ID
    response = await query_handler.search(
        variation=subject,
        disease='malignant trunk melanoma',
        statement_id='civic.eid:2997'
    )
    assert_no_match(response)

    # CIViC EID2997
    response = await query_handler.search(
        statement_id='civiC.eid:2997',
        variation='ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA'
    )
    assert len(response['statements']) == 1
    assert len(response['propositions']) == 1
    assert len(response['matches']['statements']) == 1
    assert len(response['matches']['propositions']) == 1

    # CIViC AID6
    response = await query_handler.search(
        statement_id='CIViC.AID:6',
        variation='ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA',
        disease='ncit:C2926'
    )
    assert len(response['statements']) > 1
    assert len(response['propositions']) > 1
    assert len(response['matches']['statements']) == 1
    assert len(response['matches']['propositions']) == 1

    civic_aid6_supported_by_statements = list()
    for s in response['statements']:
        if s['id'] == 'civic.aid:6':
            statement = s
        else:
            civic_aid6_supported_by_statements.append(s['id'])
    supported_by_statements = [s for s in statement['supported_by'] if
                               s.startswith('civic.eid:')]
    assert set(civic_aid6_supported_by_statements) == \
           set(supported_by_statements)

    response = await query_handler.search(
        disease='ncit:C2926',
        variation='ga4gh:VA.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA'
    )
    statement_ids = list()
    for s in response['statements']:
        if s['id'] == 'civic.aid:6':
            pass
        else:
            statement_ids.append(s['id'])
    for aid6_statement in civic_aid6_supported_by_statements:
        assert aid6_statement in statement_ids
    assert len(response['matches']['statements']) > 1
    assert len(response['matches']['propositions']) > 1


@pytest.mark.asyncio
async def test_civic_detail_flag_therapeutic(
    query_handler, civic_eid2997_statement, civic_eid2997_proposition, civic_vid33,
    civic_gid19, civic_did8, method1, pmid_23982599, civic_tid146, check_statement,
    check_proposition, check_variation_descriptor, check_descriptor, check_method,
    check_document
):
    """Test that detail flag works correctly for CIViC Therapeutic Response."""
    response = await query_handler.search(statement_id='civic.eid:2997', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = await query_handler.search(statement_id='civic.eid:2997', detail=True)
    assert_keys_for_detail_true(response.keys(), response)
    assert_response_items(response, civic_eid2997_statement,
                          civic_eid2997_proposition,
                          civic_vid33, civic_gid19, civic_did8,
                          method1, pmid_23982599, civic_tid146,
                          check_statement, check_proposition,
                          check_variation_descriptor,
                          check_descriptor, check_method, check_document
                          )


@pytest.mark.asyncio
async def test_civic_detail_flag_diagnostic(
    query_handler, civic_eid2_statement, civic_eid2_proposition, civic_vid99,
    civic_did2, civic_gid38, method1, pmid_15146165, check_statement, check_proposition,
    check_variation_descriptor, check_descriptor, check_method, check_document
):
    """Test that detail flag works correctly for CIViC Diagnostic Response."""
    response = await query_handler.search(statement_id='civic.eid:2', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = await query_handler.search(statement_id='civic.eid:2', detail=True)
    assert_keys_for_detail_true(response.keys(), response, tr_response=False)
    assert_response_items(response, civic_eid2_statement,
                          civic_eid2_proposition,
                          civic_vid99, civic_gid38, civic_did2,
                          method1, pmid_15146165, None, check_statement,
                          check_proposition, check_variation_descriptor,
                          check_descriptor, check_method, check_document)


@pytest.mark.asyncio
async def test_civic_detail_flag_prognostic(
    query_handler, civic_eid26_statement, civic_eid26_proposition, civic_vid65,
    civic_did3, civic_gid29, method1, pmid_16384925, check_statement, check_proposition,
    check_variation_descriptor, check_descriptor, check_method, check_document
):
    """Test that detail flag works correctly for CIViC Prognostic Response."""
    response = await query_handler.search(statement_id='civic.eid:26', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = await query_handler.search(statement_id='civic.eid:26', detail=True)
    assert_keys_for_detail_true(response.keys(), response, tr_response=False)
    assert_response_items(response, civic_eid26_statement,
                          civic_eid26_proposition,
                          civic_vid65, civic_gid29, civic_did3,
                          method1, pmid_16384925, None, check_statement,
                          check_proposition, check_variation_descriptor,
                          check_descriptor, check_method, check_document)


@pytest.mark.asyncio
async def test_moa_detail_flag(
    query_handler, moa_aid71_statement, moa_aid71_proposition, moa_vid67, moa_abl1,
    moa_imatinib, moa_chronic_myelogenous_leukemia, method4, pmid_11423618,
    check_statement, check_proposition, check_variation_descriptor, check_descriptor,
    check_method, check_document
):
    """Test that detail flag works correctly for MOA."""
    response = await query_handler.search(statement_id='moa.assertion:67', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = await query_handler.search(statement_id='moa.assertion:67', detail=True)
    assert_keys_for_detail_true(response.keys(), response)
    assert_response_items(response, moa_aid71_statement, moa_aid71_proposition,
                          moa_vid67, moa_abl1,
                          moa_chronic_myelogenous_leukemia, method4,
                          pmid_11423618, moa_imatinib, check_statement,
                          check_proposition, check_variation_descriptor,
                          check_descriptor, check_method, check_document)


@pytest.mark.asyncio
async def test_no_matches(query_handler):
    """Test invalid query matches."""
    # GA instead of VA
    response = await query_handler.search('ga4gh:GA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR')
    assert_no_match(response)

    # Invalid ID
    response = \
        await query_handler.search(disease='ncit:C292632425235321524352435623462')
    assert_no_match(response)

    # Empty query
    response = await query_handler.search(disease='')
    assert_no_match(response)

    response = await query_handler.search(gene='', therapy='', variation='', disease='')
    assert_no_match(response)
    assert response['warnings'] == ['No parameters were entered.']

    # Invalid variation
    response = await query_handler.search(variation='v600e')
    assert_no_match(response)

    response = query_handler.search_by_id('')
    assert_no_match_id(response)

    response = query_handler.search_by_id(' ')
    assert_no_match_id(response)

    response = query_handler.search_by_id('aid6')
    assert_no_match_id(response)

    response = query_handler.search_by_id('civc.assertion:6')
    assert_no_match_id(response)


def test_civic_id_search(query_handler, civic_eid2997_statement,
                         civic_vid33, civic_gid19, civic_tid146, civic_did8,
                         pmid_23982599, method1, check_statement,
                         check_variation_descriptor, check_descriptor,
                         check_method, check_document):
    """Test search on civic node id"""
    res = query_handler.search_by_id('civic.eid:2997')
    check_statement(res['statement'], civic_eid2997_statement)

    res = query_handler.search_by_id('civic.vid:33')
    check_variation_descriptor(res['variation_descriptor'], civic_vid33)

    res = query_handler.search_by_id('civic.gid:19')
    check_descriptor(res['gene_descriptor'], civic_gid19)

    res = query_handler.search_by_id('civic.tid:146')
    check_descriptor(res['therapy_descriptor'], civic_tid146)

    res = query_handler.search_by_id('civic.did:8')
    check_descriptor(res['disease_descriptor'], civic_did8)

    res = query_handler.search_by_id('pmid:23982599')
    check_document(res['document'], pmid_23982599)

    res = query_handler.search_by_id('method:1')
    check_method(res['method'], method1)


def test_moa_id_search(query_handler, moa_aid71_statement,
                       moa_vid67, moa_abl1, moa_imatinib,
                       moa_chronic_myelogenous_leukemia, pmid_11423618,
                       method4, check_statement, check_variation_descriptor,
                       check_descriptor, check_method, check_document):
    """Test search on moa node id"""
    res = query_handler.search_by_id('moa.assertion:67')
    check_statement(res['statement'], moa_aid71_statement)

    res = query_handler.search_by_id('moa.variant:71')
    check_variation_descriptor(res['variation_descriptor'], moa_vid67)

    res = query_handler.search_by_id('moa.normalize.gene:ABL1')
    check_descriptor(res['gene_descriptor'], moa_abl1)

    res = query_handler.search_by_id('moa.normalize.therapy:Imatinib')
    check_descriptor(res['therapy_descriptor'], moa_imatinib)

    res = query_handler.search_by_id('moa.normalize.disease:oncotree%3ACML')
    check_descriptor(res['disease_descriptor'],
                     moa_chronic_myelogenous_leukemia)

    res = query_handler.search_by_id('moa.normalize.disease:oncotree:CML')
    check_descriptor(res['disease_descriptor'],
                     moa_chronic_myelogenous_leukemia)

    res = query_handler.search_by_id('pmid:11423618')
    check_document(res['document'], pmid_11423618)

    res = query_handler.search_by_id(' method:4 ')
    check_method(res['method'], method4)


@pytest.mark.asyncio
async def test_service_meta(query_handler):
    """Test service meta in response"""
    def check_service_meta(response):
        """Check service meta in response is correct"""
        assert "service_meta_" in response
        service_meta_ = response["service_meta_"]
        assert service_meta_["name"] == "metakb"
        assert service_meta_["version"] == __version__
        assert service_meta_["last_updated"] == LAST_UPDATED
        assert service_meta_["url"] == \
               "https://github.com/cancervariants/metakb"

    statement_id = "civic.eid:2997"
    resp = await query_handler.search(statement_id=statement_id)
    check_service_meta(resp)

    resp = query_handler.search_by_id("method:4")
    check_service_meta(resp)

    resp = await query_handler.search_statements(statement_id=statement_id)
    check_service_meta(resp)
