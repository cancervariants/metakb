"""Test CIViC Transformation to common data model for Therapeutic Response."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a CIViC Transform test fixture."""
    c = CIViCTransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/therapeutic/civic_harvester.json")
    c.transform()
    c._create_json(
        civic_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'therapeutic'
    )
    with open(f"{PROJECT_ROOT}/tests/data/transform/"
              f"therapeutic/civic_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def statements():
    """Create test fixture for statements."""
    return [
        {
            "id": "civic:eid2997",
            "description": "Afatinib, an irreversible inhibitor of the ErbB family of tyrosine kinases has been approved in the US for the first-line treatment of patients with metastatic non-small-cell lung cancer (NSCLC) who have tumours with EGFR exon 19 deletions or exon 21 (L858R) substitution mutations as detected by a US FDA-approved test",  # noqa: E501
            "direction": "supports",
            "evidence_level": "civic.evidence_level:A",
            "proposition": "proposition:001",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid33",
            "therapy_descriptor": "civic:tid146",
            "disease_descriptor": "civic:did8",
            "method": "method:001",
            "supported_by": ["pmid:23982599"],
            "type": "Statement"
        },
        {
            "id": "civic:aid6",
            "description": "L858R is among the most common sensitizing EGFR mutations in NSCLC, and is assessed via DNA mutational analysis, including Sanger sequencing and next generation sequencing methods. Tyrosine kinase inhibitor afatinib is FDA approved, and is recommended (category 1) by NCCN guidelines along with erlotinib, gefitinib and osimertinib as first line systemic therapy in NSCLC with sensitizing EGFR mutation.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "amp_asco_cap_2017_level:1A",
            "proposition": "proposition:001",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid33",
            "therapy_descriptor": "civic:tid146",
            "disease_descriptor": "civic:did8",
            "method": "method:002",
            "supported_by": ["document:001", "civic:eid2997", "civic:eid2629",
                             "civic:eid982", "civic:eid968", "civic:eid883",
                             "civic:eid879"],
            "type": "Statement"
        }
    ]


@pytest.fixture(scope='module')
def propositions():
    """Create test fixture for proposition."""
    return [
        {
            "id": "proposition:001",
            "predicate": "predicts_sensitivity_to",
            "subject": "ga4gh:VA.WyOqFMhc8aOnMFgdY0uM7nSLNqxVPAiR",
            "object_qualifier": "ncit:C2926",
            "object": "rxcui:1430438",
            "type": "therapeutic_response_proposition"
        }
    ]


@pytest.fixture(scope='module')
def variation_descriptors():
    """Create test fixture for variants."""
    return [
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
                    "value": "352.5",
                    "type": "Extension"
                }
            ],
            "structural_type": "SO:0001583",
            "expressions": [
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_005219.2:p.Leu858Arg",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000275493.2:c.2573T>G",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "NM_005228.4:c.2573T>G",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000007.13:g.55259515T>G",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid19"
        }
    ]


@pytest.fixture(scope='module')
def therapy_descriptors():
    """Create test fixture for therapy descriptors."""
    return [
        {
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
    ]


@pytest.fixture(scope='module')
def disease_descriptors():
    """Create test fixture for disease descriptors."""
    return [
        {
            "id": "civic:did8",
            "type": "DiseaseDescriptor",
            "label": "Lung Non-small Cell Carcinoma",
            "value": {
                "id": "ncit:C2926",
                "type": "Disease"
            }
        }
    ]


@pytest.fixture(scope='module')
def gene_descriptors():
    """Create test fixture for gene descriptors."""
    return [
        {
            "id": "civic:gid19",
            "type": "GeneDescriptor",
            "label": "EGFR",
            "description": "EGFR is widely recognized for its importance in cancer. Amplification and mutations have been shown to be driving events in many cancer types. Its role in non-small cell lung cancer, glioblastoma and basal-like breast cancers has spurred many research and drug development efforts. Tyrosine kinase inhibitors have shown efficacy in EGFR amplfied tumors, most notably gefitinib and erlotinib. Mutations in EGFR have been shown to confer resistance to these drugs, particularly the variant T790M, which has been functionally characterized as a resistance marker for both of these drugs. The later generation TKI's have seen some success in treating these resistant cases, and targeted sequencing of the EGFR locus has become a common practice in treatment of non-small cell lung cancer. \n"  # noqa:E501
                           "Overproduction of ligands is another possible mechanism of activation of EGFR. ERBB ligands include EGF, TGF-a, AREG, EPG, BTC, HB-EGF, EPR and NRG1-4 (for detailed information please refer to the respective ligand section).",  # noqa: E501
            "value": {
                "id": "hgnc:3236",
                "type": "Gene"
            },
            "alternate_labels": [
                "EGFR",
                "mENA",
                "PIG61",
                "NISBD2",
                "HER1",
                "ERBB1",
                "ERBB"
            ]
        }
    ]


@pytest.fixture(scope='module')
def methods():
    """Create test fixture for methods."""
    return [
        {
            "id": "method:001",
            "label": "Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
            "url": "https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-019-0687-x",  # noqa: E501
            "version": {
                "year": 2019,
                "month": 11,
                "day": 29
            },
            "authors": "Danos, A.M., Krysiak, K., Barnell, E.K. et al."
        },
        {
            "id": "method:002",
            "label": "Standards and Guidelines for the Interpretation and Reporting of Sequence Variants in Cancer: A Joint Consensus Recommendation of the Association for Molecular Pathology, American Society of Clinical Oncology, and College of American Pathologists",  # noqa: E501
            "url": "https://pubmed.ncbi.nlm.nih.gov/27993330/",
            "version": {
                "year": 2017,
                "month": 1
            },
            "authors": "Li MM, Datto M, Duncavage EJ, et al."
        },
        {
            "id": "method:003",
            "label": "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology",  # noqa: E501
            "url": "https://pubmed.ncbi.nlm.nih.gov/25741868/",
            "version": {
                "year": 2015,
                "month": 5
            },
            "authors": "Richards S, Aziz N, Bale S, et al."
        }
    ]


@pytest.fixture(scope='module')
def documents():
    """Create test fixture for documents."""
    return [
        {
            "id": "pmid:23982599",
            "label": "Dungo et al., 2013, Drugs",
            "description": "Afatinib: first global approval."
        },
        {
            "id": "document:001",
            "document_id": "https://www.nccn.org/professionals/"
                           "physician_gls/default.aspx",
            "label": "NCCN Guidelines: Non-Small Cell "
                     "Lung Cancer version 3.2018"
        }
    ]


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        assert actual == test


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(actual_data[key]) == set(test_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        for item in actual_data:
            if isinstance(item, list):
                assert set(actual_data) == set(test_data)
            else:
                assert_non_lists(actual_data, test_data)


def test_civic_cdm(data, statements, propositions, variation_descriptors,
                   gene_descriptors, therapy_descriptors, disease_descriptors,
                   methods, documents):
    """Test that civic transform works correctly."""
    assertions(statements, data['statements'])
    assertions(propositions, data['propositions'])
    assertions(variation_descriptors, data['variation_descriptors'])
    assertions(gene_descriptors, data['gene_descriptors'])
    assertions(therapy_descriptors, data['therapy_descriptors'])
    assertions(disease_descriptors, data['disease_descriptors'])
    assertions(methods, data['methods'])
    assertions(documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/therapeutic/"
              f"civic_cdm.json")
