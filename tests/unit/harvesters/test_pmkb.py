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
def ev_fixture():
    """Create evidence test fixture."""
    return {
        "type": "evidence",
        "assertions": [
            {
                'type': 'assertion',
                'description': 'NOTCH2 gain of function mutations have been reported in approximately 25% of splenic marginal zone lymphomas and are thought to be rare in non-splenic marginal zone lymphomas. These mutations are typically located near the C-terminal PEST domain and lead to protein truncation or, more rarely, are nonsynonymous substitution mutations affecting the extracellular heterodimerization domain. In addition, NOTCH2 PEST domain mutations have been reported in approximately 8% of diffuse large B cell lymphomas and in vitro systems suggest that PEST domain mutant NOTCH2 receptors have increased activity compared to wild type NOTCH2. The prognostic and therapeutic implications of these alterations continue to be elucidated.',  # noqa: E501
                'gene': {
                    'name': 'NOTCH2'
                },
                'variants': [
                    {
                        'name': 'NOTCH2 I2304fs'
                    },
                    {
                        'name': 'NOTCH2 exon(s) 34 frameshift'
                    }
                ],
                'tier': 1,
                'tumor_types': [
                    'Marginal Zone B Cell Lymphoma'
                ],
                'tissue_types': [
                    'Spleen'
                ]
            }
        ],
        "source": {
            "citations": [
                'Kiel MJ, et al. Whole-genome sequencing identifies recurrent somatic NOTCH2 mutations in splenic marginal zone lymphoma. J Exp Med 2012;209(9):1553-65',  # noqa: E501
                'Lee SY, et al. Gain-of-function mutations and copy number  increases of Notch2 in diffuse large B-cell lymphoma. Cancer Sci 2009;100(5):920-6'  # noqa: E501
            ]
        }
    }


@pytest.fixture(scope='module')
def assertion_fixture():
    """Create assertion test fixture."""
    return {
        'type': 'assertion',
        'gene': {
            'name': 'FGFR3'
        },
        'description': 'FGFR3 is one of four high affinity tyrosine kinase receptors for the fibroblast growth factor family of ligands. On ligand stimulation, FGFR3 undergoes dimerization and tyrosine autophosphorylation, resulting in cell proliferation or differentiation through the mitogen-activated protein kinase (MAPK) and phospholipase Cg signal transduction pathways. Some FGFR3 mutations are believed to result in ligand-independent activation of the receptor. However, FGFR3 F384L mutation is not associated with activation of FGFR and, in NIH-3T3 cells, it was demonstrated to be devoid of any transforming activity. FGFR3 is altered in 2.9% of pancreatic adenocarcinomas. The FGFR3 F384L mutation has been reported as a benign/likely benign germline variant in ClinVar (https://www.ncbi.nlm.nih.gov/clinvar/variation/134404/). Clinical correlation is recommended.',  # noqa: E501
        'tier': 3,
        'tumor_types': [
            'Adenocarcinoma'
        ],
        'tissue_types': [
            'Ampulla (Pancreaticobiliary Duct)'
        ],
        'variants': [
            {
                'name': 'FGFR3 F384L'
            }
        ],
        'citations': [
            'Nakanishi Y, et al. The fibroblast growth factor receptor genetic status as a potential predictor of the sensitivity to CH5183284/Debio 1347, a novel selective FGFR inhibitor. Mol Cancer Ther 2014;13(11):2547-58.',  # noqa: E501
            'Lafitte M, et al. FGFR3 has tumor suppressor properties in cells with epithelial phenotype. Mol Cancer 2013;12():83.',  # noqa: E501
            'Kanazawa TY, et al. Frequency of the allelic variant c.1150T &amp;gt; C in exon 10 of the fibroblast growth factor receptor 3 (FGFR3) gene is not increased in patients with pathogenic mutations and related chondrodysplasia phenotypes. Genet Mol Biol 2014;37(4):622-4.',  # noqa: E501
            'Comprehensive TCGA PanCanAtlas (https://gdc.cancer.gov/about-data/publications/pancanatlas).'  # noqa: E501
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

        def get_ev(self):
            evidence, _ = self.pmkb._build_ev_and_assertions(self._data)
            return evidence

        def get_assertions(self):
            _, assertions = self.pmkb._build_ev_and_assertions(self._data)
            return assertions

    return PMKBVariants()


def test_variant_generation(pmkb, variant_fixture):
    """Test generation of variant objects by PMKB harvester."""
    variants = [v for v in pmkb.get_vars() if v['name'] == 'FGFR3 F384L']
    assert len(variants) == 1
    fixture_var = variants[0]
    test_var = variant_fixture
    assert test_var['type'] == fixture_var['type']
    assert test_var['name'] == fixture_var['name']
    assert test_var['gene'] == fixture_var['gene']
    assert test_var['evidence']['type'] == fixture_var['evidence']['type']
    assert set(test_var['evidence']['source']) == \
        set(test_var['evidence']['source'])
    assert len(test_var['assertions']) == len(fixture_var['assertions'])
    test_assrtn1 = [a for a in test_var['assertions']
                    if 'four' in a['description']][0]
    fixture_assrtn1 = [a for a in fixture_var['assertions']
                       if 'four' in a['description']][0]
    assert test_assrtn1['type'] == fixture_assrtn1['type']
    assert set(test_assrtn1['tumor_types']) == \
        set(fixture_assrtn1['tumor_types'])
    assert set(test_assrtn1['tissue_types']) == \
        set(fixture_assrtn1['tissue_types'])
    assert test_assrtn1['tier'] == fixture_assrtn1['tier']
    assert test_assrtn1['gene'] == fixture_assrtn1['gene']
    test_assrtn2 = [a for a in test_var['assertions']
                    if 'four' not in a['description']][0]
    fixture_assrtn2 = [a for a in fixture_var['assertions']
                       if 'four' not in a['description']][0]
    assert test_assrtn2['type'] == fixture_assrtn2['type']
    assert set(test_assrtn2['tumor_types']) == \
        set(fixture_assrtn2['tumor_types'])
    assert set(test_assrtn2['tissue_types']) == \
        set(fixture_assrtn2['tissue_types'])
    assert test_assrtn2['tier'] == fixture_assrtn2['tier']
    assert test_assrtn2['gene'] == fixture_assrtn2['gene']


def test_ev_generation(pmkb, ev_fixture):
    """Test generation of evidence objects by PMKB harvester."""
    # get specific ev object
    test_ev = pmkb.get_ev()
    for ev in test_ev:
        if ev['assertions'][0]['description'] == \
                ev_fixture['assertions'][0]['description']:
            test_ev = ev
            break

    assert test_ev['type'] == ev_fixture['type']
    assert len(test_ev['assertions']) == len(ev_fixture['assertions'])
    test_assrtn = test_ev['assertions'][0]
    fixture_assrtn = ev_fixture['assertions'][0]
    assert test_assrtn['type'] == fixture_assrtn['type']
    assert test_assrtn['description'] == fixture_assrtn['description']
    assert test_assrtn['gene']['name'] == fixture_assrtn['gene']['name']
    for fixture_var in fixture_assrtn['variants']:
        var_in_test = False
        for test_var in test_assrtn['variants']:
            if test_var['name'] == fixture_var['name']:
                var_in_test = True
        assert var_in_test
    assert test_assrtn['tier'] == fixture_assrtn['tier']
    assert set(test_assrtn['tumor_types']) == \
        set(fixture_assrtn['tumor_types'])
    assert set(test_assrtn['tissue_types']) == \
        set(fixture_assrtn['tissue_types'])
    assert len(test_ev['source']['citations']) == \
        len(ev_fixture['source']['citations'])


def test_assertion_generation(pmkb, assertion_fixture):
    """Test generation of assertion objects by PMKB harvester."""
    # get specific assertion object
    assertions = pmkb.get_assertions()
    for assertion in assertions:
        if assertion['description'] == assertion_fixture['description']:
            test_assrtn = assertion
            break

    assert test_assrtn['type'] == assertion_fixture['type']
    assert test_assrtn['gene']['name'] == assertion_fixture['gene']['name']
    assert test_assrtn['tier'] == assertion_fixture['tier']
    assert set(test_assrtn['tumor_types']) == \
        set(assertion_fixture['tumor_types'])
    assert set(test_assrtn['tissue_types']) == \
        set(assertion_fixture['tissue_types'])
    assert len(test_assrtn['variants']) == len(assertion_fixture['variants'])
    assert test_assrtn['variants'][0]['name'] == \
        assertion_fixture['variants'][0]['name']
    assert set(test_assrtn['citations']) == set(assertion_fixture['citations'])
