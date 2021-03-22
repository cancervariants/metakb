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
    transformations = moa.transform()

    fn = f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json"

    with open(fn, 'w+') as f:
        json.dump(transformations, f)

    with open(fn, 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='module')
def asst69():
    """Create assertion69 test fixture."""
    return {
        "evidence": [
            {
                "id": "moa:69",
                "description": "T315I mutant ABL1 in p210 BCR-ABL cells resulted in retained high levels of phosphotyrosine at increasing concentrations of inhibitor STI-571, whereas wildtype appropriately received inhibition.",  # noqa: E501
                "direction": None,
                "evidence_level": "moa.evidence_level:Preclinical",
                "proposition": "proposition:001",
                "variation_descriptor": "moa:vid69",
                "therapy_descriptor": "normalize:Imatinib",
                "disease_descriptor": "normalize:CML",
                "method": "method:004",
                "document": "document:001",
                "type": "Evidence"
            }
        ],
        "propositions": [
            {
                "_id": "proposition:001",
                "predicate": "predicts_resistance_to",
                "variation_origin": None,
                "has_originating_context": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",  # noqa: E501
                "disease_context": "ncit:C3174",
                "therapy": "ncit:C62035",
                "type": "therapeutic_response_proposition"
            }
        ],
        "variation_descriptors": [
            {
                "id": "moa:vid69",
                "type": "VariationDescriptor",
                "label": "ABL1 p.T315I (Missense)",
                "description": None,
                "value_id": "ga4gh:VA.wVNOLHSUDotkavwqtSiPW1aWxJln3VMG",
                "value": {
                    "location": {
                        "interval": {
                            "end": 315,
                            "start": 314,
                            "type": "SimpleInterval"
                        },
                        "sequence_id": "ga4gh:SQ.dmFigTG-0fY6I54swb7PoDuxCeT6O3Wg",  # noqa: E501
                        "type": "SequenceLocation"
                    },
                    "state": {
                        "sequence": "I",
                        "type": "SequenceState"
                    },
                    "type": "Allele"
                },
                "xrefs": None,
                "alternate_labels": None,
                "extensions": None,
                "molecule_context": "protein",
                "structural_type": "SO:0001606",
                "expressions": None,
                "ref_allele_seq": "T",
                "gene_context": "moa:['normalize:ABL1']"
            }
        ],
        "gene_descriptors": [
            {
                "id": "normalize:ABL1",
                "type": "GeneDescriptor",
                "label": "ABL1",
                "description": None,
                "value_id": None,
                "value": {
                    "gene_id": "hgnc:76",
                    "type": "Gene"
                },
                "xrefs": None,
                "alternate_labels": None,
                "extensions": None
            }
        ],
        "therapy_descriptors": [
            {
                "id": "normalize:Imatinib",
                "type": "TherapyDescriptor",
                "label": "Imatinib",
                "description": None,
                "value_id": None,
                "value": {
                    "therapy_id": "ncit:C62035",
                    "type": "Therapy"
                },
                "xrefs": None,
                "alternate_labels": None,
                "extensions": None
            }
        ],
        "disease_descriptors": [
            {
                "id": "normalize:CML",
                "type": "DiseaseDescriptor",
                "label": "Chronic Myelogenous Leukemia",
                "description": None,
                "value_id": None,
                "value": {
                    "disease_id": "ncit:C3174",
                    "type": "Disease"
                },
                "xrefs": None,
                "alternate_labels": None,
                "extensions": None
            }
        ],
        "methods": [
            {
                "id": "method:004",
                "label": "Clinical interpretation of integrative molecular profiles to guide precision cancer medicine",  # noqa: E501
                "url": "https://www.biorxiv.org/content/10.1101/2020.09.22.308833v1",  # noqa: E501
                "version": {
                    "year": 2020,
                    "month": 9,
                    "day": 22
                },
                "reference": "Reardon, B., Moore, N.D., Moore, N. et al."
            }
        ],
        "documents": [
            {
                "id": "document:001",
                "document_id": "pmid:11423618",
                "label": "Gorre, Mercedes E., et al. \"Clinical resistance to STI-571 cancer therapy caused by BCR-ABL gene mutation or amplification.\" Science 293.5531 (2001): 876-880.",  # noqa: E501
                "description": None,
                "xrefs": None
            }
        ]
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
        assert_same_keys_list_items(test_data.keys(), actual_data.keys())
        for key in actual_data.keys():
            if isinstance(actual_data[key], list):
                try:
                    assert set(test_data[key]) == set(actual_data[key])
                except:  # noqa: E722
                    assertions(test_data[key], actual_data[key])
            else:
                assert_non_lists(actual_data[key], test_data[key])


def test_asst69(data, asst69):
    """Test that transform is correct for assertion69."""
    asst69_data = None
    for item in data:
        if 'evidence' in list(item.keys())[0]:
            asst69_data = item
            break

    asst69_data_keys = asst69_data.keys()

    for key in asst69.keys():
        assert key in asst69_data_keys
        assert len(asst69_data[key]) == len(asst69[key])
        assertions(asst69_data[key][0], asst69[key][0])

    os.remove(f"{PROJECT_ROOT}/tests/data/transform/moa_cdm.json")
