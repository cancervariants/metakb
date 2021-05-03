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
                                 f"transform/diagnostic/civic_harvester.json")
    c.transform()
    c._create_json(
        civic_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform' / 'diagnostic'
    )
    with open(f"{PROJECT_ROOT}/tests/data/transform/"
              f"diagnostic/civic_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def statements():
    """Create test fixture for statements."""
    return [
        {
            "id": "civic:eid2",
            "description": "GIST tumors harboring PDGFRA D842V mutation are more likely to be benign than malignant.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "civic.evidence_level:B",
            "proposition": "proposition:001",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid99",
            "disease_descriptor": "civic:did2",
            "method": "method:001",
            "supported_by": ["pmid:15146165"],
            "type": "Statement"
        },
        {
            "id": "civic:eid74",
            "description": "In patients with medullary carcinoma, the presence of RET M918T mutation is associated with increased probability of lymph node metastases.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "civic.evidence_level:B",
            "proposition": "proposition:002",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid113",
            "disease_descriptor": "civic:did15",
            "method": "method:001",
            "supported_by": ["pmid:18073307"],
            "type": "Statement"
        },
        {
            "id": "civic:aid9",
            "description": "ACVR1 G328V mutations occur within the kinase domain, leading to activation of downstream signaling. Exclusively seen in high-grade pediatric gliomas, supporting diagnosis of diffuse intrinsic pontine glioma.",  # noqa: E501
            "direction": "supports",
            "evidence_level": "amp_asco_cap_2017_level:2C",
            "proposition": "proposition:003",
            "variation_origin": "somatic",
            "variation_descriptor": "civic:vid1686",
            "disease_descriptor": "civic:did2950",
            "method": "method:002",
            "supported_by": ["civic:eid4846", "civic:eid6955"],
            "type": "Statement"
        }
    ]


@pytest.fixture(scope='module')
def propositions():
    """Create test fixture for proposition."""
    return [
        {
            "id": "proposition:001",
            "predicate": "is_diagnostic_exclusion_criterion_for",
            "subject": "ga4gh:VA.3Yv7t0YzME9W4xErQf7-eFWtqvdfmjgt",
            "object_qualifier": "ncit:C3868",
            "type": "diagnostic_proposition"
        },
        {
            "id": "proposition:002",
            "predicate": "is_diagnostic_inclusion_criterion_for",
            "subject": "ga4gh:VA.ifPUeUiHj0TkYmimFK7T7jvbucAsGKqa",
            "object_qualifier": "ncit:C3879",
            "type": "diagnostic_proposition"
        },
        {
            "id": "proposition:003",
            "predicate": "is_diagnostic_inclusion_criterion_for",
            "subject": "ga4gh:VA.twWuxZk0p0Vn3NSkp0kwD1VgfNN2fvDm",
            "object_qualifier": "DOID:0080684",
            "type": "diagnostic_proposition"
        }
    ]


@pytest.fixture(scope='module')
def variation_descriptors():
    """Create test fixture for variants."""
    return [
        {
            "id": "civic:vid99",
            "type": "VariationDescriptor",
            "label": "D842V",
            "description": "PDGFRA D842 mutations are characterized broadly as imatinib resistance mutations. This is most well characterized in gastrointestinal stromal tumors, but other cell lines containing these mutations have been shown to be resistant as well. Exogenous expression of the A842V mutation resulted in constitutive tyrosine phosphorylation of PDGFRA in the absence of ligand in 293T cells and cytokine-independent proliferation of the IL-3-dependent Ba/F3 cell line, both evidence that this is an activating mutation. In imatinib resistant cell lines, a number of other therapeutics have demonstrated efficacy. These include; crenolanib, sirolimus, and midostaurin (PKC412).",  # noqa: E501
            "value_id": "ga4gh:VA.3Yv7t0YzME9W4xErQf7-eFWtqvdfmjgt",
            "value": {
                "location": {
                    "interval": {
                        "end": 842,
                        "start": 841,
                        "type": "SimpleInterval"
                    },
                    "sequence_id": "ga4gh:SQ.XpQn9sZLGv_GU3uiWO7YHq9-_alGjrVX",
                    "type": "SequenceLocation"
                },
                "state": {
                    "sequence": "V",
                    "type": "SequenceState"
                },
                "type": "Allele"
            },
            "xrefs": [
                "clinvar:13543",
                "caid:CA123194",
                "dbsnp:121908585"
            ],
            "alternate_labels": [
                "ASP842VAL"
            ],
            "extensions": [
                {
                    "name": "civic_representative_coordinate",
                    "value": {
                        "chromosome": "4",
                        "start": 55152093,
                        "stop": 55152093,
                        "reference_bases": "A",
                        "variant_bases": "T",
                        "representative_transcript": "ENST00000257290.5",
                        "ensembl_version": 75,
                        "reference_build": "GRCh37"
                    },
                    "type": "Extension"
                },
                {
                    "name": "civic_actionability_score",
                    "value": "100.5",
                    "type": "Extension"
                },
                {
                    "name": "variant_group",
                    "value": [
                        {
                            "id": "civic:vgid1",
                            "label": "Imatinib Resistance",
                            "description": "While imatinib has shown to be incredibly successful in treating philadelphia chromosome positive CML, patients that have shown primary or secondary resistance to the drug have been observed to harbor T315I and E255K ABL kinase domain mutations. These mutations, among others, have been observed both in primary refractory disease and acquired resistance. In gastrointestinal stromal tumors (GIST), PDGFRA 842 mutations have also been shown to confer resistance to imatinib. ",  # noqa: E501
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
                    "value": "NM_006206.4:c.2525A>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_006197.1:p.Asp842Val",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000257290.5:c.2525A>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000004.11:g.55152093A>T",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid38"
        },
        {
            "id": "civic:vid113",
            "type": "VariationDescriptor",
            "label": "M918T",
            "description": "RET M819T is the most common somatically acquired mutation in medullary thyroid cancer (MTC). While there currently are no RET-specific inhibiting agents, promiscuous kinase inhibitors have seen some success in treating RET overactivity. Data suggests however, that the M918T mutation may lead to drug resistance, especially against the VEGFR-inhibitor motesanib. It has also been suggested that RET M819T leads to more aggressive MTC with a poorer prognosis.",  # noqa: E501
            "value_id": "ga4gh:VA.ifPUeUiHj0TkYmimFK7T7jvbucAsGKqa",
            "value": {
                "location": {
                    "interval": {
                        "end": 918,
                        "start": 917,
                        "type": "SimpleInterval"
                    },
                    "sequence_id": "ga4gh:SQ.jMu9-ItXSycQsm4hyABeW_UfSNRXRVnl",
                    "type": "SequenceLocation"
                },
                "state": {
                    "sequence": "T",
                    "type": "SequenceState"
                },
                "type": "Allele"
            },
            "xrefs": [
                "clinvar:13919",
                "caid:CA009082",
                "dbsnp:74799832"
            ],
            "alternate_labels": [
                "MET918THR"
            ],
            "extensions": [
                {
                    "name": "civic_representative_coordinate",
                    "value": {
                        "chromosome": "10",
                        "start": 43617416,
                        "stop": 43617416,
                        "reference_bases": "T",
                        "variant_bases": "C",
                        "representative_transcript": "ENST00000355710.3",
                        "ensembl_version": 75,
                        "reference_build": "GRCh37"
                    },
                    "type": "Extension"
                },
                {
                    "name": "civic_actionability_score",
                    "value": "86",
                    "type": "Extension"
                },
                {
                    "name": "variant_group",
                    "value": [
                        {
                            "id": "civic:vgid6",
                            "label": "Motesanib Resistance",
                            "description": "RET activation is a common oncogenic marker of medullary thyroid carcinoma. Treatment of these patients with the targeted therapeutic motesanib has shown to be effective. However, the missense mutations C634W and M918T have shown to confer motesanib resistance in cell lines. ",  # noqa: E501
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
                    "value": "NM_020975.4:c.2753T>C",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_065681.1:p.Met918Thr",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000355710.3:c.2753T>C",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000010.10:g.43617416T>C",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid42"
        },
        {
            "id": "civic:vid1686",
            "type": "VariationDescriptor",
            "label": "G328V",
            "value_id": "ga4gh:VA.twWuxZk0p0Vn3NSkp0kwD1VgfNN2fvDm",
            "value": {
                "location": {
                    "interval": {
                        "end": 328,
                        "start": 327,
                        "type": "SimpleInterval"
                    },
                    "sequence_id": "ga4gh:SQ.6CnHhDq_bDCsuIBf0AzxtKq_lXYM7f0m",
                    "type": "SequenceLocation"
                },
                "state": {
                    "sequence": "V",
                    "type": "SequenceState"
                },
                "type": "Allele"
            },
            "xrefs": [
                "clinvar:376363",
                "caid:CA16602802",
                "dbsnp:387906589"
            ],
            "alternate_labels": [
                "GLY328VAL"
            ],
            "extensions": [
                {
                    "name": "civic_representative_coordinate",
                    "value": {
                        "chromosome": "2",
                        "start": 158622516,
                        "stop": 158622516,
                        "reference_bases": "C",
                        "variant_bases": "A",
                        "representative_transcript": "ENST00000434821.1",
                        "ensembl_version": 75,
                        "reference_build": "GRCh37"
                    },
                    "type": "Extension"
                },
                {
                    "name": "civic_actionability_score",
                    "value": "30",
                    "type": "Extension"
                },
                {
                    "name": "variant_group",
                    "value": [
                        {
                            "id": "civic:vgid23",
                            "label": "ACVR1 kinase domain mutation",
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
                    "value": "NM_001105.4:c.983G>T",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:protein",
                    "value": "NP_001096.1:p.Gly328Val",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:genomic",
                    "value": "NC_000002.11:g.158622516C>A",
                    "type": "Expression"
                },
                {
                    "syntax": "hgvs:transcript",
                    "value": "ENST00000434821.1:c.983G>T",
                    "type": "Expression"
                }
            ],
            "gene_context": "civic:gid154"
        }
    ]


@pytest.fixture(scope='module')
def disease_descriptors():
    """Create test fixture for disease descriptors."""
    return [
        {
            "id": "civic:did2",
            "type": "DiseaseDescriptor",
            "label": "Gastrointestinal Stromal Tumor",
            "value": {
                "id": "ncit:C3868",
                "type": "Disease"
            }
        },
        {
            "id": "civic:did15",
            "type": "DiseaseDescriptor",
            "label": "Thyroid Gland Medullary Carcinoma",
            "value": {
                "id": "ncit:C3879",
                "type": "Disease"
            }
        },
        {
            "id": "civic:did2950",
            "type": "DiseaseDescriptor",
            "label": "Diffuse Midline Glioma, H3 K27M-mutant",
            "value": {
                "id": "DOID:0080684",
                "type": "Disease"
            }
        }
    ]


@pytest.fixture(scope='module')
def gene_descriptors():
    """Create test fixture for gene descriptors."""
    return [
        {
            "id": "civic:gid38",
            "type": "GeneDescriptor",
            "label": "PDGFRA",
            "description": "Commonly mutated in GI tract tumors, PDGFR family genes (mutually exclusive to KIT mutations) are a hallmark of gastrointestinal stromal tumors. Gene fusions involving the PDGFRA kinase domain are highly correlated with eosinophilia, and the WHO classifies myeloid and lymphoid neoplasms with these characteristics as a distinct disorder. Mutations in the 842 region of PDGFRA have been often found to confer resistance to the tyrosine kinase inhibitor, imatinib.",  # noqa: E501
            "value": {
                "id": "hgnc:8803",
                "type": "Gene"
            },
            "alternate_labels": [
                "PDGFRA",
                "PDGFR2",
                "PDGFR-2",
                "CD140A"
            ]
        },
        {
            "id": "civic:gid42",
            "type": "GeneDescriptor",
            "label": "RET",
            "description": "RET mutations and the RET fusion RET-PTC lead to activation of this tyrosine kinase receptor and are associated with thyroid cancers. RET point mutations are the most common mutations identified in medullary thyroid cancer (MTC) with germline and somatic mutations in RET associated with hereditary and sporadic forms, respectively. The most common somatic form mutation is M918T (exon 16) and a variety of other mutations effecting exons 10, 11 and 15 have been described. The prognostic significance of these mutations have been hotly debated in the field, however, data suggests that some RET mutation may confer drug resistence. No RET-specific agents are currently clinically available but several promiscuous kinase inhibitors that target RET, among others, have been approved for MTC treatment.",  # noqa: E501
            "value": {
                "id": "hgnc:9967",
                "type": "Gene"
            },
            "alternate_labels": [
                "RET",
                "RET-ELE1",
                "PTC",
                "MTC1",
                "MEN2B",
                "MEN2A",
                "HSCR1",
                "CDHR16",
                "CDHF12"
            ]
        },
        {
            "id": "civic:gid154",
            "type": "GeneDescriptor",
            "label": "ACVR1",
            "value": {
                "id": "hgnc:171",
                "type": "Gene"
            },
            "alternate_labels": [
                "ACVR1",
                "TSRI",
                "SKR1",
                "FOP",
                "ALK2",
                "ACVRLK2",
                "ACVR1A",
                "ACTRI"
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
            "id": "pmid:15146165",
            "label": "Lasota et al., 2004, Lab. Invest.",
            "description": "A great majority of GISTs with PDGFRA mutations represent gastric tumors of low or no malignant potential."  # noqa: E501
        },
        {
            "id": "pmid:18073307",
            "label": "Elisei et al., 2008, J. Clin. Endocrinol. Metab.",
            "description": "Prognostic significance of somatic RET oncogene mutations in sporadic medullary thyroid cancer: a 10-year follow-up study."  # noqa: E501
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

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/diagnostic/civic_cdm.json")
