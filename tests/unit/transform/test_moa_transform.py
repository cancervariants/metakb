"""Test MOA Transformation to common data model"""
import pytest
from metakb.transform.moa import MOATransform
from metakb import PROJECT_ROOT
import json
import os


@pytest.fixture(scope='module')
def data():
    """Create a MOA Transform test fixture."""
    moa = MOATransform(file_path=f"{PROJECT_ROOT}/tests/data/"
                                 f"transform/moa_harvester.json")
    moa.transform()
    moa._create_json(moa_dir=PROJECT_ROOT / 'tests' / 'data' / 'transform')
    with open(f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json", 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def asst69_statements():
    """Create assertion69 statements test fixture."""
    return [
        {
            "id": "moa:aid69",
            "description": "T315I mutant ABL1 in p210 BCR-ABL cells "
                           "resulted in retained high levels of "
                           "phosphotyrosine at increasing concentrations "
                           "of inhibitor STI-571, whereas wildtype "
                           "appropriately received inhibition.",
            "evidence_level": "moa.evidence_level:Preclinical",
            "proposition": "proposition:001",
            "variation_origin": "somatic",
            "variation_descriptor": "moa:vid69",
            "therapy_descriptor": "moa.normalize.therapy:Imatinib",
            "disease_descriptor": "moa.normalize.disease:oncotree%3ACML",  # noqa: E501
            "method": "method:004",
            "supported_by": [
                "pmid:11423618"
            ],
            "type": "Statement"
        }
    ]


@pytest.fixture(scope='module')
def asst69_propositions():
    """Create assertion69 propositions test fixture."""
    return [
        {
            "id": "proposition:001",
            "predicate": "predicts_resistance_to",
            "subject": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
            "object_qualifier": "ncit:C3174",
            "object": "rxcui:282388",
            "type": "therapeutic_response_proposition"
        }
    ]


@pytest.fixture(scope='module')
def asst69_variation_descriptors():
    """Create assertion69 variation_descriptors test fixture."""
    return [
        {
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
            "gene_context": "moa.normalize.gene:ABL1"
        }
    ]


@pytest.fixture(scope='module')
def asst69_gene_descriptors():
    """Create assertion69 gene_descriptors test fixture."""
    return [
        {
            "id": "moa.normalize.gene:ABL1",
            "type": "GeneDescriptor",
            "label": "ABL1",
            "value": {
                "id": "hgnc:76",
                "type": "Gene"
            }
        }
    ]


@pytest.fixture(scope='module')
def asst69_therapy_descriptors():
    """Create assertion69 therapy_descriptors test fixture."""
    return [
        {
            "id": "moa.normalize.therapy:Imatinib",
            "type": "TherapyDescriptor",
            "label": "Imatinib",
            "value": {
                "id": "rxcui:282388",
                "type": "Drug"
            }
        }
    ]


@pytest.fixture(scope='module')
def asst69_disease_descriptors():
    """Create assertion69 disease_descriptors test fixture."""
    return [
        {
            "id": "moa.normalize.disease:oncotree%3ACML",
            "type": "DiseaseDescriptor",
            "label": "Chronic Myelogenous Leukemia",
            "value": {
                "id": "ncit:C3174",
                "type": "Disease"
            }
        }
    ]


@pytest.fixture(scope='module')
def asst69_methods():
    """Create assertion69 methods test fixture."""
    return[
        {
            "id": "method:004",
            "label": "Clinical interpretation of integrative molecular "
                     "profiles to guide precision cancer medicine",
            "url": "https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1",  # noqa: E501
            "version": {
                "year": 2020,
                "month": 9,
                "day": 22
            },
            "authors": "Reardon, B., Moore, N.D., Moore, N. et al."
        }
    ]


@pytest.fixture(scope='module')
def asst69_documents():
    """Create assertion69 documents test fixture."""
    return[
        {
            "id": "pmid:11423618",
            "label": "Gorre, Mercedes E., et al. \"Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification.\" Science 293.5531 (2001): 876-880.",  # noqa: E501
            "xrefs": [
                "doi:10.1126/science.1062538"
            ]
        }
    ]


def assert_non_lists(actual, test):
    """Check assertions for non list types."""
    if isinstance(actual, dict):
        assertions(test, actual)
    else:
        assert test == actual


def assertions(test_data, actual_data):
    """Assert that test and actual data are the same."""
    if isinstance(actual_data, dict):
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(test_data[key]) == set(actual_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])
    elif isinstance(actual_data, list):
        for item in actual_data:
            if isinstance(item, list):
                assert set(test_data) == set(actual_data)
            else:
                assert_non_lists(actual_data, test_data)


def test_moa_cdm(data, asst69_statements, asst69_propositions,
                 asst69_variation_descriptors, asst69_gene_descriptors,
                 asst69_therapy_descriptors, asst69_disease_descriptors,
                 asst69_methods, asst69_documents):
    """Test that moa transform works correctly."""
    assertions(asst69_statements, data['statements'])
    assertions(asst69_propositions, data['propositions'])
    assertions(asst69_variation_descriptors, data['variation_descriptors'])
    assertions(asst69_gene_descriptors, data['gene_descriptors'])
    assertions(asst69_therapy_descriptors, data['therapy_descriptors'])
    assertions(asst69_disease_descriptors, data['disease_descriptors'])
    assertions(asst69_methods, data['methods'])
    assertions(asst69_documents, data['documents'])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json")
