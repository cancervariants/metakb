"""Transformer for the nbl_target_2018 cBioPortal study."""

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
        return "pancan_mappyacts_2022"
    
    def get_genome_build(self) -> str:
        return "GRCh38"  # This study uses GRCh38

    def get_mut_headers(self) -> list[str]:
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        return SAMPLE_HEADERS

    def get_sample_transformations(self) -> dict:
        return {
            "sequence_source": "SEQUENCING_PLATFORM"
        }
