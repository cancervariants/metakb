"""Transformer for the pancan_mappyacts_2022 cBioPortal study."""

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
    "SEX",
]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "SEQUENCING_PLATFORM",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for pancan_mappyacts_2022 study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "pancan_mappyacts_2022"

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

    def get_sample_transformations(self) -> dict:
        """Return study-specific sample transformations."""
        return {"sequence_source": "SEQUENCING_PLATFORM"}

    def apply_custom_sample_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing ONCOTREE_CODEs using CANCER_TYPE_DETAILED as a fallback."""
        detailed_to_oncotree = {
            "Embryonal Rhabdomyosarcoma": "ERMS",
            "Ewing Sarcoma": "ES",
            "Primitive Neuroectodermal Tumor": "PNET",
            "Alveolar Rhabdomyosarcoma": "ARMS",
            "Diffuse Intrinsic Pontine Glioma": "DIPG",
        }

        if "ONCOTREE_CODE" in df.columns and "CANCER_TYPE_DETAILED" in df.columns:
            missing_mask = df["ONCOTREE_CODE"].isna() | df["ONCOTREE_CODE"].isin(
                ["NA", "No_Data", ""]
            )
            df.loc[missing_mask, "ONCOTREE_CODE"] = df.loc[
                missing_mask, "CANCER_TYPE_DETAILED"
            ].map(detailed_to_oncotree)

        # Patient-specific corrections - sample data has "NA" for cancer type, but patient data has cancer type listed
        map580_mask = df["PATIENT_ID"] == "Map580"
        df.loc[map580_mask, "CANCER_TYPE_DETAILED"] = "Rhabdoid Tumor"
        df.loc[map580_mask, "ONCOTREE_CODE"] = "MRT"

        return df
