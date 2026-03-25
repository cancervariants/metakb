"""Transformer for the mbl_pcgp cBioPortal study."""

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
    "Protein_Change",
    "AAChange",
    "Amino_Acid_Change",
]

PATIENT_HEADERS = ["PATIENT_ID", "AGE", "SEX", "ETHNICITY"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for mbl_pcgp study."""

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "mbl_pcgp"

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
        return {"amino_acid_change_source": "Protein_Change"}

    def get_patient_transformations(self) -> dict:
        """Return study-specific patient transformations."""
        # This study already has ETHNICITY, not RACE
        return {"ethnicity_source": "ETHNICITY"}
