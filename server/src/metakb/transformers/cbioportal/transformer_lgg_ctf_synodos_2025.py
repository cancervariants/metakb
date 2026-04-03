"""Transformer for the lgg_ctf_synodos_2025 cBioPortal study."""

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
]

PATIENT_HEADERS = ["PATIENT_ID", "SEX", "RACE"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
    "AGE_AT_BIOPSY",
    "AGE_AT_BIOPSY_MONTHS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for lgg_ctf_synodos_2025 study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "lgg_ctf_synodos_2025"

    def get_genome_build(self) -> str:
        """Return GRCh38 as the genome build for this study."""
        return "GRCh38"

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
        return {
            "additional_columns": {"Sequence_Source": "WGS"},
        }

    def apply_custom_sample_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate decimal AGE from AGE_AT_BIOPSY and AGE_AT_BIOPSY_MONTHS."""
        if "AGE_AT_BIOPSY" in df.columns and "AGE_AT_BIOPSY_MONTHS" in df.columns:
            years = pd.to_numeric(df["AGE_AT_BIOPSY"], errors="coerce")
            months = pd.to_numeric(df["AGE_AT_BIOPSY_MONTHS"], errors="coerce").fillna(
                0
            )
            df["AGE"] = (years + months / 12).round(2)
        else:
            df["AGE"] = "No_Data"
        return df.drop(
            columns=["AGE_AT_BIOPSY", "AGE_AT_BIOPSY_MONTHS"], errors="ignore"
        )
