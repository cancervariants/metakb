"""Test PMKB variant harvest."""
import pytest
from metakb import PROJECT_ROOT
from metakb.harvesters import PMKB


@pytest.fixture(scope='module')
def pmkb_harvester():
    """Return test fixture for PMKB harvester instance."""
    pmkb_instance = PMKB()
    pmkb_instance.pmkb_dir = PROJECT_ROOT / 'tests' / 'data' / 'harvesters' / 'pmkb'  # noqa: E501
    return pmkb_instance


@pytest.fixture(scope='module')
def pmkb_variants():
    """Return test fixture for PMKB variant output."""
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
            'pmkb_url': 'https://pmkb.org/variants/422',
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
            "coordinates": [],
            'pmkb_url': 'https://pmkb.org/variants/423',
            'transcript_ensembl_url': 'http://grch37.ensembl.org/Homo_sapiens/Transcript/Summary?db=core;t=ENST00000373103',  # noqa: E501
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
            "coordinates": [],
            'pmkb_url': 'https://pmkb.org/variants/424',
            'transcript_ensembl_url': 'http://grch37.ensembl.org/Homo_sapiens/Transcript/Summary?db=core;t=ENST00000373103',  # noqa: E501
        },
    }


def test_pmkb_variants(pmkb_harvester, pmkb_variants):
    """Test that variants are correctly harvested."""
    variants = pmkb_harvester._get_all_variants()
    assert len(variants) == len(pmkb_variants)
    for key in variants.keys():
        variant = variants[key]
        variant_actual = pmkb_variants[key]

        assert variant == variant_actual
