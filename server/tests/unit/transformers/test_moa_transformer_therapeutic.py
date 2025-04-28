"""Test MOA Transformation to common data model"""

import pytest
import pytest_asyncio
from tests.conftest import (
    TEST_TRANSFORMERS_DIR,
    get_transformed_data,
    get_vicc_normalizer_failure_ext,
    get_vicc_normalizer_priority_ext,
)

from metakb.transformers.moa import MoaTransformer

DATA_DIR = TEST_TRANSFORMERS_DIR / "therapeutic"
NORMALIZABLE_FILENAME = "moa_cdm.json"
NOT_NORMALIZABLE_FILE_NAME = "moa_cdm_normalization_failure.json"
MOA_THERAPY_CONFLICT_FILENAME = "moa_therapy_conflict_cdm.json"


@pytest_asyncio.fixture(scope="module")
async def normalizable_data(normalizers):
    """Create a MOA Transformer test fixture."""
    harvester_path = DATA_DIR / "moa_harvester.json"
    return await get_transformed_data(
        MoaTransformer, DATA_DIR, harvester_path, normalizers, NORMALIZABLE_FILENAME
    )


@pytest_asyncio.fixture(scope="module")
async def not_normalizable_data(normalizers):
    """Create a MOA Transformer test fixture for data that cannot be normalized."""
    # NOTE: This file was manually generated to create a fake evidence item
    #       However, it does include some actual moa records that fail to normalize.
    #       Gene record was modified to fail
    harvester_path = DATA_DIR / "moa_harvester_not_normalizable.json"
    return await get_transformed_data(
        MoaTransformer,
        DATA_DIR,
        harvester_path,
        normalizers,
        NOT_NORMALIZABLE_FILE_NAME,
    )


@pytest.fixture(scope="module")
def moa_vid144(braf_v600e_genomic):
    """Create a test fixture for MOA VID144."""
    genomic_rep = braf_v600e_genomic.copy()
    genomic_rep["name"] = "7-140453136-A-T"

    return {
        "id": "moa.variant:144",
        "type": "CategoricalVariant",
        "name": "BRAF p.V600E (Missense)",
        "constraints": [
            {
                "allele": {
                    "id": "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
                    "digest": "j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
                    "type": "Allele",
                    "location": {
                        "id": "ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                        "digest": "t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
                        "type": "SequenceLocation",
                        "sequenceReference": {
                            "type": "SequenceReference",
                            "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
                        },
                        "start": 599,
                        "end": 600,
                        "sequence": "V",
                    },
                    "state": {"type": "LiteralSequenceExpression", "sequence": "E"},
                },
                "type": "DefiningAlleleConstraint",
            }
        ],
        "members": [genomic_rep],
        "extensions": [
            {
                "name": "MOA representative coordinate",
                "value": {
                    "chromosome": "7",
                    "start_position": "140453136",
                    "end_position": "140453136",
                    "reference_allele": "A",
                    "alternate_allele": "T",
                    "cdna_change": "c.1799T>A",
                    "protein_change": "p.V600E",
                    "exon": "15",
                },
            }
        ],
        "mappings": [
            {
                "coding": {
                    "id": "moa.variant:144",
                    "system": "https://moalmanac.org",
                    "code": "144",
                },
                "relation": "exactMatch",
            },
            {
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov/snp/",
                    "code": "rs113488022",
                },
                "relation": "relatedMatch",
            },
        ],
    }


@pytest.fixture(scope="module")
def moa_cetuximab(cetuximab_extensions, cetuximab_normalizer_mappings):
    """Create a test fixture for MOA Cetuximab"""
    return {
        "id": "moa.normalize.therapy.rxcui:318341",
        "conceptType": "Therapy",
        "name": "Cetuximab",
        "extensions": cetuximab_extensions,
        "mappings": [
            *cetuximab_normalizer_mappings,
            {
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
                "coding": {
                    "id": "ncit:C1723",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                    "code": "C1723",
                },
                "relation": "exactMatch",
            },
        ],
    }


@pytest.fixture(scope="module")
def moa_encorafenib(encorafenib_extensions, encorafenib_normalizer_mappings):
    """Create test fixture for MOA Encorafenib"""
    return {
        "id": "moa.normalize.therapy.rxcui:2049106",
        "conceptType": "Therapy",
        "name": "Encorafenib",
        "extensions": encorafenib_extensions,
        "mappings": [
            *encorafenib_normalizer_mappings,
            {
                "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
                "coding": {
                    "id": "ncit:C98283",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                    "code": "C98283",
                },
                "relation": "exactMatch",
            },
        ],
    }


@pytest.fixture(scope="module")
def moa_aid154_study_stmt(
    moa_vid144,
    moa_cetuximab,
    moa_encorafenib,
    moa_method,
    braf_normalizer_mappings,
):
    """Create MOA AID 154 study statement test fixture. Uses CombinationTherapy."""
    braf_normalizer_mappings_cpy = braf_normalizer_mappings[:]
    braf_normalizer_mappings_cpy.append(
        {
            "coding": {
                "id": "ncbigene:673",
                "code": "673",
                "system": "https://www.ncbi.nlm.nih.gov/gene/",
            },
            "relation": "exactMatch",
            "extensions": [get_vicc_normalizer_priority_ext(is_priority=False)],
        },
    )
    return {
        "id": "moa.assertion:154",
        "type": "Statement",
        "direction": "supports",
        "description": "The U.S. Food and Drug Administration (FDA) granted regular approval to encorafenib in combination with cetuximab for the treatment of adult patients with metastatic colorectal cancer (CRC) with BRAF V600E mutation, as detected by an FDA-approved test, after prior therapy.",
        "strength": {
            "primaryCoding": {
                "system": "https://moalmanac.org/about",
                "code": "FDA-Approved",
            },
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000002",
                        "name": "FDA recognized evidence",
                    },
                    "relation": "exactMatch",
                },
            ],
        },
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "subjectVariant": moa_vid144,
            "objectTherapeutic": {
                "membershipOperator": "AND",
                "id": "moa.ctid:E8RHoiov2ULWPZVlCea5dqttCbNY0IyL",
                "therapies": [moa_cetuximab, moa_encorafenib],
                "extensions": [
                    {
                        "name": "moa_therapy_type",
                        "value": "Targeted therapy",
                    }
                ],
            },
            "conditionQualifier": {
                "id": "moa.normalize.disease.ncit:C5105",
                "conceptType": "Disease",
                "name": "Colorectal Adenocarcinoma",
                "mappings": [
                    {
                        "coding": {
                            "name": "Colorectal Adenocarcinoma",
                            "system": "https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                            "code": "COADREAD",
                            "id": "oncotree:COADREAD",
                        },
                        "relation": "exactMatch",
                    },
                    {
                        "coding": {
                            "name": "Colorectal Adenocarcinoma",
                            "id": "ncit:C5105",
                            "code": "C5105",
                            "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                        },
                        "relation": "exactMatch",
                        "extensions": [
                            get_vicc_normalizer_priority_ext(is_priority=True)
                        ],
                    },
                    {
                        "coding": {
                            "id": "MONDO_0005008",
                            "code": "MONDO:0005008",
                            "system": "https://purl.obolibrary.org/obo/",
                        },
                        "relation": "exactMatch",
                        "extensions": [
                            get_vicc_normalizer_priority_ext(is_priority=False)
                        ],
                    },
                    {
                        "extensions": [
                            get_vicc_normalizer_priority_ext(is_priority=False)
                        ],
                        "coding": {
                            "id": "DOID:0050913",
                            "system": "https://disease-ontology.org/?id=",
                            "code": "DOID:0050913",
                        },
                        "relation": "exactMatch",
                    },
                    {
                        "extensions": [
                            get_vicc_normalizer_priority_ext(is_priority=False)
                        ],
                        "coding": {
                            "id": "DOID:0050861",
                            "system": "https://disease-ontology.org/?id=",
                            "code": "DOID:0050861",
                        },
                        "relation": "exactMatch",
                    },
                ],
            },
            "alleleOriginQualifier": {"name": "somatic"},
            "geneContextQualifier": {
                "id": "moa.normalize.gene.hgnc:1097",
                "conceptType": "Gene",
                "name": "BRAF",
                "mappings": braf_normalizer_mappings_cpy,
            },
        },
        "specifiedBy": moa_method,
        "reportedIn": [
            {
                "id": "moa.source:64",
                "extensions": [{"name": "source_type", "value": "FDA"}],
                "type": "Document",
                "title": "Array BioPharma Inc. Braftovi (encorafenib) [package insert]. U.S. Food and Drug Administration website. www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf. Revised April 2020. Accessed October 15, 2020.",
                "urls": [
                    "https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/210496s006lbl.pdf"
                ],
            }
        ],
    }


@pytest.fixture(scope="session")
def moa_vid21_modified():
    """Create a test fixture for MOA VID21 which has been modified to fail"""
    return {
        "id": "moa.variant:21",
        "type": "CategoricalVariant",
        "name": "FakeGene Translocation",
        "extensions": [
            get_vicc_normalizer_failure_ext(),
            {"name": "MOA locus", "value": "t(6;14)"},
        ],
        "mappings": [
            {
                "coding": {
                    "id": "moa.variant:21",
                    "system": "https://moalmanac.org",
                    "code": "21",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="session")
def moa_mito_cp():
    """Create a test fixture for MOA Imatinib Therapy."""
    return {
        "id": "moa.therapy:Mito-CP",
        "conceptType": "Therapy",
        "name": "Mito-CP",
        "extensions": [get_vicc_normalizer_failure_ext()],
    }


@pytest.fixture(scope="session")
def moa_t_cell_acute_lymphoid_leukemia():
    """Create test fixture for MOA T-Cell Acute Lymphoid Leukemia."""
    return {
        "id": "moa.disease:T-Cell_Acute_Lymphoid_Leukemia",
        "conceptType": "Disease",
        "name": "T-Cell Acute Lymphoid Leukemia",
        "extensions": [get_vicc_normalizer_failure_ext()],
        "mappings": [
            {
                "coding": {
                    "id": "oncotree:TALL",
                    "name": "T-Cell Acute Lymphoid Leukemia",
                    "system": "https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                    "code": "TALL",
                },
                "relation": "exactMatch",
            }
        ],
    }


@pytest.fixture(scope="module")
def moa_fake_gene():
    """Create a test fixture for a fake gene in MOA."""
    return {
        "id": "moa.gene:FakeGene",
        "conceptType": "Gene",
        "name": "FakeGene",
        "extensions": [get_vicc_normalizer_failure_ext()],
    }


@pytest.fixture(scope="module")
def moa_not_normalizable_stmt(
    moa_vid21_modified,
    moa_fake_gene,
    moa_mito_cp,
    moa_t_cell_acute_lymphoid_leukemia,
    moa_method,
    moa_source45,
):
    """Create test fixture for fake moa statement that fails to normalize gene,
    variant, disease, and therapy.
    """
    return {
        "id": "moa.assertion:123456789",
        "description": "This is a fake assertion item.",
        "strength": {
            "primaryCoding": {
                "system": "https://moalmanac.org/about",
                "code": "Preclinical evidence",
            },
            "mappings": [
                {
                    "coding": {
                        "system": "https://go.osu.edu/evidence-codes",
                        "code": "e000009",
                        "name": "preclinical evidence",
                    },
                    "relation": "exactMatch",
                },
            ],
        },
        "direction": "supports",
        "proposition": {
            "type": "VariantTherapeuticResponseProposition",
            "predicate": "predictsSensitivityTo",
            "subjectVariant": moa_vid21_modified,
            "objectTherapeutic": moa_mito_cp,
            "conditionQualifier": moa_t_cell_acute_lymphoid_leukemia,
            # "alleleOriginQualifier": {"name": "somatic"},
            "geneContextQualifier": moa_fake_gene,
        },
        "specifiedBy": moa_method,
        "reportedIn": [moa_source45],
        "type": "Statement",
    }


@pytest.fixture(scope="module")
def statements(moa_aid66_study_stmt, moa_aid154_study_stmt):
    """Create test fixture for MOA therapeutic statements."""
    return [moa_aid66_study_stmt, moa_aid154_study_stmt]


def test_moa_cdm(normalizable_data, statements, check_transformed_cdm):
    """Test that moa transformation works correctly."""
    check_transformed_cdm(
        normalizable_data, statements, DATA_DIR / NORMALIZABLE_FILENAME
    )


def test_moa_cdm_not_normalizable(
    not_normalizable_data, moa_not_normalizable_stmt, check_transformed_cdm
):
    """Test that moa transformation works correctly for MOA records that cannot
    normalize (gene, disease, variant, and therapy)
    """
    check_transformed_cdm(
        not_normalizable_data,
        [moa_not_normalizable_stmt],
        DATA_DIR / NOT_NORMALIZABLE_FILE_NAME,
    )


@pytest.mark.asyncio
async def test_moa_concept_conflicts(normalizers):
    """Test that MOA therapy and disease conflict resolution works correctly"""
    t = MoaTransformer(
        data_dir=DATA_DIR,
        harvester_path=DATA_DIR / "moa_harvester_conflicts.json",
        normalizers=normalizers,
    )
    harvested_data = t.extract_harvested_data()
    await t.transform(harvested_data)

    therapies = t.processed_data.therapies
    assert len(therapies) == 1

    therapy = therapies[0]
    assert therapy.id == "moa.normalize.therapy.rxcui:2370147"
    assert therapy.name == "LOXO-292"
    therapy_alias_ext = next(
        (ext for ext in therapy.extensions if ext.name == "aliases"),
        None,
    )
    assert therapy_alias_ext.model_dump(exclude_none=True) == {
        "name": "aliases",
        "value": ["Selpercatinib"],
    }

    conditions = t.processed_data.conditions
    assert len(conditions) == 1

    condition = conditions[0]
    assert condition.id == "moa.normalize.disease.ncit:C3247"
    assert condition.name == "Myelodysplasia"
    condition_alias_ext = next(
        (ext for ext in condition.extensions if ext.name == "aliases"),
        None,
    )
    assert condition_alias_ext.model_dump(exclude_none=True) == {
        "name": "aliases",
        "value": ["Myelodysplastic Syndromes"],
    }
