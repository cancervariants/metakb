from metakb.transformers.base import (
    Transformer 
)
import pandas as pd

MUT_HEADERS = {'Hugo_Symbol',
            'Chromosome',
            'Start_Position', 
            'End_Position',
            'Consequence',
            'Variant_Classification',
            'Variant_Type',
            'Reference_Allele',
            'Tumor_Seq_Allele2',
            'Tumor_Sample_Barcode',
            'Sequence_Source',
            'HGVSc',
            'HGVSp',
            'HGVSp_Short',
            'Transcript_ID',
            'RefSeq',
            'Protein_position'}

PATIENT_HEADERS = {'PATIENT_ID',
                   'AGE',
                   'SEX',
                   'ETHNICITY',
                   'Consequence'}

SAMPLE_HEADERS = {'PATIENT_ID',
                  'SAMPLE_ID',
                  'SAMPLE_CLASS',
                  'ONCOTREE_CODE',
                  'CANCER_TYPE',
                  'CANCER_TYPE_DETAIL',
                  'TMB_NONSYNONYMOUS'}

class cBioportalTransformer(Transformer):
    """A class for transforming cBioportal Data to the common data model."""

    # TODO: TypeError: Can't instantiate abstract class cBioportalTransformer without an implementation for abstract method '_create_cache'

    def __init__(self):
        pass

    # TODO: These private methods don't do anything meaningful right towards cbioportal data now
    def _get_therapeutic_substitute_group(self, therapeutic_sub_group_id, therapies, therapy_interaction_type):
        return super()._get_therapeutic_substitute_group(therapeutic_sub_group_id, therapies, therapy_interaction_type)

    def _get_therapy(self, therapy):
        return super()._get_therapy(therapy)
    
    def _create_cache():
        pass

    def transform(self, harvested_data):

        # for harvested_data_obj in harvested_data:
        self.variants = pd.DataFrame(harvested_data.variants).filter(MUT_HEADERS)
        self.patients = pd.DataFrame(harvested_data.patients).filter(PATIENT_HEADERS)
        self.samples = pd.DataFrame(harvested_data.samples).filter(SAMPLE_HEADERS)
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # TODO: Heather's methods for data cleanup, normalization, and formating to common data model goes here

        # def _chr23_male():
        #   relevant code
        # 
        # def _add_cols_chrom_23_male():
        #   relevant code 
        # 
        # def _check_for_x_variant():
        #   relevant code
        #
        # def _check_for_y_variant():
        #   relevant code
        #
        # def _test_tokenization():
        #   relevant code

        # self.data = _create_combined_df(self,relevant data frames)
        # self.data = _chr23_male(self,relevant data frame)
        

        # TODO: Method's for mapping cleaned up data to Common Data Model format
        # civic.py transformer may have some logic to reuse here
        # test fixture is the end result for a single entry
        #   
        # TODO: Output one CDM per study or one CDM total?

        pass