"""Transformer for the pediatric_dkfz_2017 cBioPortal study."""

import pandas as pd

from metakb.transformers.cbioportal.base import CBioPortalStudyTransformer

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
    "Amino_Acid_Change",
]

PATIENT_HEADERS = ["PATIENT_ID", "AGE", "SEX", "RACE"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "SAMPLE_CLASS",
    "ONCOTREE_CODE_CANCER_TYPE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
    "SEQUENCING_TYPE"
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for pediatric_dkfz_2017 study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "pediatric_dkfz_2017"

    def get_mut_headers(self) -> list[str]:
        """Return the list of mutation/variant column headers to keep."""
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        """Return the list of patient column headers to keep."""
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        """Return the list of sample column headers to keep."""
        return SAMPLE_HEADERS

    def get_variant_transformations(self) -> dict:
        """Return study-specific variant transformations."""
        return {"additional_columns": {"Sequence_Source": "No_data"}}

    def get_sample_transformations(self) -> dict:
        """Return study-specific sample transformations."""
        return {"sequence_source": "SEQUENCING_TYPE"}

    def apply_custom_variant_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply DKFZ-specific variant transformations."""
        # Replace empty/whitespace Center values with 'DKFZ'
        df["Center"] = df["Center"].replace(r"^\s*\.?\s*$", "DKFZ", regex=True)

        # Fix chromosome for RAB36 gene
        df.loc[
            (df["Hugo_Symbol"] == "RAB36") & (df["Chromosome"] == "NA"),
            "Chromosome",
        ] = 22

        return df
