from os import environ

environ["AWS_ACCESS_KEY_ID"] = "dummy"
environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
environ["AWS_SESSION_TOKEN"] = "dummy"

import logging

import pandas as pd

from metakb.transformers.cbioportal.base import (
    cBioportalStudyTransformer,
    cBioportalTransformerBase,
)

_logger = logging.getLogger(__name__)


MUT_HEADERS = [
    "Hugo_Symbol",
    "Entrez_Gene_Id",
    "Center",
    "NCBI_Build",
    "Chromosome",
    "Start_Position",
    "End_Position",
    "Consequence",
    "Variant_Classification",
    "Variant_Type",
    "Reference_Allele",
    "Tumor_Seq_Allele2",
    "Tumor_Sample_Barcode",
    "Sequence_Source",
    "HGVSc",
    "HGVSp",
    "HGVSp_Short",
    "Transcript_ID",
    "RefSeq",
    "Protein_position",
    "Codons",
    "Protein_Change",
    "AAChange",
    "Amino_Acid_Change",
]

PATIENT_HEADERS = [
    "PATIENT_ID",
    "AGE",
]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class cBioportalTransformer(cBioportalStudyTransformer):
    """Transformer for chl_sccc_2023 study.

    This study has some unique characteristics:
    - Missing SEX and ETHNICITY columns in patient data
    - No metadata with study identifier
    - Center needs to be set
    """

    def get_study_name(self) -> str:
        return "chl_sccc_2023"

    def get_mut_headers(self) -> list[str]:
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        return SAMPLE_HEADERS

    def get_variant_transformations(self) -> dict:
        return {
            "center_value": "Weill Cornell Medical College"
        }

    def transform(self, harvested_data) -> pd.DataFrame:
        """Override transform to handle hardcoded study ID.

        This study doesn't have a proper metadata field with study identifier,
        so we need to override the combine step.
        """
        study = self.get_study_name()
        save_loc = cBioportalTransformerBase.setup_save_location(study)

        # Extract data
        self.variants = pd.DataFrame(harvested_data.variants).filter(self.get_mut_headers())
        self.patients = pd.DataFrame(harvested_data.patients).filter(self.get_patient_headers())
        self.samples = pd.DataFrame(harvested_data.samples).filter(self.get_sample_headers())
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # Process variants
        variant_transforms = self.get_variant_transformations()
        self.variants = cBioportalTransformerBase.filter_and_rename_variants(
            self.variants,
            self.get_mut_headers(),
            amino_acid_change_source=variant_transforms.get("amino_acid_change_source")
        )

        if "center_value" in variant_transforms:
            self.variants["Center"] = variant_transforms["center_value"]

        self.variants = self.apply_custom_variant_logic(self.variants)
        self.variants = cBioportalTransformerBase.handle_duplicates(
            self.variants, study, save_loc, "mut"
        )

        # Process patients
        patient_transforms = self.get_patient_transformations()
        self.patients = cBioportalTransformerBase.filter_and_rename_patients(
            self.patients,
            self.get_patient_headers(),
            ethnicity_source=patient_transforms.get("ethnicity_source", "RACE"),
            age_source=patient_transforms.get("age_source")
        )
        self.patients = cBioportalTransformerBase.handle_duplicates(
            self.patients, study, save_loc, "patient"
        )

        # Process samples
        sample_transforms = self.get_sample_transformations()
        self.samples = cBioportalTransformerBase.filter_and_rename_samples(
            self.samples,
            self.get_sample_headers(),
            sequence_source=sample_transforms.get("sequence_source")
        )
        self.samples = self.apply_custom_sample_logic(self.samples)
        self.samples = cBioportalTransformerBase.handle_duplicates(
            self.samples, study, save_loc, "samples"
        )

        # Combine dataframes - USE HARDCODED STUDY ID
        combined_df = cBioportalTransformerBase.combine_dataframes(
            self.variants,
            self.samples,
            self.patients,
            self.metadata,
            study_id_override="chl_sccc_2023"  # Hardcoded study ID
        )
        combined_df = cBioportalTransformerBase.handle_duplicates(
            combined_df, study, save_loc, "combined"
        )

        # Add Gnomad notation
        combined_df = cBioportalTransformerBase.add_gnomad_notation(combined_df)

        # Remove patient-variant duplicates
        final_df = cBioportalTransformerBase.remove_patient_variant_duplicates(
            combined_df, study, save_loc
        )

        # Fill missing values
        final_df = cBioportalTransformerBase.fill_missing_values(final_df)

        # Save outputs
        cBioportalTransformerBase.save_study_outputs(final_df, study, save_loc)

        self.final_df = final_df
        return final_df
