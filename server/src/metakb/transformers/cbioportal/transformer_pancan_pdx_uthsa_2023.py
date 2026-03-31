"""Transformer for the pancan_pdx_uthsa_2023 cBioPortal study."""

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
    "Amino_acids"
]

PATIENT_HEADERS = ["PATIENT_ID", "AGE", "SEX", "ETHNICITY"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "SAMPLE_CLASS",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for pancan_pdx_uthsa_2023 study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "pancan_pdx_uthsa_2023"
    
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
            "amino_acid_change_source": "Amino_acids",
            "additional_columns": {"Sequence_Source": "WES"},
        }
    
    def apply_custom_variant_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace empty/whitespace Center values with 'UTHSA' and strip 'chr' prefix from Chromosome."""
        df["Center"] = df["Center"].replace(r"^\s*\.?\s*$", "UTHSA", regex=True)
        if "Chromosome" in df.columns:
            df["Chromosome"] = df["Chromosome"].astype(str).str.replace("^chr", "", regex=True)
        return df
    
    def apply_custom_sample_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only Tumor samples and drop any variants from Xenograft samples."""
        tumor_df = df[df["SAMPLE_CLASS"] == "Tumor"].reset_index(drop=True)
        tumor_sample_ids = set(tumor_df["SAMPLE_ID"])
        self.variants = self.variants[self.variants["SAMPLE_ID"].isin(tumor_sample_ids)].reset_index(drop=True)
        return tumor_df
