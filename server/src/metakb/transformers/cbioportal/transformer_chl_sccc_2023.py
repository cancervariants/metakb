import os
from os import environ
environ["AWS_ACCESS_KEY_ID"]="dummy"
environ["AWS_SECRET_ACCESS_KEY"]="dummy"
environ["AWS_SESSION_TOKEN"]="dummy"

from metakb.transformers.base import (
    Transformer
)
import pandas as pd
import requests
import time
import pprint
from urllib.parse import quote_plus
import re
import json
from tqdm import tqdm
from typing import List

import logging
_logger = logging.getLogger(__name__)

from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)

MUT_HEADERS = ['Hugo_Symbol',
            'Entrez_Gene_Id',
            'Center',
            'NCBI_Build',
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
            'Protein_position',
            'Codons',
            'Protein_Change',
            'AAChange',
            'Amino_Acid_Change']

#this study has both race and ethnicity.
#choose race column and rename ethnicity to match other study data
PATIENT_HEADERS = ['PATIENT_ID',
                   'AGE'
                #    'SEX'
                #    'ETHNICITY'
                ]

SAMPLE_HEADERS = ['PATIENT_ID',
                  'SAMPLE_ID',
                #   'SEQUENCING_PLATFORM',
                  'ONCOTREE_CODE',
                  'CANCER_TYPE',
                  'CANCER_TYPE_DETAILED',
                  'TMB_NONSYNONYMOUS']

PATTERN = re.compile(r'^23-')

class cBioportalTransformer(Transformer):
    """A class for transforming cBioportal Data to the common data model."""

    # TODO: TypeError: Can't instantiate abstract class cBioportalTransformer without an implementation for abstract method '_create_cache'

    def __init__(self):
        super().__init__()
        self.final_df = None

    # TODO: These private methods don't do anything meaningful right towards cbioportal data now
    def _get_therapeutic_substitute_group(self, therapeutic_sub_group_id, therapies, therapy_interaction_type):
        return super()._get_therapeutic_substitute_group(therapeutic_sub_group_id, therapies, therapy_interaction_type)


    def _get_therapy(self, therapy):
        return super()._get_therapy(therapy)

    def _create_cache(self):
        pass



    def transform(self, harvested_data):


        study = "chl_sccc_2023"
        # Get current directory
        loc = os.getcwd()
        # Move one level up and into "transformers"
        base_dir = os.path.join(loc, "..", "transformers")
        # Normalize path
        base_dir = os.path.abspath(base_dir)
        # Create study directory
        study_out_dir = os.path.join(base_dir, "munged_data")
        save_loc = os.path.join(study_out_dir, study)
        os.makedirs(save_loc, exist_ok=True)

        # for harvested_data_obj in harvested_data:
        self.variants = pd.DataFrame(harvested_data.variants).filter(MUT_HEADERS)
        self.patients = pd.DataFrame(harvested_data.patients).filter(PATIENT_HEADERS)
        self.samples = pd.DataFrame(harvested_data.samples).filter(SAMPLE_HEADERS)
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # MUT DF
        # Strip whitespace and rename col
        self.variants.columns = self.variants.columns.str.strip()
        self.variants = self.variants.rename(columns={'Tumor_Sample_Barcode': 'SAMPLE_ID'})
        # self.variants = self.variants.rename(columns={'Protein_Change': 'Amino_Acid_Change'})
        if 'Amino_Acid_Change' not in self.variants.columns:
            self.variants['Amino_Acid_Change'] = "No_data"
        # if "Sequence_Source" not in self.variants.columns:
        #     self.variants["Sequence_Source"] = "No_data"
        self.variants["Center"] = "Weill Cornell Medical College"

        # Check duplicate count
        num_duplicates = self.variants.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.variants[self.variants.duplicated()])
        # save duplicate rows to file
            dupes = self.variants[self.variants.duplicated(keep=False)]
            file_path = os.path.join(save_loc, f'{study}_mut_dupes.csv')
            dupes.to_csv(file_path, index=False)
        # remove duplicates, but keep first occurrence
            self.variants = self.variants.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.variants.shape}")
        else:
            print("No duplicate rows found.")

        # PATIENT DF
        # Rename RACE → ETHNICITY if present
        # if "RACE" in self.patients.columns:
        #     self.patients = self.patients.rename(columns={"RACE": "ETHNICITY"})
        if 'ETHNICITY' not in self.patients.columns:
            self.patients['ETHNICITY'] = "No_data"
        if 'SEX' not in self.patients.columns:
            self.patients['SEX'] = "No_data"
        # self.patients = self.patients.rename(columns={'AGE_TESTING_YEARS': 'AGE'})
        # self.patients = self.patients.rename(columns={'INFERRED_ETHNICITY': 'ETHNICITY'})
        # Check duplicate count
        num_duplicates = self.patients.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.patients[self.patients.duplicated()])
        # save duplicate rows to file
            dupes = self.patients[self.patients.duplicated(keep=False)]
            file_path = os.path.join(save_loc, f'{study}_patient_dupes.csv')
            dupes.to_csv(file_path, index=False)
        # assign age to NAs
            # self.patients["AGE"] = self.patients["AGE"].replace(r'^\s*$', pd.NA, regex=True).fillna("<21")
        # remove duplicates, but keep first occurrence
            self.patients = self.patients.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.patients.shape}")
        else:
            print("No duplicate rows found.")

        # SAMPLE DF
        # Check duplicate count
        num_duplicates = self.samples.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # self.samples = self.samples.rename(columns={'SEQUENCING_PLATFORM': 'Sequence_Source'})
        # self.samples["Sequence_Source"] = self.samples["Sequence_Source"].str.replace(" + RNAseq", "", regex=False)
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.samples[self.samples.duplicated()])
        # save duplicate rows to file
            dupes = self.samples[self.samples.duplicated(keep=False)]
            file_path = os.path.join(save_loc, f'{study}_samples_dupes.csv')
            dupes.to_csv(file_path, index=False)

        # remove duplicates, but keep first occurrence
            self.samples = self.samples.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.samples.shape}")
        else:
            print("No duplicate rows found.")

        # combine dataframes
        init_combined_df = self.variants.merge(self.samples, on='SAMPLE_ID', how='left')
        combined_df = init_combined_df.merge(self.patients, on='PATIENT_ID', how='left')

        # add study_id column
        # study_id = self.metadata.iloc[0, 0]
        # study_id = study_id.replace('cancer_study_identifier: ', '')
        combined_df['STUDY_ID'] = "chl_sccc_2023"

        # remove duplicates from combined dataframe
        # Check duplicate count
        num_duplicates = combined_df.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(combined_df[combined_df.duplicated()])
        # remove duplicates, but keep first occurrence
            combined_df = combined_df.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {combined_df.shape}")
        else:
            print("No duplicate rows found.")

        # construct Gnomad variant ID column
        combined_df["Gnomad_Notation"] = combined_df.apply(
            lambda row: f"{row['Chromosome']}-{row['Start_Position']}-{row['Reference_Allele']}-{row['Tumor_Seq_Allele2']}",
            axis=1
        )

        # remove variant dupes per patient
        # find duplicated (PATIENT_ID, Gnomad_Notation) pairs
        dupe_mask = combined_df.duplicated(subset=["PATIENT_ID", "Gnomad_Notation"], keep="first")
        # new DataFrame with the duplicated rows
        patient_variant_dupes = combined_df[dupe_mask]
        # remove those rows from the original DataFrame
        final_df = combined_df[~dupe_mask]
        # write removed rows to file
        file_path = os.path.join(save_loc, f'{study}_patient_variant_dupes.csv')
        patient_variant_dupes.to_csv(file_path, index=False)
        # print the number of rows removed
        print(f"Removed {patient_variant_dupes.shape[0]} rows with duplicated Gnomad_Notation per PATIENT_ID.")
        # post_validation_df_cleaned.to_csv("final_cbp_df.csv", index=False)


        #filling NaNs
        final_df = final_df.fillna("No_Data")
        final_df = final_df.replace(r'^\s*$', pd.NA, regex=True).fillna("No_Data")
        file_path = os.path.join(save_loc, f'{study}_final_no_NAs.csv')
        final_df.to_csv(file_path, index=False)


        self.final_df = final_df


        # Save final DF with extra logic columns
        file_path = os.path.join(save_loc, f'{study}_final_df_logic_cols.csv')
        final_df.to_csv(file_path, index=False)

        #Drop unnecessary columnns
        # final_df = final_df.drop(['SAMPLE_CLASS',
        #                           'temp_Gnomad_Notation',
        #                           'Chrom_23',
        #                           'Chr23_X',
        #                           'Chr23_Y',
        #                           'x_hgnc_id',
        #                           'y_hgnc_id',
        #                           'ambig_chrom',
        #                           'gene_hgnc_id',
        #                           'hgnc_id_match'], axis=1) # or df.drop(columns=['col2', 'col4'])

        file_path = os.path.join(save_loc, f'{study}_final_df_clean.csv')
        final_df.to_csv(file_path, index=False)

        return final_df



        #Convert CBP data df to a list of dictionaries (each row its own dictionary)
        # genes = df.to_dict(orient='records')
        #Take just a subset to test
        # sub_genes = genes[0:5]


        # TODO: Method's for mapping cleaned up data to Common Data Model format
        # civic.py transformer may have some logic to reuse here
        # test fixture is the end result for a single entry
        #
        # TODO: Output one CDM per study or one CDM total?

        pass
