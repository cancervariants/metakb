"""Test the classes from models.py."""
from metakb.models import Biomarker, VariationType
import pytest


class TestBiomarker:
    """Test the models.Biomarker class."""

    psub = Biomarker(
        label='BRAF V600E',
        genes=['BRAF'],
        variations=list(),
    )

    gfus = Biomarker(
        label='BCR-ABL Fusion',
        genes=['BCR', 'ABL'],
        variations=list()
    )

    def test_biomarker_attributes(self):
        """Test for expected attributes."""
        assert self.psub.label == 'BRAF V600E'
        assert 'BRAF' in self.psub.genes

    @pytest.mark.skip(reason='Need Variant Lexicon to support this class')
    def test_biomarker_variation(self):
        """Test for correct Variation in Biomarker."""
        assert len(self.psub.variations) == 1
        assert self.psub.variations[0].type == \
            VariationType.PROTEIN_SUBSTITUTION
