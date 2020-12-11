"""Test the models.biomarkers module."""
from metakb.models.biomarkers import Biomarker, VariationType
import pytest


@pytest.fixture(scope='module')
def protein_substitution():
    """Create a protein substitution biomarker fixture."""
    psub = Biomarker(
        label='BRAF V600E',
        genes=['BRAF'],
        variations=list(),
    )
    return psub


@pytest.fixture(scope='module')
def gene_fusion():
    """Create a gene fusion biomarker fixture."""
    gfus = Biomarker(
        label='BCR-ABL Fusion',
        genes=['BCR', 'ABL'],
        variations=list()
    )
    return gfus


def test_biomarker_attributes(protein_substitution):
    """Test for expected attributes."""
    assert protein_substitution.label == 'BRAF V600E'
    assert 'BRAF' in protein_substitution.genes


@pytest.mark.skip(reason='Need Variant Lexicon to support this class')
def test_biomarker_variation(self):
    """Test for correct Variation in Biomarker."""
    assert len(protein_substitution.variations) == 1
    assert protein_substitution.variations[0].type == \
        VariationType.PROTEIN_SUBSTITUTION
