"""Test MOA Transformation to common data model for therapeutic collection"""
import json

import pytest
import pytest_asyncio

from metakb import PROJECT_ROOT  # noqa: I202
from metakb.transform.moa import MOATransform


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic_collection"
FILENAME = "moa_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a MOA Transform test fixture."""
    harvester_path = DATA_DIR / "moa_harvester.json"
    moa = MOATransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await moa.transform()
    moa.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def moa_source62():
    """Create test fixture for MOA Source 62"""
    return {
        "id": "moa.source:62",
        "extensions": [
            {"name": "source_url", "value": "https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf", "type": "Extension"},  # noqa: E501
            {"name": "source_type", "value": "FDA", "type": "Extension"}
        ],
        "title": "Array BioPharma Inc. Braftovi (encorafenib) [package insert]. U.S. Food and Drug Administration website. www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf. Revised April 2020. Accessed October 15, 2020.",  # noqa: E501
        "type": "Document"
    }


@pytest.fixture(scope="module")
def moa_aid159_statement(method4, moa_source62):
    """Create MOAlmanac Assertion 159 Statement test fixture"""
    return {
        "id": "moa.assertion:159",
        "type": "VariationNeoplasmTherapeuticResponseStatement",
        "description": "The U.S. Food and Drug Administration (FDA) granted regular approval to encorafenib in combination with cetuximab for the treatment of adult patients with metastatic colorectal cancer (CRC) with BRAF V600E mutation, as detected by an FDA-approved test, after prior therapy.",  # noqa: E501
        "evidence_level": {
            "id": "vicc:e00002",
            "label": "FDA recognized evidence",
            "type": "Coding"
        },
        "target_proposition": "proposition:LgtRmnYf3XjmswInlRuVpAknqjqL7Mz2",
        "variation_origin": "somatic",
        "subject_descriptor": "moa.variant:149",
        "object_descriptor": "moa.tcd:zBda4sO3iQLExj5SB8VTPzPLaPoWefiP",
        "neoplasm_type_descriptor": "moa.normalize.disease:oncotree%3ACOADREAD",
        "specified_by": method4,
        "is_reported_in": [moa_source62]
    }


@pytest.fixture(scope="module")
def moa_aid159_proposition():
    """Create MOA Assertion 159 Proposition test fixture"""
    return {
        "id": "proposition:LgtRmnYf3XjmswInlRuVpAknqjqL7Mz2",
        "type": "VariationNeoplasmTherapeuticResponseProposition",
        "predicate": "predicts_sensitivity_to",
        "subject": "ga4gh:VA.h313H4CQh6pogbbSJ3H5pI1cPoh9YMm_",
        "neoplasm_type_qualifier": {"id": "ncit:C5105", "type": "Disease"},
        "object": {
            "type": "CombinationTherapeutics",
            "members": [
                {"id": "rxcui:318341", "type": "Therapeutic"},
                {"id": "rxcui:2049106", "type": "Therapeutic"}
            ]
        }
    }


@pytest.fixture(scope="module")
def moa_vid149(braf_v600e_variation):
    """Create test fixture for MOA variant 149"""
    return {
        "id": "moa.variant:149",
        "type": "VariationDescriptor",
        "label": "BRAF p.V600E (Missense)",
        "variation": braf_v600e_variation,
        "extensions": [
            {
                "name": "moa_representative_coordinate",
                "type": "Extension",
                "value": {
                    "chromosome": "7",
                    "start_position": "140453136",
                    "end_position": "140453136",
                    "reference_allele": "A",
                    "alternate_allele": "T",
                    "cdna_change": "c.1799T>A",
                    "protein_change": "p.V600E",
                    "exon": "15",
                }
            }
        ],
        "xrefs": ["dbsnp:113488022"],
        "vrs_ref_allele_seq": "V",
        "gene_context": "moa.normalize.gene:BRAF"
    }


@pytest.fixture(scope="session")
def moa_gene_braf():
    """Create test fixture for MOA Gene BRAF"""
    return {
        "id": "moa.normalize.gene:BRAF",
        "type": "GeneDescriptor",
        "label": "BRAF",
        "gene": "hgnc:1097"
    }


@pytest.fixture(scope="module")
def moa_cetuximab():
    """Create test fixture for MOA Cetuximab Therapeutic Descriptor"""
    return {
        "id": "moa.normalize.therapy:Cetuximab",
        "type": "TherapeuticDescriptor",
        "label": "Cetuximab",
        "therapeutic": "rxcui:318341",
        "extensions": [{
            "type": "Extension",
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "ChEMBL",
                "has_indications": [
                    {
                        "id": "mesh:D002294",
                        "type": "DiseaseDescriptor",
                        "label": "Carcinoma, Squamous Cell",
                        "disease": "ncit:C2929"
                    },
                    {
                        "id": "mesh:D009369",
                        "type": "DiseaseDescriptor",
                        "label": "Neoplasms",
                        "disease": "ncit:C3262"
                    },
                    {
                        "id": "mesh:D015179",
                        "type": "DiseaseDescriptor",
                        "label": "Colorectal Neoplasms",
                        "disease": "ncit:C2956"
                    },
                    {
                        "id": "mesh:D006258",
                        "type": "DiseaseDescriptor",
                        "label": "Head and Neck Neoplasms",
                        "disease": "ncit:C4013"
                    }
                ]
            }
        }]
    }


@pytest.fixture(scope="module")
def moa_encorafenib():
    """Create test fixture for MOA Encorafenib Therapeutic Descriptor"""
    return {
        "id": "moa.normalize.therapy:Encorafenib",
        "type": "TherapeuticDescriptor",
        "label": "Encorafenib",
        "therapeutic": "rxcui:2049106",
        "extensions": [{
            "type": "Extension",
            "name": "regulatory_approval",
            "value": {
                "approval_rating": "ChEMBL",
                "has_indications": [
                    {
                        "id": "mesh:D009369",
                        "type": "DiseaseDescriptor",
                        "label": "Neoplasms",
                        "disease": "ncit:C3262"
                    },
                    {
                        "id": "mesh:D008545",
                        "type": "DiseaseDescriptor",
                        "label": "Melanoma",
                        "disease": "ncit:C3224"
                    }
                ]
            }
        }]
    }


@pytest.fixture(scope="module")
def moa_tcd_combination(moa_cetuximab, moa_encorafenib):
    """Create test fixture for MOA Combination Collection"""
    return {
        "id": "moa.tcd:zBda4sO3iQLExj5SB8VTPzPLaPoWefiP",
        "type": "TherapeuticsCollectionDescriptor",
        "therapeutic_collection": {
            "type": "CombinationTherapeutics",
            "members": [
                {"id": "rxcui:318341", "type": "Therapeutic"},
                {"id": "rxcui:2049106", "type": "Therapeutic"}
            ]
        },
        "member_descriptors": [moa_cetuximab, moa_encorafenib],
        "extensions": [
            {
                "type": "Extension",
                "name": "moa_therapy_type",
                "value": "Targeted therapy"
            }
        ]
    }


@pytest.fixture(scope="module")
def moa_colorectal_adenocarcinoma():
    """Create test fixture for MOA Colorectal Adenocarcinoma Disease Descriptor"""
    return {
        "id": "moa.normalize.disease:oncotree%3ACOADREAD",
        "type": "DiseaseDescriptor",
        "label": "Colorectal Adenocarcinoma",
        "xrefs": ["oncotree:COADREAD"],
        "disease": "ncit:C5105"
    }


@pytest.fixture(scope="module")
def statements(moa_aid159_statement):
    """Create test fixture for statements"""
    return [moa_aid159_statement]


@pytest.fixture(scope="module")
def propositions(moa_aid159_proposition):
    """Create test fixture for propositions"""
    return [moa_aid159_proposition]


@pytest.fixture(scope="module")
def variation_descriptors(moa_vid149):
    """Create test fixture for variation descriptors"""
    return [moa_vid149]


@pytest.fixture(scope="module")
def therapeutic_descriptors(moa_cetuximab, moa_encorafenib):
    """Create test fixture for therapeutic descriptors"""
    return [moa_cetuximab, moa_encorafenib]


@pytest.fixture(scope="module")
def therapeutic_collection_descriptors(moa_tcd_combination):
    """Create test fixture for therapeutic collection descriptors"""
    return [moa_tcd_combination]


@pytest.fixture(scope="module")
def disease_descriptors(moa_colorectal_adenocarcinoma):
    """Create test fixture for disease_descriptors"""
    return [moa_colorectal_adenocarcinoma]


@pytest.fixture(scope="module")
def gene_descriptors(moa_gene_braf):
    """Create test fixture for gene descriptors"""
    return [moa_gene_braf]


@pytest.fixture(scope="module")
def documents(moa_source62):
    """Create test fixture for documents"""
    return [moa_source62]


@pytest.fixture(scope="module")
def methods(method4):
    """Create test fixture for methods"""
    return [method4]


def test_moa_cdm(data, statements, propositions, variation_descriptors,
                 gene_descriptors, disease_descriptors, methods, documents,
                 check_statement, check_proposition, check_variation_descriptor,
                 check_descriptor, check_document, check_method,
                 therapeutic_descriptors, therapeutic_collection_descriptors,
                 check_transformed_cdm):
    """Test that moa transform works correctly with therapeutic collections."""
    check_transformed_cdm(
        data, statements, propositions, variation_descriptors, gene_descriptors,
        disease_descriptors, methods, documents, check_statement, check_proposition,
        check_variation_descriptor, check_descriptor, check_document, check_method,
        DATA_DIR / FILENAME, therapeutic_descriptors=therapeutic_descriptors,
        therapeutic_collection_descriptors=therapeutic_collection_descriptors
    )
