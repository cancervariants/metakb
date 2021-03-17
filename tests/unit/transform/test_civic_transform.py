"""Test CIViC Transformation to common data model"""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json


@pytest.fixture(scope='module')
def data():
    """Create a CIViC Transform test fixture."""
    c = CIViCTransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/civic_harvester.json")
    transformations = c.transform()

    fn = f"{PROJECT_ROOT}/tests/data/transform/civic_cdm.json"

    with open(fn, 'w+') as f:
        json.dump(transformations, f)

    with open(fn, 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def eid2997():
    """Create EID2997 test fixture."""
    return {
        "evidence": [
            {
                "id": "civic:eid2997",
                "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
                "direction": "supports",
                "evidence_level": "civic.evidence_level:A",
                "proposition": "proposition:001",
                "variation_descriptor": "civic:vid33",
                "therapy_descriptor": "civic:tid146",
                "disease_descriptor": "civic:did8",
                "assertion_method": "assertion_method:001",
                "document": "document:001",
                "type": "Evidence"
            }
        ],
        "propositions": [
            {
                "_id": "proposition:001",
                "predicate": "predicts_sensitivity_to",
                "variation_origin": "somatic",
                "has_originating_context": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",  # noqa: E501
                "disease_context": "ncit:C2926",
                "therapy": "ncit:C66940",
                "type": "therapeutic_response_proposition"
            }
        ],
        "variation_descriptors": [
            {
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
                        "sequence_id": "ga4gh:SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",  # noqa: E501
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
                    "clinvar:376282",
                    "clinvar:16609",
                    "caid:CA126713",
                    "dbsnp:121434568"
                ],
                "alternate_labels": [
                    "LEU858ARG"
                ],
                "extensions": [
                    {
                        "name": "representative_variation_descriptor",
                        "value": "civic:vid33.rep",
                        "type": "Extension"
                    },
                    {
                        "name": "civic_actionability_score",
                        "value": "352.5",
                        "type": "Extension"
                    },
                    {
                        "name": "variant_groups",
                        "value": {},
                        "type": "Extension"
                    }
                ],
                "molecule_context": "protein",
                "structural_type": "SO:0001060",
                "expressions": [
                    {
                        "syntax": "hgvs:protein",
                        "value": "NP_005219.2:p.Leu858Arg",
                        "version": None,
                        "type": "Expression"
                    },
                    {
                        "syntax": "hgvs:transcript",
                        "value": "ENST00000275493.2:c.2573T>G",
                        "version": None,
                        "type": "Expression"
                    },
                    {
                        "syntax": "hgvs:transcript",
                        "value": "NM_005228.4:c.2573T>G",
                        "version": None,
                        "type": "Expression"
                    },
                    {
                        "syntax": "hgvs:genomic",
                        "value": "NC_000007.13:g.55259515T>G",
                        "version": None,
                        "type": "Expression"
                    }
                ],
                "ref_allele_seq": "L",
                "gene_context": "civic:gid19",
                "location_descriptor": None,
                "sequence_descriptor": None,
                "allelic_state": None
            }
        ],
        "therapy_descriptors": [
            {
                "id": "civic:tid146",
                "type": "TherapyDescriptor",
                "label": "Afatinib",
                "description": None,
                "value_id": None,
                "value": {
                    "therapy_id": "ncit:C66940",
                    "type": "Therapy"
                },
                "xrefs": None,
                "alternate_labels": [
                    "BIBW2992",
                    "BIBW 2992",
                    "(2e)-N-(4-(3-Chloro-4-Fluoroanilino)-7-(((3s)-Oxolan-3-yl)Oxy)Quinoxazolin-6-yl)-4-(Dimethylamino)But-2-Enamide"  # noqa: E501
                ],
                "extensions": None
            }
        ],
        "disease_descriptors": [
            {
                "id": "civic:did8",
                "type": "DiseaseDescriptor",
                "label": "Lung Non-small Cell Carcinoma",
                "description": None,
                "value_id": None,
                "value": {
                    "disease_id": "ncit:C2926",
                    "type": "Disease"
                },
                "xrefs": None,
                "alternate_labels": None,
                "extensions": None
            }
        ],
        "assertion_methods": [
            {
                "id": "assertion_method:001",
                "label": "Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
                "url": "https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x",  # noqa: E501
                "version": {
                    "year": 2019,
                    "month": 11,
                    "day": 29
                },
                "reference": "Danos, A.M., Krysiak, K., Barnell, E.K. et al."
            }
        ],
        "documents": [
            {
                "id": "document:001",
                "document_id": "pmid:23982599",
                "label": "Dungo et al., 2013, Drugs",
                "description": "Afatinib: first global approval.",
                "xrefs": []
            }
        ]
    }


@pytest.fixture(scope='module')
def aid6():
    """Create AID6 test fixture."""
    return {
        "assertion": [
            {
                "id": "civic:aid6",
                "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved, and is recommended (category 1) by NCCN guidelines along with erlotinib, gefitinib and osimertinib as first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
                "direction": "supports",
                "assertion_level": "civic.amp_level:tier_i_-_level_a",
                "proposition": "proposition:001",
                "assertion_methods": [
                    "assertion_method:002",
                    "assertion_method:003"
                ],
                "evidence": [
                    "civic:eid2997"
                ],
                "document": "document:002",
                "type": "Assertion"
            }
        ],
        "propositions": [
            {
                "_id": "proposition:001",
                "predicate": "predicts_sensitivity_to",
                "variation_origin": "somatic",
                "has_originating_context": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",  # noqa: E501
                "disease_context": "ncit:C2926",
                "therapy": "ncit:C66940",
                "type": "therapeutic_response_proposition"
            }
        ],
        "evidence": [
            "civic:eid2997"
        ],
        "assertion_methods": [
            {
                "id": "assertion_method:002",
                "label": "Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",  # noqa: E501
                "url": "https://pubmed.ncbi.nlm.nih.gov/27993330/",
                "version": {
                    "year": 2017,
                    "month": 1,
                    "day": None
                },
                "reference": "Li MM, Datto M, Duncavage EJ, et al."
            },
            {
                "id": "assertion_method:003",
                "label": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology",  # noqa: E501
                "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
                "version": {
                    "year": 2015,
                    "month": 5,
                    "day": None
                },
                "reference": "Richards S, Aziz N, Bale S, et al."
            }
        ],
        "documents": [
            {
                "id": "document:002",
                "document_id": None,
                "label": "Non-Small Cell Lung Cancer",
                "description": "NCCN Guideline Version: 3.2018",
                "xrefs": None
            }
        ]
    }


def assert_matching_key_values(test_data, actual_data):
    """Assert that test and actual data are the same."""
    assert list(test_data.keys()) == list(actual_data.keys())
    for key in actual_data.keys():
        if isinstance(key, list):
            assert set(test_data[key]) == set(actual_data[key])
        elif isinstance(key, dict):
            assert_matching_key_values(test_data[key], actual_data[key])
        else:
            assert test_data[key] == actual_data[key]


def test_eid2997(data, eid2997):
    """Test that transform is correct for EID2997."""
    eid2997_data = None
    evidence = 'evidence'
    for item in data:
        if evidence in list(item.keys())[0]:
            eid2997_data = item
            break

    for key in [evidence, 'propositions', 'variation_descriptors',
                'therapy_descriptors', 'disease_descriptors',
                'assertion_methods', 'documents']:
        assert len(eid2997_data[key]) == len(eid2997[key])
        assert_matching_key_values(eid2997_data[key][0],
                                   eid2997[key][0])


def test_aid6(data, aid6):
    """Test that transform is correct for AID6."""
    aid6_data = None
    assertion = 'assertion'
    for item in data:
        if assertion in list(item.keys())[0]:
            aid6_data = item
            break

    for key in [assertion, 'propositions', 'assertion_methods', 'documents']:
        assert len(aid6_data[key]) == len(aid6[key])
        assert_matching_key_values(aid6_data[key][0], aid6[key][0])
