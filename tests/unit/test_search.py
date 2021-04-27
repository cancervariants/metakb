"""Test the MetaKB search method."""
from metakb.query import QueryHandler
import pytest
import collections

# TODO:
#  Commented out tests to be fixed after first pass
#  Load DB with test data


@pytest.fixture(scope='module')
def query_handler():
    """Create query handler test fixture."""
    class QueryGetter:

        def __init__(self):
            self.query_handler = QueryHandler()

        def search(self, variation='', disease='', therapy='', gene='',
                   statement_id='', detail=False):
            response = self.query_handler.search(variation=variation,
                                                 disease=disease,
                                                 therapy=therapy, gene=gene,
                                                 statement_id=statement_id,
                                                 detail=detail)
            return response

        def search_by_id(self, node_id=''):
            response = self.query_handler.search_by_id(node_id=node_id)

            return response
    return QueryGetter()


@pytest.fixture(scope='module')
def civic_eid2997():
    """Create CIVIC EID2997 Statement test fixture."""
    return {
        "id": "civic:eid2997",
        "type": "Statement",
        "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
        "direction": "supports",
        "variation_origin": "somatic",
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
        "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
        "object_qualifier": "ncit:C2926",
        "object": "rxcui:1430438",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def civic_vid33():
    """Create a test fixture for CIViC VID33."""
    return {
        "id": "civic:vid33",
        "type": "VariationDescriptor",
        "label": "L858R",
        "description": "EGFR L858R has long been recognized as a functionally significant mutation in cancer, and is one of the most prevalent single mutations in lung cancer. Best described in non-small cell lung cancer (NSCLC), the mutation seems to confer sensitivity to first and second generation TKI's like gefitinib and neratinib. NSCLC patients with this mutation treated with TKI's show increased overall and progression-free survival, as compared to chemotherapy alone. Third generation TKI's are currently in clinical trials that specifically focus on mutant forms of EGFR, a few of which have shown efficacy in treating patients that failed to respond to earlier generation TKI therapies.",  # noqa: E501
        "value_id": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
        "value": {
            "location": {
                "interval": {
                    "end": 858,
                    "start": 857,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "R",
                "type": "SequenceState"
            },
            "type": "Allele"
        },
        "xrefs": [
            "clinvar:376280",
            "clinvar:16609",
            "clinvar:376282",
            "caid:CA126713",
            "dbsnp:121434568"
        ],
        "alternate_labels": [
            "LEU858ARG"
        ],
        "extensions": [
            {
                "name": "civic_representative_coordinate",
                "value": {
                    "chromosome": "7",
                    "start": 55259515,
                    "stop": 55259515,
                    "reference_bases": "T",
                    "variant_bases": "G",
                    "representative_transcript": "ENST00000275493.2",
                    "ensembl_version": 75,
                    "reference_build": "GRCh37"
                },
                "type": "Extension"
            },
            {
                "name": "civic_actionability_score",
                "value": "375",
                "type": "Extension"
            }
        ],
        "molecule_context": "protein",
        "structural_type": "SO:0001060",
        "expressions": [
            {
                "syntax": "hgvs:genomic",
                "value": "NC_000007.13:g.55259515T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:protein",
                "value": "NP_005219.2:p.Leu858Arg",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "NM_005228.4:c.2573T>G",
                "type": "Expression"
            },
            {
                "syntax": "hgvs:transcript",
                "value": "ENST00000275493.2:c.2573T>G",
                "type": "Expression"
            }
        ],
        "ref_allele_seq": "L",
        "gene_context": "civic:gid19"
    }


@pytest.fixture(scope='module')
def civic_gid19():
    """Create test fixture for CIViC GID19."""
    return {
        "id": "civic:gid19",
        "type": "GeneDescriptor",
        "label": "EGFR",
        "description": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. \nOverproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",  # noqa: E501
        "value": {
            "id": "hgnc:3236",
            "type": "Gene"
        },
        "alternate_labels": [
            "ERRP",
            "EGFR",
            "mENA",
            "PIG61",
            "NISBD2",
            "HER1",
            "ERBB1",
            "ERBB"
        ]
    }


@pytest.fixture(scope='module')
def civic_tid146():
    """Create test fixture for CIViC TID146."""
    return {
        "id": "civic:tid146",
        "type": "TherapyDescriptor",
        "label": "Afatinib",
        "value": {
            "id": "rxcui:1430438",
            "type": "Drug"
        },
        "alternate_labels": [
            "BIBW2992",
            "BIBW 2992",
            "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide"  # noqa: E501
        ]
    }


@pytest.fixture(scope='module')
def civic_did8():
    """Create test fixture for CIViC DID8."""
    return {
        "id": "civic:did8",
        "type": "DiseaseDescriptor",
        "label": "Lung Non-small Cell Carcinoma",
        "value": {
            "id": "ncit:C2926",
            "type": "Disease"
        }
    }


@pytest.fixture(scope='module')
def method001():
    """Create test fixture for method:001."""
    return {
        "id": "method:001",
        "label": "Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
        "url": "https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x",  # noqa: E501
        "version": {
            "year": 2019,
            "month": 11,
            "day": 29
        },
        "authors": "Danos, A.M., Krysiak, K., Barnell, E.K. et al."
    }


@pytest.fixture(scope='module')
def eid2997_document():
    """Create test fixture for CIViC EID2997 document."""
    return {
        "id": "pmid:23982599",
        "label": "Dungo et al., 2013, Drugs",
        "description": "Afatinib: first global approval."
    }


@pytest.fixture(scope='module')
def eid1409_proposition():
    """Create test fixture for EID1409 proposition."""
    return {
        "id": "proposition:701",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.9dA0egRAIfVFDL1sdU1VP7HsBcG0-DtE",
        "object_qualifier": "ncit:C3510",
        "object": "rxcui:1147220",
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
        "proposition": "proposition:701",
        "variation_origin": "somatic",
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
        "evidence_level": "amp_asco_cap_2017_level:1A",
        "direction": "supports",
        "variation_origin": "somatic",
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


@pytest.fixture(scope='module')
def moa_aid69():
    """Create a MOA Statement 69 test fixture."""
    return {
        "id": "moa:aid69",
        "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",  # noqa: E501
        "evidence_level": "moa.evidence_level:Preclinical",
        "proposition": "proposition:001",
        "variation_origin": "somatic",
        "variation_descriptor": "moa:vid69",
        "therapy_descriptor": "moa.normalize.therapy:Imatinib",
        "disease_descriptor": "moa.normalize.disease:oncotree%3ACML",
        "method": "method:004",
        "supported_by": [
            "pmid:11423618"
        ],
        "type": "Statement"
    }


@pytest.fixture(scope='module')
def aid69_proposition():
    """Create a test fixture for MOA AID69 proposition."""
    return {
        "id": "proposition:001",
        "predicate": "predicts_resistance_to",
        "subject": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
        "object_qualifier": "ncit:C3174",
        "object": "rxcui:282388",
        "type": "therapeutic_response_proposition"
    }


@pytest.fixture(scope='module')
def moa_vid69():
    """Create a test fixture for MOA VID69."""
    return {
        "id": "moa:vid69",
        "type": "VariationDescriptor",
        "label": "ABL1 p.T315I (Missense)",
        "value_id": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
        "value": {
            "location": {
                "interval": {
                    "end": 315,
                    "start": 314,
                    "type": "SimpleInterval"
                },
                "sequence_id": "ga4gh:SQ.dmFigTG-0fY6I54swb7PoDuxCeT6O3Wg",
                "type": "SequenceLocation"
            },
            "state": {
                "sequence": "I",
                "type": "SequenceState"
            },
            "type": "Allele"
        },
        "extensions": [
            {
                "name": "moa_representative_coordinate",
                "value": {
                    "chromosome": "9",
                    "start_position": "133747580.0",
                    "end_position": "133747580.0",
                    "reference_allele": "C",
                    "alternate_allele": "T",
                    "cdna_change": "c.944C>T",
                    "protein_change": "p.T315I",
                    "exon": "5.0"
                },
                "type": "Extension"
            }
        ],
        "molecule_context": "protein",
        "structural_type": "SO:0001606",
        "ref_allele_seq": "T",
        "gene_context": "moa.normalize.gene:ABL1",
        "expressions": [],
    }


@pytest.fixture(scope='module')
def moa_abl1():
    """Create a test fixture for MOA ABL1 Gene Descriptor."""
    return {
        "id": "moa.normalize.gene:ABL1",
        "type": "GeneDescriptor",
        "label": "ABL1",
        "value": {
            "id": "hgnc:76",
            "type": "Gene"
        }
    }


@pytest.fixture(scope='module')
def moa_imatinib():
    """Create a test fixture for MOA Imatinib Therapy Descriptor."""
    return {
        "id": "moa.normalize.therapy:Imatinib",
        "type": "TherapyDescriptor",
        "label": "Imatinib",
        "value": {
            "id": "rxcui:282388",
            "type": "Drug"
        }
    }


@pytest.fixture(scope='module')
def moa_chronic_myelogenous_leukemia():
    """Create test fixture for MOA Chronic Myelogenous Leukemia Descriptor."""
    return {
        "id": "moa.normalize.disease:oncotree%3ACML",
        "type": "DiseaseDescriptor",
        "label": "Chronic Myelogenous Leukemia",
        "value": {
            "id": "ncit:C3174",
            "type": "Disease"
        }
    }


@pytest.fixture(scope='module')
def method004():
    """Create a test fixture for MOA method:004."""
    return {
        "id": "method:004",
        "label": "Clinical interpretation of integrative molecular profiles to guide precision cancer medicine",  # noqa: E501
        "url": "https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1",
        "version": {
            "year": 2020,
            "month": 9,
            "day": 22
        },
        "authors": "Reardon, B., Moore, N.D., Moore, N. et al."
    }


@pytest.fixture(scope='module')
def moa_aid69_document():
    """Create a test fixture for MOA AID69 document."""
    return {
        "id": "pmid:11423618",
        "label": "Gorre, Mercedes E., et al. \"Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification.\" Science 293.5531 (2001): 876-880.",  # noqa: E501
        "xrefs": [
            "doi:10.1126/science.1062538"
        ]
    }


def assert_same_keys_list_items(actual, test):
    """Assert that keys in a dict are same or items in list are same."""
    assert len(list(actual)) == len(list(test))
    if isinstance(actual, collections.abc.KeysView):
        for item in list(actual):
            assert item in test
    else:
        for i in range(len(list(actual))):
            assertions(test[i], actual[i])


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        if isinstance(actual, str):
            if test.startswith('proposition:'):
                assert actual.startswith('proposition:')
            else:
                assert actual == test
        else:
            assert actual == test


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        assert_same_keys_list_items(actual_data.keys(), test_data.keys())
        for key in actual_data.keys():
            if key == 'supported_by':
                assert_same_keys_list_items(actual_data[key], test_data[key])
            elif isinstance(actual_data[key], list):
                if key == 'extensions' or key == 'expressions':
                    assertions(test_data[key], actual_data[key])
                else:
                    try:
                        assert set(actual_data[key]) == set(test_data[key])
                    except:  # noqa: E722
                        assertions(test_data[key], actual_data[key])
            else:
                if key == 'proposition':
                    assert test_data[key].startswith('proposition:')
                    assert actual_data[key].startswith('proposition:')
                else:
                    assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        assert_same_keys_list_items(actual_data, test_data)
        for item in actual_data:
            if isinstance(item, list):
                assert set(actual_data) == set(test_data)
            else:
                assert_non_lists(actual_data, test_data)


def return_response(query_handler, statement_id, **kwargs):
    """Return the statement given ID if it exists."""
    response = query_handler.search(**kwargs)
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
    """No match assertions for queried concepts."""
    assert response['statements'] == []
    assert response['propositions'] == []
    assert len(response['warnings']) > 0


def assert_keys_for_detail_false(response_keys):
    """Check that keys aren't in response when detail is false."""
    assert 'variation_descriptors' not in response_keys
    assert 'gene_descriptors' not in response_keys
    assert 'therapy_descriptors' not in response_keys
    assert 'disease_descriptors' not in response_keys
    assert 'methods' not in response_keys
    assert 'documents' not in response_keys


def assert_keys_for_detail_true(response_keys, response, is_evidence=True):
    """Check that keys are in response when detail is false."""
    fields = ['variation_descriptors', 'gene_descriptors',
              'therapy_descriptors', 'disease_descriptors', 'methods',
              'documents', 'statements', 'propositions']
    for field in fields:
        assert field in response_keys
        if is_evidence:
            # Evidence only does not have supported_by with other statements
            assert len(response[field]) == 1
        else:
            assert len(response[field]) > 1


def assert_response_items(response, statement, proposition,
                          variation_descriptor, gene_descriptor,
                          therapy_descriptor, disease_descriptor, method,
                          document):
    """Check that search response match expected values."""
    assert_keys_for_detail_true(response.keys(), response)

    response_statement = response['statements'][0]
    response_proposition = response['propositions'][0]
    response_variation_descriptor = response['variation_descriptors'][0]
    response_gene_descriptor = response['gene_descriptors'][0]
    response_therapy_descriptor = response['therapy_descriptors'][0]
    response_disease_descriptor = response['disease_descriptors'][0]
    response_method = response['methods'][0]
    response_document = response['documents'][0]

    assertions(statement, response_statement)
    assertions(proposition, response_proposition)
    assertions(variation_descriptor, response_variation_descriptor)
    assertions(gene_descriptor, response_gene_descriptor)
    assertions(therapy_descriptor, response_therapy_descriptor)
    assertions(disease_descriptor, response_disease_descriptor)
    assertions(method, response_method)
    assertions(document, response_document)

    # Assert that IDs match in response items
    assert response_statement['proposition'] == response_proposition['id']
    assert response_statement['variation_descriptor'] == \
           response_variation_descriptor['id']
    assert response_statement['therapy_descriptor'] == \
           response_therapy_descriptor['id']
    assert response_statement['disease_descriptor'] == \
           response_disease_descriptor['id']
    assert response_statement['method'] == response_method['id']
    assert response_statement['supported_by'][0] == response_document['id']

    assert proposition['subject'] == response_variation_descriptor['value_id']
    assert proposition['object_qualifier'] == \
           response_disease_descriptor['value']['id']
    assert proposition['object'] == response_therapy_descriptor['value']['id']

    assert response_variation_descriptor['gene_context'] == \
           response_gene_descriptor['id']


def test_civic_eid2997(query_handler, civic_eid2997, eid2997_proposition):
    """Test search on CIViC Evidence Item 2997."""
    statement_id = 'civic:eid2997'

    # Test search by Subject
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR')  # noqa: E501
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Object
    s, p = return_response(query_handler, statement_id,
                           therapy='rxcui:1430438')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Object Qualifier
    s, p = return_response(query_handler, statement_id, disease='ncit:C2926')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = return_response(query_handler, statement_id, gene='hgnc:3236')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Label
    s, p = return_response(query_handler, statement_id, gene='EGFR')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Alt label
    s, p = return_response(query_handler, statement_id, gene='ERBB1')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = return_response(query_handler, statement_id, variation='EGFR L858R')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Sequence ID
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE')  # noqa: E501
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Alt Label
    s, p = return_response(query_handler, statement_id,
                           variation='egfr Leu858ARG')
    assertions(civic_eid2997, s)

    # HGVS Expression
    s, p = return_response(query_handler, statement_id,
                           variation='NP_005219.2:p.Leu858Arg')  # noqa: E501
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Therapy Descriptor
    # Label
    s, p = return_response(query_handler, statement_id, therapy='Afatinib')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Alt Label
    s, p = return_response(query_handler, statement_id, therapy='BIBW2992')
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)

    # Test search by Disease Descriptor
    # Label
    s, p = return_response(query_handler, statement_id,
                           disease='Lung Non-small Cell Carcinoma')  # noqa: E501
    assertions(civic_eid2997, s)
    assertions(eid2997_proposition, p)


def test_civic_eid1409(query_handler, civic_eid1409):
    """Test search on CIViC Evidence Item 1409."""
    statement_id = 'civic:eid1409'

    # Test search by Subject
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:VA.9dA0egRAIfVFDL1sdU1VP7HsBcG0-DtE')  # noqa: E501
    assertions(civic_eid1409, s)

    # Test search by Object
    s, p = return_response(query_handler, statement_id, therapy='ncit:C64768')
    assertions(civic_eid1409, s)

    # Test search by Object Qualifier
    s, p = return_response(query_handler, statement_id, disease='ncit:C3510')
    assertions(civic_eid1409, s)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = return_response(query_handler, statement_id, gene='hgnc:1097')
    assertions(civic_eid1409, s)

    # Label
    s, p = return_response(query_handler, statement_id, gene='BRAF')
    assertions(civic_eid1409, s)

    # TODO: Not found in gene normalizer
    # # Alt label
    # s, p = return_response(query_handler,
    # statement_id, gene='NS7')
    # assertions(civic_eid1409, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = return_response(query_handler, statement_id,
                           variation='BRAF V600E')
    assertions(civic_eid1409, s)

    # Sequence ID
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:SQ.WaAJ_cXXn9YpMNfhcq9lnzIvaB9ALawo')  # noqa: E501
    assertions(civic_eid1409, s)

    # # Alt Label
    s, p = return_response(query_handler, statement_id,
                           variation='braf val600glu')
    assertions(civic_eid1409, s)

    # HGVS Expression
    s, p = return_response(query_handler, statement_id,
                           variation='NP_004324.2:p.Val600Glu')  # noqa: E501
    assertions(civic_eid1409, s)

    # Test search by Therapy Descriptor
    # Label
    s, p = return_response(query_handler, statement_id, therapy='Vemurafenib')
    assertions(civic_eid1409, s)

    # # Alt Label
    s, p = return_response(query_handler, statement_id,
                           therapy='BRAF(V600E) Kinase Inhibitor RO5185426')
    assertions(civic_eid1409, s)

    # Label
    s, p = return_response(query_handler, statement_id,
                           disease='Skin Melanoma')
    assertions(civic_eid1409, s)


def test_civic_aid6(query_handler, civic_aid6):
    """Test search on CIViC Evidence Item 6."""
    statement_id = 'civic:aid6'

    # Test search by Subject
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR')  # noqa: E501
    assertions(civic_aid6, s)

    # Test search by Object
    s, p = return_response(query_handler, statement_id,
                           therapy='rxcui:1430438')
    assertions(civic_aid6, s)

    # Test search by Object Qualifier
    s, p = return_response(query_handler, statement_id, disease='ncit:C2926')
    assertions(civic_aid6, s)

    # Test search by Gene Descriptor
    # HGNC ID
    s, p = return_response(query_handler, statement_id, gene='hgnc:3236')
    assertions(civic_aid6, s)

    # Label
    s, p = return_response(query_handler, statement_id, gene='EGFR')
    assertions(civic_aid6, s)

    # Alt label
    s, p = return_response(query_handler, statement_id, gene='ERBB1')
    assertions(civic_aid6, s)

    # Test search by Variation Descriptor
    # Gene Symbol + Variant Name
    s, p = return_response(query_handler, statement_id, variation='EGFR L858R')
    assertions(civic_aid6, s)

    # Sequence ID
    s, p = return_response(query_handler, statement_id,
                           variation='ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE')  # noqa: E501
    assertions(civic_aid6, s)

    # Alt Label
    s, p = return_response(query_handler, statement_id,
                           variation='egfr leu858arg')
    assertions(civic_aid6, s)

    # HGVS Expression
    s, p = return_response(query_handler, statement_id,
                           variation='NP_005219.2:p.leu858arg')  # Noqa: E501
    assertions(civic_aid6, s)

    # Label
    s, p = return_response(query_handler, statement_id, therapy='afatinib')
    assertions(civic_aid6, s)

    # Alt Label
    s, p = return_response(query_handler, statement_id, therapy='BIBW 2992')
    assertions(civic_aid6, s)

    # Label
    s, p = return_response(query_handler, statement_id,
                           disease='Lung Non-small Cell Carcinoma    ')  # noqa: E501
    assertions(civic_aid6, s)


def test_multiple_parameters(query_handler):
    """Test that multiple parameter searches work correctly."""
    # Test no match
    response = query_handler.search(variation=' braf v600e', gene='egfr',
                                    disease='cancer', therapy='cisplatin')
    assert_no_match(response)

    response = query_handler.search(therapy='cisplatin', disease='4dfadfafas')
    assert_no_match(response)

    # Test EID2997 queries
    object_qualifier = 'ncit:C2926'
    subject = 'ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR'
    object = 'rxcui:1430438'
    response = query_handler.search(
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
    response = query_handler.search(
        variation='NP_005219.2:p.Leu858Arg',
        disease='NSCLC',
        therapy='Afatinib',
        gene='braf'
    )
    assert_no_match(response)

    # Test eid1409 queries
    object_qualifier = 'ncit:C3510'
    subject = 'ga4gh:VA.9dA0egRAIfVFDL1sdU1VP7HsBcG0-DtE'
    response = query_handler.search(
        variation=subject,
        disease='malignant trunk melanoma'
    )
    for p in response['propositions']:
        if p['id'] in response['matches']['propositions']:
            assert p['object_qualifier'] == object_qualifier
            assert p['subject'] == subject
            assert p['object']

    # No Match for statement ID
    response = query_handler.search(
        variation=subject,
        disease='malignant trunk melanoma',
        statement_id='civic:eid2997'
    )
    assert_no_match(response)

    # CIViC EID2997
    response = query_handler.search(
        statement_id='civiC:eid2997',
        variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR'
    )
    assert len(response['statements']) == 1
    assert len(response['propositions']) == 1
    assert len(response['matches']['statements']) == 1
    assert len(response['matches']['propositions']) == 1

    # CIViC AID6
    response = query_handler.search(
        statement_id='CIViC:AID6',
        variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR',
        disease='ncit:C2926'
    )
    assert len(response['statements']) > 1
    assert len(response['propositions']) > 1
    assert len(response['matches']['statements']) == 1
    assert len(response['matches']['propositions']) == 1

    civic_aid6_supported_by_statements = list()
    for s in response['statements']:
        if s['id'] == 'civic:aid6':
            statement = s
        else:
            civic_aid6_supported_by_statements.append(s['id'])
    supported_by_statements = \
        [s for s in statement['supported_by'] if s.startswith('civic:eid')]
    assert set(civic_aid6_supported_by_statements) == \
           set(supported_by_statements)

    response = query_handler.search(
        disease='ncit:C2926',
        variation='ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR'
    )
    statement_ids = list()
    for s in response['statements']:
        if s['id'] == 'civic:aid6':
            pass
        else:
            statement_ids.append(s['id'])
    for aid6_statement in civic_aid6_supported_by_statements:
        assert aid6_statement in statement_ids
    assert len(response['matches']['statements']) > 1
    assert len(response['matches']['propositions']) > 1


def test_civic_detail_flag(query_handler, civic_eid2997, eid2997_proposition,
                           civic_vid33, civic_gid19, civic_tid146, civic_did8,
                           method001, eid2997_document):
    """Test that detail flag works correctly for CIViC."""
    response = query_handler.search(statement_id='civic:eid2997', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = query_handler.search(statement_id='civic:eid2997', detail=True)
    assert_keys_for_detail_true(response.keys(), response)
    assert_response_items(response, civic_eid2997, eid2997_proposition,
                          civic_vid33, civic_gid19, civic_tid146, civic_did8,
                          method001, eid2997_document)


def test_moa_detail_flag(query_handler, moa_aid69, aid69_proposition,
                         moa_vid69, moa_abl1, moa_imatinib,
                         moa_chronic_myelogenous_leukemia, method004,
                         moa_aid69_document):
    """Test that detail flag works correctly for MOA."""
    response = query_handler.search(statement_id='moa:aid69', detail=False)
    assert_keys_for_detail_false(response.keys())

    response = query_handler.search(statement_id='moa:aid69', detail=True)
    assert_keys_for_detail_true(response.keys(), response)
    assert_response_items(response, moa_aid69, aid69_proposition,
                          moa_vid69, moa_abl1, moa_imatinib,
                          moa_chronic_myelogenous_leukemia,
                          method004, moa_aid69_document)


def test_no_matches(query_handler):
    """Test invalid query matches."""
    # GA instead of VA
    response = query_handler.search('ga4gh:GA.WyOqFMhc8a'
                                    'OnMFgdY0uM7nSLNqxVPAiR')
    assert_no_match(response)

    # Invalid ID
    response = \
        query_handler.search(disease='ncit:C292632425235321524352435623462')
    assert_no_match(response)

    # Empty query
    response = query_handler.search(disease='')
    assert_no_match(response)

    response = query_handler.search(gene='', therapy='', variation='',
                                    disease='')
    assert_no_match(response)
    assert response['warnings'] == ['No parameters were entered.']

    # Invalid variation
    response = query_handler.search(variation='v600e')
    assert_no_match(response)


def test_civic_id_search(query_handler, civic_vid33, civic_gid19,
                         civic_tid146, civic_did8,
                         eid2997_document, method001):
    """Test search on civic node id"""
    res = query_handler.search_by_id(node_id='civic:vid33')
    res = res['variation_descriptor']
    assertions(civic_vid33, res)

    res = query_handler.search_by_id(node_id='civic:gid19')
    res = res['gene_descriptor']
    assertions(civic_gid19, res)

    res = query_handler.search_by_id(node_id='civic:tid146')
    res = res['therapy_descriptor']
    assertions(civic_tid146, res)

    res = query_handler.search_by_id(node_id='civic:did8')
    res = res['disease_descriptor']
    assertions(civic_did8, res)

    res = query_handler.search_by_id(node_id='pmid:23982599')
    res = res['document']
    assertions(eid2997_document, res)

    res = query_handler.search_by_id(node_id='method:001')
    res = res['method']
    assertions(method001, res)


def test_moa_id_search(query_handler, moa_vid69, moa_abl1, moa_imatinib,
                       moa_chronic_myelogenous_leukemia,
                       moa_aid69_document, method004):
    """Test search on moa node id"""
    res = query_handler.search_by_id(node_id='moa:vid69')
    res = res['variation_descriptor']
    assertions(moa_vid69, res)

    res = query_handler.search_by_id(node_id='moa.normalize.gene:ABL1')
    res = res['gene_descriptor']
    assertions(moa_abl1, res)

    res = query_handler.search_by_id(node_id='moa.normalize.therapy:Imatinib')
    res = res['therapy_descriptor']
    assertions(moa_imatinib, res)

    res = query_handler.search_by_id(node_id='moa.normalize.disease:oncotree%3ACML')  # noqa: E501
    res = res['disease_descriptor']
    assertions(moa_chronic_myelogenous_leukemia, res)

    res = query_handler.search_by_id(node_id='pmid:11423618')
    res = res['document']
    assertions(moa_aid69_document, res)

    res = query_handler.search_by_id(node_id='method:004')
    res = res['method']
    assertions(method004, res)
