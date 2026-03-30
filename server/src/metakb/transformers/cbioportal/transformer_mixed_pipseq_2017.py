"""Transformer for the mixed_pipseq_2017 cBioPortal study."""

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

PATIENT_HEADERS = ["PATIENT_ID", "AGE_TESTING_YEARS", "SEX", "RACE"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for mixed_pipseq_2017 study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "mixed_pipseq_2017"

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

    def get_patient_transformations(self) -> dict:
        """Return study-specific patient transformations."""
        return {"ethnicity_source": "RACE", "age_source": "AGE_TESTING_YEARS"}

    def get_sample_transformations(self) -> dict:
        """Return study-specific sample transformations."""
        return {"sequence_source": "NGS_TEST"}

    def apply_custom_variant_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace empty/whitespace Center values with 'Columbia'."""
        df["Center"] = df["Center"].replace(r"^\s*\.?\s*$", "Columbia", regex=True)
        return df
