"""Transformer for the all_phase2_target_2018_pub cBioPortal study."""

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
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for all_phase2_target_2018_pub study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "all_phase2_target_2018_pub"

    def get_mut_headers(self) -> list[str]:
        """Return the list of mutation/variant column headers to keep."""
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        """Return the list of patient column headers to keep."""
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        """Return the list of sample column headers to keep."""
        return SAMPLE_HEADERS
