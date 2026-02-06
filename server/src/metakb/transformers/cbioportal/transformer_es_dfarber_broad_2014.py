from os import environ

environ["AWS_ACCESS_KEY_ID"] = "dummy"
environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
environ["AWS_SESSION_TOKEN"] = "dummy"

import contextlib
import json
import logging
import re
import time

import pandas as pd
import requests
from tqdm import tqdm

from metakb.transformers.cbioportal.base import (
    cBioportalStudyTransformer,
    cBioportalTransformerBase,
)

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
    "Protein_change",
    "AAChange",
    "Amino_Acid_Change",
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

PATTERN = re.compile(r"^23-")


class cBioportalTransformer(cBioportalStudyTransformer):
    """Transformer for es_dfarber_broad_2014 study.

    This study has extensive custom logic for handling chromosome 23 variants,
    which requires special processing to determine X vs Y chromosome assignment
    in male samples.
    """

    def get_study_name(self) -> str:
        return "es_dfarber_broad_2014"

    def get_mut_headers(self) -> list[str]:
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        return SAMPLE_HEADERS

    def get_patient_transformations(self) -> dict:
        # This study already has ETHNICITY, not RACE
        return {
            "ethnicity_source": "ETHNICITY"
        }

    # ========================================================================
    # Custom Chromosome 23 Logic
    # ========================================================================

    def _flag_rows_chrom_23(self, df):
        """Create "Chrom_23" column, True for those with Chromosome = 23"""
        df["Chrom_23"] = False
        df["Chrom_23"] = df["Chromosome"].astype(str).str.strip().eq("23")
        df.loc[df["Chromosome"] == 23, "Chrom_23"] = True
        return df

    def _chr23_female(self, df):
        """Convert Chromosome 23 to 'X' for rows where SEX is female."""
        chr_col = df["Chromosome"].astype(str).str.strip()
        sex_col = df["SEX"].astype(str).str.upper().str.strip()
        mask = (chr_col == "23") & (sex_col.str.startswith("F"))
        df.loc[mask, "Chromosome"] = "X"
        return df

    def _add_cols_chrom_23_male(self, df):
        """Create "Chr23_X and Chr23_Y" columns, fill with false"""
        df["Chr23_X"] = False
        df["Chr23_Y"] = False
        return df

    def _chr23_to_X(self, variant: str) -> str:
        """Convert a single '23-' prefix in a variant string to 'X-'."""
        return PATTERN.sub("X-", variant) if isinstance(variant, str) else variant

    def _chr23_to_Y(self, variant: str) -> str:
        """Convert a single '23-' prefix in a variant string to 'Y-'."""
        return PATTERN.sub("Y-", variant) if isinstance(variant, str) else variant

    def _test_variant_tokenization(self, variant: str, delay=0.5):
        """Fetch normalized variant info from VICC API for a single variant string."""
        BASE_URL = "http://localhost:8001/variation/"
        HEADERS = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        results = []
        url = f"{BASE_URL}normalize?q={variant}&hgvs_dup_del_mode=default&input_assembly=GRCh37"
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                results.append({"variant": variant, "response": json.dumps(data)})
            else:
                results.append(
                    {
                        "variant": variant,
                        "response": f"Error {response.status_code}: {response.text}",
                    }
                )
        except Exception as e:
            results.append({"variant": variant, "response": f"Exception: {e!s}"})
        time.sleep(delay)
        return pd.DataFrame(results)

    def _check_for_x_variant(self, df, variant):
        """Test tokenization of chromosome 23 variants as X variants"""
        variant_x = self._chr23_to_X(variant)
        x_df = self._test_variant_tokenization(variant_x)
        raw_response = x_df.loc[0, "response"]
        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError:
            return df
        if "variation" not in parsed_response:
            return df

        hgnc_id = None
        with contextlib.suppress(KeyError, IndexError, TypeError):
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0]["hgnc_id"]

        if "x_hgnc_id" not in df.columns:
            df["x_hgnc_id"] = "no_value"
        if "Chr23_X" not in df.columns:
            df["Chr23_X"] = False

        reconstructed = (
            "X-"
            + df["Start_Position"].astype(str).str.strip()
            + "-"
            + df["Reference_Allele"].astype(str).str.strip()
            + "-"
            + df["Tumor_Seq_Allele2"].astype(str).str.strip()
        )

        chrom_col = df["Chromosome"].astype(str).str.strip()
        mask = (chrom_col == "23") & (reconstructed == variant_x)
        df.loc[mask, "Chr23_X"] = True

        if hgnc_id is not None:
            df.loc[mask, "x_hgnc_id"] = hgnc_id

        return df

    def _check_for_y_variant(self, df, variant):
        """Test tokenization of chromosome 23 variants as Y variants"""
        variant_y = self._chr23_to_Y(variant)
        y_df = self._test_variant_tokenization(variant_y)
        raw_response = y_df.loc[0, "response"]
        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError:
            return df
        if "variation" not in parsed_response:
            return df

        hgnc_id = None
        with contextlib.suppress(KeyError, IndexError, TypeError):
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0]["hgnc_id"]

        if "y_hgnc_id" not in df.columns:
            df["y_hgnc_id"] = "no_value"
        if "Chr23_Y" not in df.columns:
            df["Chr23_Y"] = False

        reconstructed = (
            "Y-"
            + df["Start_Position"].astype(str).str.strip()
            + "-"
            + df["Reference_Allele"].astype(str).str.strip()
            + "-"
            + df["Tumor_Seq_Allele2"].astype(str).str.strip()
        )

        chrom_col = df["Chromosome"].astype(str).str.strip()
        mask = (chrom_col == "23") & (reconstructed == variant_y)
        df.loc[mask, "Chr23_Y"] = True

        if hgnc_id is not None:
            df.loc[mask, "y_hgnc_id"] = hgnc_id

        return df

    def _chr23_male(self, df, variant):
        """Driver function for _check_for_x_variant and _check_for_y_variant."""
        if "Chr23_X" not in df.columns:
            df["Chr23_X"] = False
        if "Chr23_Y" not in df.columns:
            df["Chr23_Y"] = False
        df = self._check_for_x_variant(df, variant)
        return self._check_for_y_variant(df, variant)

    def _correct_male_chrom23(self, df):
        """Correct male chromosome 23 variants."""
        df["ambig_chrom"] = "non-ambiguous"

        def update_row(row):
            if (
                row.get("Chrom_23") is True
                and str(row.get("SEX", "")).strip().lower() == "male"
            ):
                if row["Chr23_X"] and not row["Chr23_Y"]:
                    row["Chromosome"] = "X"
                elif row["Chr23_Y"] and not row["Chr23_X"]:
                    row["Chromosome"] = "Y"
                elif row["Chr23_X"] and row["Chr23_Y"]:
                    row["ambig_chrom"] = "XY"
                else:
                    row["ambig_chrom"] = "neither"
            return row

        df = df.apply(update_row, axis=1)
        ambig_rows = df[df["ambig_chrom"].isin(["XY", "neither"])]
        if not ambig_rows.empty:
            pass
        return df

    def _resolve_ambiguous_chromosomes(self, df):
        """Resolve ambiguous Chr23 variants in male samples using HGNC ID matching."""
        if "gene_hgnc_id" not in df.columns:
            df["gene_hgnc_id"] = "no_value"
        if "hgnc_id_match" not in df.columns:
            df["hgnc_id_match"] = "no_value"

        def resolve_row(row):
            if row.get("ambig_chrom") not in ["XY", "neither"]:
                return row

            x_hgnc = str(row.get("x_hgnc_id", "no_value"))
            y_hgnc = str(row.get("y_hgnc_id", "no_value"))
            gene_hgnc = str(row.get("gene_hgnc_id", "no_value"))

            if gene_hgnc == "no_value":
                return row

            if x_hgnc == gene_hgnc and y_hgnc != gene_hgnc:
                row["Chromosome"] = "X"
                row["hgnc_id_match"] = "X"
                row["ambig_chrom"] = "resolved_to_X"
            elif y_hgnc == gene_hgnc and x_hgnc != gene_hgnc:
                row["Chromosome"] = "Y"
                row["hgnc_id_match"] = "Y"
                row["ambig_chrom"] = "resolved_to_Y"
            elif x_hgnc == y_hgnc == gene_hgnc:
                row["hgnc_id_match"] = "both_match"
            else:
                row["hgnc_id_match"] = "neither_match"

            return row

        return df.apply(resolve_row, axis=1)

    # ========================================================================
    # Override transform to include chromosome 23 processing
    # ========================================================================

    def transform(self, harvested_data) -> pd.DataFrame:
        """Custom transformation with chromosome 23 processing."""
        study = self.get_study_name()
        save_loc = cBioportalTransformerBase.setup_save_location(study)

        # Extract data
        self.variants = pd.DataFrame(harvested_data.variants).filter(self.get_mut_headers())
        self.patients = pd.DataFrame(harvested_data.patients).filter(self.get_patient_headers())
        self.samples = pd.DataFrame(harvested_data.samples).filter(self.get_sample_headers())
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # Process variants
        variant_transforms = self.get_variant_transformations()
        self.variants = cBioportalTransformerBase.filter_and_rename_variants(
            self.variants,
            self.get_mut_headers(),
            amino_acid_change_source=variant_transforms.get("amino_acid_change_source")
        )
        self.variants = self.apply_custom_variant_logic(self.variants)
        self.variants = cBioportalTransformerBase.handle_duplicates(
            self.variants, study, save_loc, "mut"
        )

        # Process patients
        patient_transforms = self.get_patient_transformations()
        self.patients = cBioportalTransformerBase.filter_and_rename_patients(
            self.patients,
            self.get_patient_headers(),
            ethnicity_source=patient_transforms.get("ethnicity_source", "RACE"),
            age_source=patient_transforms.get("age_source")
        )
        self.patients = cBioportalTransformerBase.handle_duplicates(
            self.patients, study, save_loc, "patient"
        )

        # Process samples
        sample_transforms = self.get_sample_transformations()
        self.samples = cBioportalTransformerBase.filter_and_rename_samples(
            self.samples,
            self.get_sample_headers(),
            sequence_source=sample_transforms.get("sequence_source")
        )
        self.samples = self.apply_custom_sample_logic(self.samples)
        self.samples = cBioportalTransformerBase.handle_duplicates(
            self.samples, study, save_loc, "samples"
        )

        # Combine dataframes
        combined_df = cBioportalTransformerBase.combine_dataframes(
            self.variants, self.samples, self.patients, self.metadata
        )
        combined_df = cBioportalTransformerBase.handle_duplicates(
            combined_df, study, save_loc, "combined"
        )

        # ========================================================================
        # CUSTOM CHROMOSOME 23 PROCESSING
        # ========================================================================

        # Flag chromosome 23 rows
        combined_df = self._flag_rows_chrom_23(combined_df)

        # Convert female chr23 → X
        combined_df = self._chr23_female(combined_df)

        # Add columns for male chr23 processing
        combined_df = self._add_cols_chrom_23_male(combined_df)

        # Add Gnomad notation BEFORE processing male chr23
        combined_df = cBioportalTransformerBase.add_gnomad_notation(combined_df)

        # Identify unique chr23 variants in males for API testing
        chr23_mask = (
            combined_df["Chrom_23"]
            & (combined_df["SEX"].str.strip().str.lower() == "male")
        )
        unique_chr23_variants = combined_df.loc[chr23_mask, "Gnomad_Notation"].unique()

        # Process each unique chr23 variant
        _logger.info(f"Processing {len(unique_chr23_variants)} unique chr23 variants...")
        for variant in tqdm(unique_chr23_variants, desc="Chr23 variants"):
            combined_df = self._chr23_male(combined_df, variant)

        # Correct male chr23 assignments
        combined_df = self._correct_male_chrom23(combined_df)

        # Resolve ambiguous cases using HGNC ID matching
        combined_df = self._resolve_ambiguous_chromosomes(combined_df)

        # ========================================================================
        # CONTINUE WITH STANDARD PROCESSING
        # ========================================================================

        # Remove patient-variant duplicates
        final_df = cBioportalTransformerBase.remove_patient_variant_duplicates(
            combined_df, study, save_loc
        )

        # Fill missing values
        final_df = cBioportalTransformerBase.fill_missing_values(final_df)

        # Save outputs
        cBioportalTransformerBase.save_study_outputs(final_df, study, save_loc)

        self.final_df = final_df
        return final_df
