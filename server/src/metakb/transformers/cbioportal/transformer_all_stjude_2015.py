"""Transformer for the all_stjude_2015 cBioPortal study."""

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
    "Amino_Acid_Change",
]

PATIENT_HEADERS = ["PATIENT_ID", "AGE", "SEX", "RACE"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "GENE_PANEL",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for all_stjude_2015 study."""

    def get_study_name(self) -> str:
        """Return the cBioPortal study identifier."""
        return "all_stjude_2015"

    def get_mut_headers(self) -> list[str]:
        """Return mutation data column headers."""
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        """Return patient data column headers."""
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        """Return sample data column headers."""
        return SAMPLE_HEADERS

    def get_sample_transformations(self) -> dict:
        """Return sample column transformation mappings."""
        return {"sequence_source": "GENE_PANEL"}
