"""Test components of the PMKB harvester."""
import pytest
from metakb.harvesters.pmkb import PMKB
from metakb import PROJECT_ROOT


@pytest.fixture(scope='module')
def variant_fixture():
    """Return fixture for data associated with FGFR3 F384L variant."""
    return {
        'type': 'variant',
        'name': 'FGFR3 F384L',
        'gene': 'FGFR3',
        'evidence': {
            'type': 'evidence',
            'source': [
                'Nakanishi Y, et al. The fibroblast growth factor receptor genetic status as a potential predictor of the sensitivity to CH5183284/Debio 1347, a novel selective FGFR inhibitor. Mol Cancer Ther 2014;13(11):2547-58', 'Lafitte M, et al. FGFR3 has tumor suppressor properties in cells with epithelial phenotype. Mol Cancer 2013;12():83',  # noqa: E501
                'Kanazawa TY, et al. Frequency of the allelic variant c.1150T &amp;gt; C in exon 10 of the fibroblast growth factor receptor 3 (FGFR3) gene is not increased in patients with pathogenic mutations and related chondrodysplasia phenotypes. Genet Mol Biol 2014;37(4):622-4',  # noqa: E501
            ]
        },
        'assertions': [
            {
                'type': 'assertion',
                'description': 'FGFR3 is one of 4 high affinity tyrosine kinase receptors for the fibroblast growth factor family of ligands. On ligand stimulation, FGFR3 undergoes dimerization and tyrosine autophosphorylation, resulting in cell proliferation or differentiation, , through the mitogen-activated protein kinase (MAPK) and phospholipase Cg signal transduction pathways. Some FGFR3 mutations are believed to result in ligand-independent activation of the receptor. However, FGFR3 F384L mutation is not associated with activation of FGFR and, in NIH-3T3 cells, it was demonstrated to be devoid of any transforming activity.  In some cases, the possibility of FGFR3 variants being of germline origin, cannot be excluded. The FGFR3 F384L mutation has been reported as a benign/likely benign germline variant in ClinVar (https://www.ncbi.nlm.nih.gov/clinvar/variation/134404/). Clinical correlation is recommended.',  # noqa: E501
                'tumor_types': [
                    'Adenocarcinoma', 'Carcinoma', 'Squamous Cell Carcinoma',
                    'Papillary Carcinoma', 'Follicular Carcinoma'
                ],
                'tissue_types': [
                    'Lung', 'Breast', 'Colon', 'Pancreas', 'Thyroid', 'Liver',
                ],
                'tier': 3,
                'gene': 'FGFR3'
            },
            {
                'type': 'assertion',
                'description': 'FGFR3 is one of four high affinity tyrosine kinase receptors for the fibroblast growth factor family of ligands. On ligand stimulation, FGFR3 undergoes dimerization and tyrosine autophosphorylation, resulting in cell proliferation or differentiation through the mitogen-activated protein kinase (MAPK) and phospholipase Cg signal transduction pathways. Some FGFR3 mutations are believed to result in ligand-independent activation of the receptor. However, FGFR3 F384L mutation is not associated with activation of FGFR and, in NIH-3T3 cells, it was demonstrated to be devoid of any transforming activity. FGFR3 is altered in 2.9% of pancreatic adenocarcinomas. The FGFR3 F384L mutation has been reported as a benign/likely benign germline variant in ClinVar (https://www.ncbi.nlm.nih.gov/clinvar/variation/134404/). Clinical correlation is recommended.',  # noqa: E501
                'tumor_types': ['Adenocarcinoma'],
                'tissue_types': ['Ampulla (Pancreaticobiliary Duct)'],
                'tier': 3,
                'gene': 'FGFR3'
            }
        ]
    }


@pytest.fixture(scope='module')
def gene_fixture():
    """Create NOTCH2 gene fixture."""
    return {
        'type': 'gene',
        'name': 'NOTCH2',
        'variants': [
            {
                'name': 'NOTCH2 I2304fs',
                'evidence_count': 1
            }
        ]
    }


@pytest.fixture(scope='module')
def pmkb():
    """Create PMKB harvester test fixture"""
    class PMKBVariants:

        def __init__(self):
            self.pmkb = PMKB()
            self._data = self.pmkb._load_dataframe(data_dir=PROJECT_ROOT / 'tests' / 'unit' / 'harvesters' / 'data')  # noqa: E501

        def get_vars(self):
            return self.pmkb._build_variants(self._data)

    return PMKBVariants()


def test_variant_generation(pmkb, variant_fixture):
    """Test generation of variant objects by PMKB harvester."""
    variants = [v for v in pmkb.get_vars() if v['name'] == 'FGFR3 F384L']
    assert len(variants) == 1
    actual_var = variants[0]
    test_var = variant_fixture
    assert test_var['type'] == actual_var['type']
    assert test_var['name'] == actual_var['name']
    assert test_var['gene'] == actual_var['gene']
    assert test_var['evidence']['type'] == actual_var['evidence']['type']
    assert set(test_var['evidence']['source']) == \
        set(test_var['evidence']['source'])
    assert len(test_var['assertions']) == len(actual_var['assertions'])
    test_assrtn1 = [a for a in test_var['assertions']
                    if 'four' in a['description']][0]
    actual_assrtn1 = [a for a in actual_var['assertions']
                      if 'four' in a['description']][0]
    assert test_assrtn1['type'] == actual_assrtn1['type']
    assert set(test_assrtn1['tumor_types']) == \
        set(actual_assrtn1['tumor_types'])
    assert set(test_assrtn1['tissue_types']) == \
        set(actual_assrtn1['tissue_types'])
    assert test_assrtn1['tier'] == actual_assrtn1['tier']
    assert test_assrtn1['gene'] == actual_assrtn1['gene']
