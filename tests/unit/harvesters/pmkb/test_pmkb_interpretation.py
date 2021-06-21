"""Test PMKB interpretation harvest."""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters import PMKB
import unittest


@pytest.fixture(scope='module')
def pmkb_harvester():
    """Return test fixture for PMKB harvester instance."""
    pmkb_instance = PMKB()
    pmkb_instance.pmkb_dir = PROJECT_ROOT / 'tests' / 'data' / 'harvesters' / 'pmkb'  # noqa: E501
    return pmkb_instance


@pytest.fixture(scope='module')
def pmkb_variants():
    """Return test fixture for variant input to _get_all_interpretations."""
    return {
        "CSF3R T618I": {
            "name": "CSF3R T618I",
            "gene": "CSF3R",
            "id": "422",
            "origin": "Somatic",
            "variation_type": "missense",
            "dna_change": "",
            "amino_acid_change": "T618I",
            "ensembl_id": "ENST00000373103",
            "cosmic_id": "",
            "chromosome": "",
            "arm_cytoband": "",
            "partner_gene": "",
            "codons": "618",
            "exons": "",
            "coordinates": [],
            "pmkb_url": "https://pmkb.org/variants/422",
            'transcript_ensembl_url': 'http://grch37.ensembl.org/Homo_sapiens/Transcript/Summary?db=core;t=ENST00000373103'  # noqa: E501
        },
        "CSF3R any nonsense": {
            "name": "CSF3R any nonsense",
            "gene": "CSF3R",
            "id": "423",
            "origin": "Somatic",
            "variation_type": "nonsense",
            "dna_change": "",
            "amino_acid_change": "",
            "ensembl_id": "ENST00000373103",
            "cosmic_id": "",
            "chromosome": "",
            "arm_cytoband": "",
            "partner_gene": "",
            "codons": "",
            "exons": "",
            "coordinates": []
        },
        "CSF3R any frameshift": {
            "name": "CSF3R any frameshift",
            "gene": "CSF3R",
            "id": "424",
            "origin": "Somatic",
            "variation_type": "frameshift",
            "dna_change": "",
            "amino_acid_change": "",
            "ensembl_id": "ENST00000373103",
            "cosmic_id": "",
            "chromosome": "",
            "arm_cytoband": "",
            "partner_gene": "",
            "codons": "",
            "exons": "",
            "coordinates": []
        },
    }


@pytest.fixture(scope='module')
def pmkb_interp_1():
    """Return test fixture for PMKB interpretation ID 1."""
    return {
        "id": "1",
        "gene": "CSF3R",
        "evidence_items": [
            "Pardanani A, et al. CSF3R T618I is a highly prevalent and specific mutation in chronic neutrophilic leukemia. Leukemia 2013;27(9):1870-3",  # noqa: E501
            "Maxson JE, et al. Oncogenic CSF3R mutations in chronic neutrophilic leukemia and atypical CML. N Engl J Med 2013;368(19):1781-90",  # noqa: E501
            "Plo I, et al. An activating mutation in the CSF3R gene induces a hereditary chronic neutrophilia. J Exp Med 2009;206(8):1701-7"  # noqa: E501
        ],
        "pmkb_evidence_tier": "1",
        "variants": [
            {
                "name": "CSF3R any nonsense",
                "id": "423"
            },
            {
                "name": "CSF3R any frameshift",
                "id": "424"
            },
            {
                "name": "CSF3R T618I",
                "id": "422"
            },
        ],
        "diseases": [
            "Myeloproliferative Neoplasm",
            "Atypical Chronic Myeloid Leukemia",
            "Chronic Neutrophilic Leukemia"
        ],
        "therapies": [
            ""
        ],
        "description": "The activating missense membrane-proximal mutation in CSF3R (p.T618I) has been reported to occur in approximately 83% of cases of chronic neutrophilic leukemia; some reports indicate this mutation may be present in cases of atypical chronic myeloid leukemia as well.   The CS3R T618I mutation has been associated with response to JAK2 inhibitors but not dasatinib.  A germline activating CSF3R mutation (p. T617N) has been described in autosomal dominant hereditary neutrophilia associated with splenomegaly and increased circulating CD34-positive myeloid progenitors.  Nonsense and/or frameshift somatic mutations truncating the cytoplasmic domain of CSF3R have been described in approximately 40% of patients with severe congenital neutropenia and in the context of mutations in other genes may be associated with progression to acute myeloid leukemia.  These activating truncating mutations have also been found in patients with chronic neutrophilic leukemia or atypical chronic myeloid leukemia. Some of these cytoplasmic truncating mutations have been associated with responses to dasatinib but not JAK2 inhibitors.",  # noqa: E501
        "tissue_types": [
            "Bone Marrow",
            "Blood"
        ],
    }


def test_interp_1(pmkb_harvester, pmkb_interp_1, pmkb_variants):
    """Test harvesting of PMKB interpretation."""
    interp = pmkb_harvester._get_all_interpretations(pmkb_variants)[0]
    assert interp['id'] == pmkb_interp_1['id']
    assert interp['gene'] == pmkb_interp_1['gene']
    assert set(interp['evidence_items']) == \
        set(pmkb_interp_1['evidence_items'])
    assert interp['pmkb_evidence_tier'] == pmkb_interp_1['pmkb_evidence_tier']
    unittest.TestCase().assertCountEqual(interp['variants'],
                                         pmkb_interp_1['variants'])
    assert set(interp['diseases']) == set(pmkb_interp_1['diseases'])
    assert set(interp['therapies']) == set(pmkb_interp_1['therapies'])
    assert interp['description'] == pmkb_interp_1['description']
    assert set(interp['tissue_types']) == set(pmkb_interp_1['tissue_types'])
