"""Test CIViC Transformation to common data model for prognostic."""
import pytest
from metakb.transform.civic import CIViCTransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a CIViC Transform test fixture."""
    c = CIViCTransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/prognostic/civic_harvester.json")
    c.transform()
    c._create_json(
        civic_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'prognostic'
    )
    with open(f"{PROJECT_ROOT}/tests/data/transform/"
              f"prognostic/civic_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def statements():
    """Create test fixture for statements."""
    return [
        {
            "id": "civic:eid26",
            "description": "In acute myloid leukemia patients, D816 mutation is associated with earlier relapse and poorer prognosis than wildtype KIT.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "civic.evidence_level:B",
            "proposition": "proposition:001",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid65",
            "disease_descriptor": "civic:did3",
            "method": "method:001",
            "supported_by": ["pmid:16384925"],
            "type": "Statement"
        },
        {
            "id": "civic:eid1756",
            "description": "Study of 1817 PCa cases and 2026 cancer free controls to clarify the association of (MTHFR)c.677C>T  (and c.1298A>C ) of pancreatic cancer risk in a population of Han Chinese in Shanghai.  Results indicated a lower risk for the heterozygous CT genotype and homozygous TT genotype carriers of (MTHFR)c.677C>T  which had a significantly lower risk of developing pancreatic cancer compared with the wild-type CC genotype.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "civic.evidence_level:B",
            "proposition": "proposition:002",
            "variation_origin": "germline",
            "variation_descriptor": "civic:vid258",
            "disease_descriptor": "civic:did556",
            "method": "method:001",
            "supported_by": ["pmid:27819322"],
            "type": "Statement"
        }
    ]


@pytest.fixture(scope='module')
def propositions():
    """Create test fixture for proposition."""
    return [
        {
            "id": "proposition:001",
            "predicate": "is_prognostic_of_worse_outcome_for",
            "subject": "ga4gh:VA.EGLm8XWH3V17-VZw7vEygPmy4wHQ8mCf",
            "object_qualifier": "ncit:C3171",
            "type": "prognostic_proposition"
        },
        {
            "id": "proposition:002",
            "predicate": "is_prognostic_of_better_outcome_for",
            "subject": "ga4gh:VA.V5IUMLhaM8Oo-oAClUZqb-gDPaIzIi-A",
            "object_qualifier": "ncit:C9005",
            "type": "prognostic_proposition"
        }
    ]


@pytest.fixture(scope='module')
def variation_descriptors():
    """Create test fixture for variants."""
    return [
        {
            "id": "civic:vid65",
            "type": "VariationDescriptor",
            "label": "D816V",
            "description": "KIT D816V is a mutation observed in acute myeloid leukemia (AML). This variant has been linked to poorer prognosis and worse outcome in AML patients.",  # noqa: E501
            "value_id": "ga4gh:VA.EGLm8XWH3V17-VZw7vEygPmy4wHQ8mCf",
            "value": {
                "location": {
                    "interval": {
                        "end": 816,
                        "start": 815,
                        "type": "SimpleInterval"
                    },
                    "sequence_id": "ga4gh:SQ.TcMVFj5kDODDWpiy1d_1-3_gOf4BYaAB",
                    "type": "SequenceLocation"
                },
                "state": {
                    "sequence": "V",
                    "type": "SequenceState"
                },
                "type": "Allele"
            },
            "xrefs": [
                "clinvar:13852",
                "caid:CA123513",
                "dbsnp:121913507"
            ],
            "alternate_labels": [
                "ASP816VAL"
            ],
            "extensions": [
                {
                    "name": "civic_representative_coordinate",
                    "value": {
                        "chromosome": "4",
                        "start": 55599321,
                        "stop": 55599321,
                        "reference_bases": "A",
                        "variant_bases": "T",
                        "representative_transcript": "ENST00000288135.5",
                        "ensembl_version": 75,
                        "reference_build": "GRCh37"
                    },
                    "type": "Extension"
                },
                {
                    "name": "civic_actionability_score",
                    "value": "67",
                    "type": "Extension"
                },
                {
                    "name": "variant_group",
                    "value": [
                        {
                            "id": "civic:vgid2",
                            "label": "KIT Exon 17",
                            'type': 'variant_group'
                        }
                    ],
                    "type": "Extension"
                }
            ],
            "structural_type": "SO:0001583",
            "expressions": [
                {
                    "syntax": "hgvs:transcript",
                    "value": "NM_000222.2:c.2447A>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_000213.1:p.Asp816Val",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000288135.5:c.2447A>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000004.11:g.55599321A>T",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid29"
        },
        {
            "id": "civic:vid258",
            "type": "VariationDescriptor",
            "label": "A222V",
            "value_id": "ga4gh:VA.V5IUMLhaM8Oo-oAClUZqb-gDPaIzIi-A",
            "value": {
                "location": {
                    "interval": {
                        "end": 222,
                        "start": 221,
                        "type": "SimpleInterval"
                    },
                    "sequence_id": "ga4gh:SQ.4RSETawLfMkNpQBPepa7Uf9ItHAEJUde",
                    "type": "SequenceLocation"
                },
                "state": {
                    "sequence": "V",
                    "type": "SequenceState"
                },
                "type": "Allele"
            },
            "xrefs": [
                "clinvar:3520",
                "caid:CA170990",
                "dbsnp:1801133"
            ],
            "alternate_labels": [
                "C677T",
                "ALA222VAL"
            ],
            "extensions": [
                {
                    "name": "civic_representative_coordinate",
                    "value": {
                        "chromosome": "1",
                        "start": 11856378,
                        "stop": 11856378,
                        "reference_bases": "G",
                        "variant_bases": "A",
                        "representative_transcript": "ENST00000376592.1",
                        "ensembl_version": 75,
                        "reference_build": "GRCh37"
                    },
                    "type": "Extension"
                },
                {
                    "name": "civic_actionability_score",
                    "value": "55",
                    "type": "Extension"
                }
            ],
            "structural_type": "SO:0001583",
            "expressions": [
                {
                    "syntax": "hgvs:transcript",
                    "value": "NM_005957.4:c.665C>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_005948.3:p.Ala222Val",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000376592.1:c.665G>A",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000001.10:g.11856378G>A",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid3672"
        }
    ]


@pytest.fixture(scope='module')
def disease_descriptors():
    """Create test fixture for disease descriptors."""
    return [
        {
            "id": "civic:did3",
            "type": "DiseaseDescriptor",
            "label": "Acute Myeloid Leukemia",
            "value": {
                "id": "ncit:C3171",
                "type": "Disease"
            }
        },
        {
            "id": "civic:did556",
            "type": "DiseaseDescriptor",
            "label": "Pancreatic Cancer",
            "value": {
                "id": "ncit:C9005",
                "type": "Disease"
            }
        }
    ]


@pytest.fixture(scope='module')
def gene_descriptors():
    """Create test fixture for gene descriptors."""
    return [
        {
            "id": "civic:gid29",
            "type": "GeneDescriptor",
            "label": "KIT",
            "description": "c-KIT activation has been shown to have oncogenic activity in gastrointestinal stromal tumors (GISTs), melanomas, lung cancer, and other tumor types. The targeted therapeutics nilotinib and sunitinib have shown efficacy in treating KIT overactive patients, and are in late-stage trials in melanoma and GIST. KIT overactivity can be the result of many genomic events from genomic amplification to overexpression to missense mutations. Missense mutations have been shown to be key players in mediating clinical response and acquired resistance in patients being treated with these targeted therapeutics.",  # noqa: E501
            "value": {
                "id": "hgnc:6342",
                "type": "Gene"
            },
            "alternate_labels": [
                "MASTC",
                "KIT",
                "SCFR",
                "PBT",
                "CD117",
                "C-Kit"
            ]
        },
        {
            "id": "civic:gid3672",
            "type": "GeneDescriptor",
            "label": "MTHFR",
            "value": {
                "id": "hgnc:7436",
                "type": "Gene"
            },
            "alternate_labels": [
                "MTHFR"
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
            "id": "pmid:16384925",
            "label": "Cairoli et al., 2006, Blood",
            "description": "Prognostic impact of c-KIT mutations in core binding factor leukemias: an Italian retrospective study."  # noqa: E501
        },
        {
            "id": "pmid:27819322",
            "label": "Wu et al., 2016, Sci Rep",
            "description": "MTHFR c.677C>T Inhibits Cell Proliferation and Decreases Prostate Cancer Susceptibility in the Han Chinese Population in Shanghai.",  # noqa: E501
            "xrefs": ["pmc:PMC5098242"]
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
                   gene_descriptors, disease_descriptors, methods, documents):
    """Test that civic transform works correctly."""
    assertions(statements, data['statements'])
    assertions(propositions, data['propositions'])
    assertions(variation_descriptors, data['variation_descriptors'])
    assertions(gene_descriptors, data['gene_descriptors'])
    assertions(disease_descriptors, data['disease_descriptors'])
    assertions(methods, data['methods'])
    assertions(documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/prognostic/civic_cdm.json")
