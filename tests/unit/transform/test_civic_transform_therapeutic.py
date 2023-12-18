"""Test CIViC Transformation to common data model for Therapeutic Response."""
import pytest
import pytest_asyncio
from metakb.transform.civic import CivicTransform
from metakb import PROJECT_ROOT
import json


DATA_DIR = PROJECT_ROOT / "tests" / "data" / "transform" / "therapeutic"
FILENAME = "civic_cdm.json"


@pytest_asyncio.fixture(scope="module")
@pytest.mark.asyncio
async def data(normalizers):
    """Create a CIViC Transform test fixture."""
    harvester_path = DATA_DIR / "civic_harvester.json"
    c = CivicTransform(data_dir=DATA_DIR, harvester_path=harvester_path,
                       normalizers=normalizers)
    await c.transform()
    c.create_json(transform_dir=DATA_DIR, filename=FILENAME)
    with open(DATA_DIR / FILENAME, "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="module")
def civic_tid28():
    """Create test fixture for CIViC therapy ID 28"""
    return {
        "id": "civic.tid:28",
        "type": "TherapeuticAgent",
        "label": "Panitumumab",
        "mappings": [
            {
                "coding": {
                    "code": "C1857",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
            "ABX-EGF",
            "ABX-EGF Monoclonal Antibody",
            "ABX-EGF, Clone E7.6.3",
            "E7.6.3",
            "Human IgG2K Monoclonal Antibody",
            "MoAb ABX-EGF",
            "MoAb E7.6.3",
            "Monoclonal Antibody ABX-EGF",
            "Monoclonal Antibody E7.6.3",
            "Vectibix"
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "therapy_normalizer_id",
                "value": "rxcui:263034"
            },
            {
                "type": "Extension",
                "name": "regulatory_approval",
                "value": {
                    "approval_rating": "ChEMBL",
                    "has_indications": [
                        {
                            "id": "mesh:D009369",
                            "type": "Disease",
                            "label": "Neoplasms",
                            "mappings": [
                                {
                                    "coding": {"code": "C3262", "system": "ncit"},
                                    "relation": "relatedMatch"
                                }
                            ]
                        },
                        {
                            "id": "mesh:D015179",
                            "type": "Disease",
                            "label": "Colorectal Neoplasms",
                            "mappings": [
                                {
                                    "coding": {"code": "C2956", "system": "ncit"},
                                    "relation": "relatedMatch"
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid16(cetuximab_extensions):
    """Create test fixture for CIViC therapy ID 16"""
    return {
        "id": "civic.tid:16",
        "type": "TherapeuticAgent",
        "label": "Cetuximab",
        "mappings": [
            {
                "coding": {
                    "code": "C1723",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
            "Cetuximab Biosimilar CDP-1",
            "Cetuximab Biosimilar CMAB009",
            "Cetuximab Biosimilar KL 140",
            "Chimeric Anti-EGFR Monoclonal Antibody",
            "Chimeric MoAb C225",
            "Chimeric Monoclonal Antibody C225",
            "Erbitux",
            "IMC-C225"
        ],
        "extensions": cetuximab_extensions
    }


@pytest.fixture(scope="module")
def civic_did11():
    """Create test fixture for CIViC Disease ID 11"""
    return {
        "id": "civic.did:11",
        "type": "Disease",
        "label": "Colorectal Cancer",
        "mappings": [
            {
                "coding": {
                    "code": "DOID:9256",
                    "system": "https://www.disease-ontology.org/"
                },
                "relation": "exactMatch"
            }
        ],
        "extensions": [
            {
                "type": "Extension",
                "name": "disease_normalizer_id",
                "value": "ncit:C4978"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_eid816_study(
    civic_mpid12,
    civic_tid28,
    civic_tid16,
    civic_did11,
    civic_gid5,
    civic_method
):
    """Create CIVIC EID816 study test fixture. Uses TherapeuticSubstituteGroup."""
    return {
        "id": "civic.eid:816",
        "type": "VariantTherapeuticResponseStudy",
        "description": "This meta-analysis of 7 randomized control trials evaluating overall survival (OS) (8 for progression free survival) could not definitely state that survival benefit of anti-EGFR monoclonal antibodies is limited to patients with wild type BRAF. In other words, the authors believe that there is insufficient data to justify the exclusion of anti-EGFR monoclonal antibody therapy for patients with mutant BRAF. In these studies, mutant BRAF specifically meant the V600E mutation.",  # noqa: E501
        "direction": "refutes",
        "strength": {
            "code": "e000005",
            "label": "clinical cohort evidence",
            "system": "https://go.osu.edu/evidence-codes"
        },
        "predicate": "predictsResistanceTo",
        "variant": civic_mpid12,
        "therapeutic": {
            "type": "TherapeuticSubstituteGroup",
            "id": "civic.tsgid:7IxyhCwID0QYyVCP2xuIyYvwwu-S_HrZ",
            "substitutes": [civic_tid16, civic_tid28],
            "extensions": [
                {
                    "type": "Extension",
                    "name": "civic_therapy_interaction_type",
                    "value": "SUBSTITUTES"
                }
            ]
        },
        "tumorType": civic_did11,
        "qualifiers": {
            "alleleOrigin": "somatic",
            "geneContext": civic_gid5
        },
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:548",
                "label": "Rowland et al., 2015, Br. J. Cancer",
                "title": "Meta-analysis of BRAF mutation as a predictive biomarker of benefit from anti-EGFR monoclonal antibody therapy for RAS wild-type metastatic colorectal cancer.",  # noqa: E501
                "pmid": 25989278,
                "type": "Document"
            }
        ]
    }


@pytest.fixture(scope="module")
def civic_tid483(encorafenib_extensions):
    """Create test fixture for CIViC Therapy ID 483"""
    return {
        "id": "civic.tid:483",
        "type": "TherapeuticAgent",
        "label": "Encorafenib",
        "mappings": [
            {
                "coding": {
                    "code": "C98283",
                    "system": "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code="  # noqa: E501
                },
                "relation": "exactMatch"
            }
        ],
        "aliases": [
            "Braftovi",
            "LGX 818",
            "LGX-818",
            "LGX818"
        ],
        "extensions": encorafenib_extensions
    }


@pytest.fixture(scope="module")
def civic_eid9851_study(
    civic_mpid12,
    civic_tid483,
    civic_tid16,
    civic_did11,
    civic_gid5,
    civic_method,
):
    """Create CIVIC EID9851 study test fixture. Uses CombinationTherapy."""
    return {
        "id": "civic.eid:9851",
        "type": "VariantTherapeuticResponseStudy",
        "description": "The open-label phase 3 BEACON CRC trial included 665 patients with BRAF V600E-mutated metastatic CRC. Patients were randomly assigned in a 1:1:1 ratio to receive encorafenib, binimetinib, and cetuximab (triplet-therapy group); encorafenib and cetuximab (doublet-therapy group); or the investigators\u2019 choice of either cetuximab and irinotecan or cetuximab and FOLFIRI. The median overall survival was 8.4 months (95% CI, 7.5 to 11.0) in the doublet-therapy group and 5.4 months (95% CI, 4.8 to 6.6) in the control group, with a significantly lower risk of death compared to the control group (hazard ratio for death doublet-group vs. control, 0.60; 95% CI, 0.45 to 0.79; P<0.001). The confirmed response rate was 26% (95% CI, 18 to 35) in the triplet-therapy group, 20% in the doublet-therapy group (95% CI 13 to 29) and 2% (95% CI, 0 to 7) in the control group (doublet group vs. control P<0.001). Median PFS was 4.2 months (95% CI, 3.7 to 5.4) in the doublet-therapy group, and 1.5 months (95% CI, 1.5 to 1.7) in the control group (hazard ratio for disease progression doublet-group vs control, 0.40; 95% CI, 0.31 to 0.52, P<0.001).",  # noqa: E501
        "direction": "supports",
        "strength": {
            "code": "e000001",
            "label": "authoritative evidence",
            "system": "https://go.osu.edu/evidence-codes"
        },
        "predicate": "predictsSensitivityTo",
        "variant": civic_mpid12,
        "therapeutic": {
            "type": "CombinationTherapy",
            "id": "civic.ctid:P1PY89shAjemg7jquQ0V9pg1VnYnkPeK",
            "components": [civic_tid483, civic_tid16],
            "extensions": [
                {
                    "type": "Extension",
                    "name": "civic_therapy_interaction_type",
                    "value": "COMBINATION"
                }
            ]
        },
        "tumorType": civic_did11,
        "qualifiers": {
            "alleleOrigin": "somatic",
            "geneContext": civic_gid5
        },
        "specifiedBy": civic_method,
        "isReportedIn": [
            {
                "id": "civic.source:3025",
                "label": "Kopetz et al., 2019, N. Engl. J. Med.",
                "title": "Encorafenib, Binimetinib, and Cetuximab in BRAF V600E-Mutated Colorectal Cancer.",  # noqa: E501
                "pmid": 31566309,
                "type": "Document"
            }
        ]
    }


@pytest.fixture(scope="module")
def studies(civic_eid2997_study, civic_eid816_study, civic_eid9851_study):
    """Create test fixture for CIViC therapeutic studies."""
    return [civic_eid2997_study, civic_eid816_study, civic_eid9851_study]


def test_civic_cdm(data, studies, check_transformed_cdm):
    """Test that civic transform works correctly."""
    check_transformed_cdm(
        data, studies, DATA_DIR / FILENAME
    )
