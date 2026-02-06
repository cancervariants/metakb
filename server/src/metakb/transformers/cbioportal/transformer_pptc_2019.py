import os
from os import environ
from pathlib import Path

environ["AWS_ACCESS_KEY_ID"] = "dummy"
environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
environ["AWS_SESSION_TOKEN"] = "dummy"

import logging
import re

import pandas as pd

from metakb.transformers.cbioportal.base import cBioportalStudyTransformer

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
    "Amino_Acid_Change",
    "User_Amino_Acid_Change",
]

PATIENT_HEADERS = ["PATIENT_ID", "AGE", "SEX", "INFERRED_ETHNICITY"]

SAMPLE_HEADERS = [
    "PATIENT_ID",
    "SAMPLE_ID",
    "ONCOTREE_CODE",
    "CANCER_TYPE",
    "CANCER_TYPE_DETAILED",
    "TMB_NONSYNONYMOUS",
]


class cBioportalTransformer(cBioportalStudyTransformer):
    """Transformer for pptc_2019 study."""

    def get_study_name(self) -> str:
        return "pptc_2019"

    def get_mut_headers(self) -> list[str]:
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        return SAMPLE_HEADERS

    def get_variant_transformations(self) -> dict:
        return {
            "amino_acid_change_source": "User_Amino_Acid_Change",
            "additional_columns": {
                "Sequence_Source": "No_data"
            }
        }

    def get_patient_transformations(self) -> dict:
        return {
            "ethnicity_source": "INFERRED_ETHNICITY"
        }
