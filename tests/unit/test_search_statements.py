"""Test the MetaKB search statements method"""
import copy

import pytest


@pytest.fixture(scope="module")
def civic_vid33_with_gene(civic_vid33, civic_gid19):
    """Create civic vid 33 test fixture"""
    vid33 = copy.deepcopy(civic_vid33)
    vid33["gene_context"] = civic_gid19
    return vid33


@pytest.fixture(scope="module")
def civic_eid2997(civic_eid2997_proposition, civic_vid33_with_gene,
                  civic_tid146, civic_did8, method1, pmid_23982599):
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
        "method": method1,
        "supported_by": [pmid_23982599]
    }


@pytest.fixture(scope="module")
def civic_aid6(civic_eid2997_proposition, civic_vid33_with_gene, civic_tid146,
               civic_did8, method2, civic_aid6_document):
    """Create test fixture for CIViC AID6"""
    return {
        "id": "civic.aid:6",
        "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved as a first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
        "direction": "supports",
        "evidence_level": "amp_asco_cap_2017_level:1A",
        "proposition": civic_eid2997_proposition,
        "variation_origin": "somatic",
        "variation_descriptor": civic_vid33_with_gene,
        "therapy_descriptor": civic_tid146,
        "disease_descriptor": civic_did8,
        "method": method2,
        "supported_by": [
            civic_aid6_document, "civic.eid:2997",
            "civic.eid:2629", "civic.eid:982",
            "civic.eid:968", "civic.eid:883",
            "civic.eid:879"
        ],
        "type": "Statement"
    }


@pytest.fixture(scope="module")
def moa_vid71_with_gene(moa_vid71, moa_abl1):
    """Create test fixture for MOA Variant 71 with gene descriptor"""
    vid71 = copy.deepcopy(moa_vid71)
    vid71["gene_context"] = moa_abl1
    return vid71


@pytest.fixture(scope="module")
def moa_aid71(moa_aid71_proposition, moa_vid71_with_gene, moa_imatinib,
              moa_chronic_myelogenous_leukemia, method4,
              pmid_11423618):
    """Create test fixture for MOA Assertion 71"""
    return {
        "id": "moa.assertion:71",
        "type": "Statement",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",  # noqa: E501
        "evidence_level": "moa.evidence_level:Preclinical",
        "proposition": moa_aid71_proposition,
        "variation_origin": "somatic",
        "variation_descriptor": moa_vid71_with_gene,
        "therapy_descriptor": moa_imatinib,
        "disease_descriptor": moa_chronic_myelogenous_leukemia,
        "method": method4,
        "supported_by": [pmid_11423618]
    }


@pytest.fixture(scope="module")
def oncokb_diagnostic1(
    oncokb_diagnostic_statement1, oncokb_diagnostic_proposition1, oncokb_braf_v600e_vd,
    oncokb_braf_gene_descriptor, oncokb_ecd_disease_descriptor, oncokb_method,
    oncokb_diagnostic1_documents
):
    """Create test fixture for OncoKB Diagnostic evidence for BRAF V600E"""
    vd = copy.deepcopy(oncokb_braf_v600e_vd)
    vd["gene_context"] = oncokb_braf_gene_descriptor
    return {
        "id": oncokb_diagnostic_statement1["id"],
        "type": "Statement",
        "evidence_level": oncokb_diagnostic_statement1["evidence_level"],
        "proposition": oncokb_diagnostic_proposition1,
        "variation_descriptor": vd,
        "disease_descriptor": oncokb_ecd_disease_descriptor,
        "method": oncokb_method,
        "supported_by": oncokb_diagnostic1_documents
    }


@pytest.fixture(scope="module")
def oncokb_therapeutic1(
    oncokb_therapeutic_statement1, oncokb_therapeutic_proposition1,
    oncokb_braf_v600e_vd, oncokb_braf_gene_descriptor, oncokb_mel_disease_descriptor,
    oncokb_trametinib_therapy_descriptor, oncokb_method,
    oncokb_therapeutic1_documents_query
):
    """Create test fixture for OncoKB Therapeutic evidence for BRAF V600E"""
    vd = copy.deepcopy(oncokb_braf_v600e_vd)
    vd["gene_context"] = oncokb_braf_gene_descriptor
    return {
        "id": oncokb_therapeutic_statement1["id"],
        "type": "Statement",
        "description": "Trametinib is an oral small molecule inhibitor of MEK1/2 that is FDA-approved alone or with dabrafenib for the treatment of patients with metastatic melanoma harboring a V600E or V600K BRAF mutation. In an open-label, randomized Phase III trial, patients with BRAF V600E/K-mutated unresectable, metastatic melanoma received oral trametinib (2 mg once daily) or an intravenous regimen of either dacarbazine (1000 mg/m2) or paclitaxel (175 mg/m2) every three weeks. Trametinib demonstrated improved progression-free survival (HR for disease progression or death = 0.45) and six-month overall survival (81% vs. 67%; death HR = 0.54; p=0.01) (PMID: 22663011). However, like other MEK inhibitors, the benefit of trametinib is limited by adverse reactions, most notably grade three or four rash and diarrhea (PMID: 22663011). Trametinib is not typically used as monotherapy for patients with BRAF V600K melanoma given its lower response rate compared to BRAF inhibitors and combined BRAF and MEK inhibitors. Patients previously treated with a RAF inhibitor appear to be less likely than untreated patients to respond to trametinib treatment (PMID: 22663011), and FDA guidelines state that trametinib as a monotherapy is not indicated for these patients. Dabrafenib and trametinib are FDA-approved as a combination therapy, which has superior clinical outcomes compared to dabrafenib or trametinib monotherapy (PMID: 25399551, 25265492). Additionally, patients with melanoma treated with dabrafenib and trametinib in both the neoadjuvant and adjuvant settings had improved survival over patients given standard of care (PMID: 29361468).",  # noqa: E501
        "evidence_level": oncokb_therapeutic_statement1["evidence_level"],
        "proposition": oncokb_therapeutic_proposition1,
        "variation_descriptor": vd,
        "disease_descriptor": oncokb_mel_disease_descriptor,
        "therapy_descriptor": oncokb_trametinib_therapy_descriptor,
        "method": oncokb_method,
        "supported_by": oncokb_therapeutic1_documents_query
    }


def assert_general_search_statements(response):
    """Check that general search statement queries return a valid response"""
    assert response["matches"]
    assert len(response["matches"]["propositions"]) > 0
    len_statement_matches = len(response["matches"]["statements"])
    assert len_statement_matches > 0
    len_statements = len(response["statements"])
    assert len_statements > 0
    assert len_statement_matches == len_statements


def assert_no_match(response):
    """No match assertions for queried concepts in search search statements."""
    assert response["statements"] == []
    assert len(response["matches"]["propositions"]) == 0
    assert len(response["matches"]["statements"]) == 0
    assert len(response["warnings"]) > 0


def check_statement_assertions(
        actual, test, check_proposition, check_variation_descriptor,
        check_descriptor, check_method):
    """Check that statement response is correct"""
    for key in {"id", "type", "evidence_level", "method"}:
        assert actual[key] == test[key], key

    for key in {"direction", "description", "variation_origin"}:
        if key in test.keys():
            assert actual[key] == test[key], key
        else:
            assert key not in actual.keys(), key

    check_proposition(actual["proposition"], test["proposition"])
    check_variation_descriptor(actual["variation_descriptor"],
                               test["variation_descriptor"],
                               check_descriptor=check_descriptor, nested=True)
    check_descriptor(actual["disease_descriptor"], test["disease_descriptor"])
    if test.get("therapy_descriptor"):
        check_descriptor(actual["therapy_descriptor"],
                         test["therapy_descriptor"])
    else:
        assert actual.get("therapy_descriptor") is None
    check_method(actual["method"], test["method"])
    assert len(actual["supported_by"]) == len(test["supported_by"])
    for sb in test["supported_by"]:
        assert sb in actual["supported_by"]


@pytest.mark.asyncio
async def test_civic_eid2997(
        query_handler, civic_eid2997, check_proposition,
        check_variation_descriptor, check_descriptor, check_method):
    """Test that search_statements works correctly for CIVIC EID2997"""
    resp = await query_handler.search_statements(statement_id="civic.eid:2997")
    assert len(resp["statements"]) == 1
    assert resp["matches"]["statements"] == ["civic.eid:2997"]
    assert len(resp["matches"]["propositions"]) == 1
    check_statement_assertions(
        resp["statements"][0], civic_eid2997, check_proposition,
        check_variation_descriptor, check_descriptor, check_method)
    assert resp["warnings"] == []


@pytest.mark.asyncio
async def test_civic_aid6(
        query_handler, civic_aid6, civic_eid2997, check_proposition,
        check_variation_descriptor, check_descriptor, check_method):
    """Test that search_statements works correctly for CIVIC EID2997"""
    resp = await query_handler.search_statements(statement_id="civic.aid:6")
    assert len(resp["statements"]) == 7
    assert resp["matches"]["statements"] == ["civic.aid:6"]
    assert len(resp["matches"]["propositions"]) == 1
    assert resp["warnings"] == []
    found_eid2997 = False
    found_aid6 = False

    for s in resp["statements"]:
        if s["id"] == "civic.eid:2997":
            check_statement_assertions(
                s, civic_eid2997, check_proposition,
                check_variation_descriptor, check_descriptor, check_method)
            found_eid2997 = True
        elif s["id"] == "civic.aid:6":
            check_statement_assertions(
                s, civic_aid6, check_proposition,
                check_variation_descriptor, check_descriptor, check_method)
            found_aid6 = True
    assert found_eid2997
    assert found_aid6


@pytest.mark.asyncio
async def test_moa(query_handler, moa_aid71, check_proposition,
                   check_variation_descriptor, check_descriptor, check_method):
    """Test that search_statements works correctly for MOA Assertion 71"""
    resp = await query_handler.search_statements(
        statement_id="moa.assertion:71")
    assert len(resp["statements"]) == 1
    check_statement_assertions(
        resp["statements"][0], moa_aid71, check_proposition,
        check_variation_descriptor, check_descriptor, check_method)
    assert resp["warnings"] == []


@pytest.mark.asyncio
async def test_oncokb_diagnostic(
    query_handler, oncokb_diagnostic1, check_proposition, check_variation_descriptor,
    check_descriptor, check_method
):
    """Test that search_statements works correctly for OncoKB Diagnostic evidence
    for BRAF V600E
    """
    resp = await query_handler.search_statements(
        statement_id=oncokb_diagnostic1["id"], variation="BRAF V600E")
    assert len(resp["statements"]) == 1
    check_statement_assertions(
        resp["statements"][0], oncokb_diagnostic1, check_proposition,
        check_variation_descriptor, check_descriptor, check_method)
    assert resp["warnings"] == []


@pytest.mark.asyncio
async def test_oncokb_therapeutic(
    query_handler, oncokb_therapeutic1, check_proposition, check_variation_descriptor,
    check_descriptor, check_method
):
    """Test that search_statements works correctly for OncoKB Therapeutic evidence
    for BRAF V600E
    """
    resp = await query_handler.search_statements(
        statement_id=oncokb_therapeutic1["id"], variation="BRAF V600E")
    assert len(resp["statements"]) == 1
    check_statement_assertions(
        resp["statements"][0], oncokb_therapeutic1, check_proposition,
        check_variation_descriptor, check_descriptor, check_method)
    assert resp["warnings"] == []


@pytest.mark.asyncio
async def test_general_search_statements(query_handler):
    """Test that queries do not return errors"""
    resp = await query_handler.search_statements(variation="BRAF V600E")
    assert_general_search_statements(resp)

    resp = await query_handler.search_statements(variation="EGFR L858R")
    assert_general_search_statements(resp)

    resp = await query_handler.search_statements(disease="cancer")
    assert_general_search_statements(resp)


@pytest.mark.asyncio
async def test_no_matches(query_handler):
    """Test invalid queries"""
    # invalid vrs variation prefix
    resp = await query_handler.search_statements(
        variation="ga4gh:variation.kgjrhgf84CEndyLjKdAO0RxN-e3pJjxA")
    assert_no_match(resp)

    # invalid id
    resp = await query_handler.search_statements(
        disease="ncit:C292632425235321524352435623462"
    )
    assert_no_match(resp)

    resp = await query_handler.search_statements(statement_id="civic:aid6")
    assert_no_match(resp)

    # empty query
    resp = await query_handler.search_statements(therapy="")
    assert_no_match(resp)
