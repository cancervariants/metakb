"""Test CIViC source"""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters.civic import CIViC
from mock import patch
import json


@pytest.fixture(scope='module')
def lnscc():
    """Create a fixture for EID3017 evidence."""
    return {
        "id": 3017,
        "name": "EID3017",
        "description": "Patients with BRAF V600E-mutant NSCLC (n=57) were "
                       "enrolled into a phase 2, multicentre, non-randomised, "
                       "open-label study, administering dabrafenib plus "
                       "trametinib. The overall response rate was 36/57 "
                       "(63.2%, [95% CI 49.3-75.6]) and the median "
                       "progression-free survival was 9.7 months "
                       "(95% CI 6.9-19.6). At data cutoff "
                       "(11.6 months of follow-up), 18/36  (50%) confirmed "
                       "responses were ongoing and 23/57 (40%) of patients "
                       "had died.",
        "disease": {
            "id": 8,
            "name": "Lung Non-small Cell Carcinoma",
            "display_name": "Lung Non-small Cell Carcinoma",
            "doid": "3908",
            "url": "http://www.disease-ontology.org/?id=DOID:3908"
        },
        "drugs": [
            {
                "id": 19,
                "name": "Trametinib",
                "ncit_id": "C77908",
                "aliases": [
                    "N-(3-{3-cyclopropyl-5-[(2-fluoro-4-iodophenyl)amino]-6"
                    ",8-dimethyl-2,4,7-trioxo-3,4,6,7-tetrahydropyrido[4,3-d]"
                    "pyrimidin-1(2H)-yl}phenyl)acetamide",
                    "Mekinist", "MEK Inhibitor GSK1120212", "JTP-74057",
                    "GSK1120212"]
            }, {
                "id": 22,
                "name": "Dabrafenib",
                "ncit_id": "C82386",
                "aliases": ["GSK2118436", "GSK-2118436A", "GSK-2118436",
                            "BRAF Inhibitor GSK2118436",
                            "Benzenesulfonamide, N-(3-(5-(2-amino-4-pyrimidin"
                            "yl)-2-(1,1-dimethylethyl)-4-thiazolyl)-2-fluor"
                            "ophenyl)-2,6-difluoro-"]
            }
        ],
        "rating": 4,
        "evidence_level": "A",
        "evidence_type": "Predictive",
        "clinical_significance": "Sensitivity/Response",
        "evidence_direction": "Supports",
        "variant_origin": "Somatic",
        "drug_interaction_type": "Combination",
        "status": "accepted",
        # "open_change_count": 0,
        "type": "evidence",
        "source": {
            "id": 1296,
            "name": "Dabrafenib plus trametinib in patients with previously "
                    "treated BRAF(V600E)-mutant metastatic non-small cell "
                    "lung cancer: an open-label, multicentre phase 2 trial.",
            "citation": "Planchard et al., 2016, Lancet Oncol.",
            "citation_id": "27283860",
            "source_type": "PubMed",
            "asco_abstract_id": None,
            "source_url": "http://www.ncbi.nlm.nih.gov/pubmed/27283860",
            "open_access": True,
            "pmc_id": "PMC4993103",
            "publication_date": {
                "year": 2016,
                "month": 7
            },
            "journal": "Lancet Oncol.",
            "full_journal_title": "The Lancet. Oncology",
            "status": "partially curated",
            "is_review": False,
            "clinical_trials": [{
                "nct_id": "NCT01336634",
                "name": "Study of Selective BRAF Kinase Inhibitor Dabrafenib "
                        "Monotherapy Twice Daily and in Combination With "
                        "Dabrafenib Twice Daily and Trametinib Once Daily in "
                        "Combination Therapy in Subjects With BRAF V600E "
                        "Mutation Positive Metastatic (Stage IV) Non-small "
                        "Cell Lung Cancer.",
                "description": "Dabrafenib is a potent and selective inhibitor"
                               " of BRAF kinase activity. This is a Phase II,"
                               " non-randomized, open-label study to assess "
                               "the efficacy, safety, and tolerability of "
                               "dabrafenib administered as a single agent and "
                               "in combination with trametinib in stage IV "
                               "disease to subjects with BRAF mutant advanced"
                               " non-small cell lung cancer. Subjects will "
                               "receive dabrafenib 150 mg twice daily (BID) "
                               "in monotherapy treatment and dabrafenib 150 "
                               "mg bid and trametinib 2 mg once daily in "
                               "combination therapy and continue on treatment"
                               " until disease progression, death, or "
                               "unacceptable adverse event.",
                "clinical_trial_url":
                    "https://clinicaltrials.gov/show/NCT01336634"
            }]
        },
        "variant_id": 12,
        "phenotypes": [],
        "assertions": [],
        # "errors": {},
        # "fields_with_pending_changes": {},
        "gene_id": 5
    }


@patch.object(CIViC, '_get_all_evidence')
def test_evidence(test_get_all_evidence, lnscc):
    """Test that CIViC harvest evidence method is correct."""
    with open(f"{PROJECT_ROOT}/tests/data/"
              f"harvesters/civic/evidence.json") as f:
        data = json.load(f)
    test_get_all_evidence.return_value = data
    evidence = CIViC()._harvest_evidence()
    evidence_item = None
    for ev in evidence:
        if ev['id'] == 3017:
            evidence_item = ev
    assert evidence_item == lnscc
