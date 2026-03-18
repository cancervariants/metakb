"""Transformer for the es_dfarber_broad_2014 cBioPortal study."""

import contextlib
import json
import logging
import re
import time

import pandas as pd
import requests
from tqdm import tqdm

from metakb.harvesters.cbioportal import CBioPortalHarvestedData
from metakb.transformers.cbioportal.base import (
    CBioPortalStudyTransformer,
    CBioPortalTransformerBase,
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
CHROM_23 = "23"
CHROM_23_INT = 23
HTTP_OK = 200


class CBioPortalTransformer(CBioPortalStudyTransformer):
    """Transformer for es_dfarber_broad_2014 study.

    This study has extensive custom logic for handling chromosome 23 variants,
    which requires special processing to determine X vs Y chromosome assignment
    in male samples.
    """

    def get_study_name(self) -> str:
        """Return the study identifier."""
        return "es_dfarber_broad_2014"

    def get_mut_headers(self) -> list[str]:
        """Return the list of mutation/variant column headers to keep."""
        return MUT_HEADERS

    def get_patient_headers(self) -> list[str]:
        """Return the list of patient column headers to keep."""
        return PATIENT_HEADERS

    def get_sample_headers(self) -> list[str]:
        """Return the list of sample column headers to keep."""
        return SAMPLE_HEADERS

    def get_patient_transformations(self) -> dict:
        """Return sample column transformation mappings."""
        # This study already has ETHNICITY, not RACE
        return {"ethnicity_source": "ETHNICITY"}

    # ========================================================================
    # Custom Chromosome 23 Logic
    # ========================================================================

    def _flag_rows_chrom_23(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create "Chrom_23" column, True for those with Chromosome = 23"""
        df["Chrom_23"] = False
        df["Chrom_23"] = df["Chromosome"].astype(str).str.strip().eq(CHROM_23)
        df.loc[df["Chromosome"] == CHROM_23_INT, "Chrom_23"] = True
        return df

    def _chr23_female(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Chromosome 23 to 'X' for rows where SEX is female."""
        chr_col = df["Chromosome"].astype(str).str.strip()
        sex_col = df["SEX"].astype(str).str.upper().str.strip()
        mask = (chr_col == CHROM_23) & (sex_col.str.startswith("F"))
        df.loc[mask, "Chromosome"] = "X"
        return df

    def _add_cols_chrom_23_male(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create "Chr23_X and Chr23_Y" columns, fill with false"""
        df["Chr23_X"] = False
        df["Chr23_Y"] = False
        return df

    def _chr23_to_x(self, variant: str) -> str:
        """Convert a single '23-' prefix in a variant string to 'X-'."""
        return PATTERN.sub("X-", variant) if isinstance(variant, str) else variant

    def _chr23_to_y(self, variant: str) -> str:
        """Convert a single '23-' prefix in a variant string to 'Y-'."""
        return PATTERN.sub("Y-", variant) if isinstance(variant, str) else variant

    def _test_variant_tokenization(
        self, variant: str, delay: float = 0.5
    ) -> pd.DataFrame:
        """Fetch normalized variant info from VICC API for a single variant string."""
        base_url = "http://localhost:8001/variation/"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        results = []
        url = f"{base_url}normalize?q={variant}&hgvs_dup_del_mode=default&input_assembly=GRCh37"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == HTTP_OK:
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

    def _check_for_x_variant(self, df: pd.DataFrame, variant: str) -> pd.DataFrame:
        """Test tokenization of chromosome 23 variants as X variants"""
        variant_x = self._chr23_to_x(variant)
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
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0][
                "hgnc_id"
            ]

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
        mask = (chrom_col == CHROM_23) & (reconstructed == variant_x)
        df.loc[mask, "Chr23_X"] = True

        if hgnc_id is not None:
            df.loc[mask, "x_hgnc_id"] = hgnc_id

        return df

    def _check_for_y_variant(self, df: pd.DataFrame, variant: str) -> pd.DataFrame:
        """Test tokenization of chromosome 23 variants as Y variants"""
        variant_y = self._chr23_to_y(variant)
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
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0][
                "hgnc_id"
            ]

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
        mask = (chrom_col == CHROM_23) & (reconstructed == variant_y)
        df.loc[mask, "Chr23_Y"] = True

        if hgnc_id is not None:
            df.loc[mask, "y_hgnc_id"] = hgnc_id

        return df

    def _chr23_male(self, df: pd.DataFrame, variant: str) -> pd.DataFrame:
        """Driver function for _check_for_x_variant and _check_for_y_variant."""
        if "Chr23_X" not in df.columns:
            df["Chr23_X"] = False
        if "Chr23_Y" not in df.columns:
            df["Chr23_Y"] = False
        df = self._check_for_x_variant(df, variant)
        return self._check_for_y_variant(df, variant)

    def _test_gene_tokenization(self, gene: str, delay: float = 0.5) -> pd.DataFrame:
        """Fetch normalized gene info from VICC API for a single gene."""
        base_url = "https://normalize.cancervariants.org/gene/"
        headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        results = []
        url = f"{base_url}normalize?q={gene}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == HTTP_OK:
                data = response.json()
                results.append({"gene": gene, "response": json.dumps(data)})
            else:
                results.append(
                    {
                        "gene": gene,
                        "response": f"Error {response.status_code}: {response.text}",
                    }
                )
        except Exception as e:
            results.append({"gene": gene, "response": f"Exception: {e!s}"})
        time.sleep(delay)
        return pd.DataFrame(results)

    def _populate_gene_hgnc_col(
        self, gene_list: list[str], df: pd.DataFrame, col: str = "temp_gene_hgnc_id"
    ) -> pd.DataFrame:
        """Populate gene hgnc id column for chr23 male variants."""
        if col not in df.columns:
            df[col] = "untested"
        for gene in tqdm(gene_list, desc="Processing genes"):
            gene_df = self._test_gene_tokenization(gene)
            raw_response = gene_df.loc[0, "response"]
            try:
                parsed_response = json.loads(raw_response)
            except json.JSONDecodeError:
                continue
            if "gene" not in parsed_response:
                continue
            try:
                hgnc_id = parsed_response["gene"]["id"].split(":")[-1]
            except (KeyError, IndexError, TypeError):
                continue
            df.loc[
                (df["Chrom_23"])
                & (df["SEX"].str.strip().str.lower() == "male")
                & (df["Hugo_Symbol"].str.strip() == gene.strip()),
                col,
            ] = hgnc_id
        return df

    def _correct_male_chrom23(self, df: pd.DataFrame) -> pd.DataFrame:
        """Correct male chromosome 23 variants."""
        df["ambig_chrom"] = "non-ambiguous"

        def update_row(row: pd.Series) -> pd.Series:
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

    def _resolve_ambiguous_chromosomes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resolve ambiguous Chr23 variants using x/y hgnc_id and temp_gene_hgnc_id."""
        if "ambig_chrom" not in df.columns:
            return df

        for idx, row in df[df["ambig_chrom"].isin(["XY", "neither"])].iterrows():
            x_id = str(row.get("x_hgnc_id", "no_value")).strip()
            y_id = str(row.get("y_hgnc_id", "no_value")).strip()
            gene_id = str(row.get("temp_gene_hgnc_id", "untested")).strip()

            if gene_id not in ("untested", "no_value", ""):
                if x_id == gene_id and y_id != gene_id:
                    df.at[idx, "Chromosome"] = "X"
                    df.at[idx, "ambig_chrom"] = "resolved_to_X"
                elif y_id == gene_id and x_id != gene_id:
                    df.at[idx, "Chromosome"] = "Y"
                    df.at[idx, "ambig_chrom"] = "resolved_to_Y"
            elif x_id != "no_value" and y_id == "no_value":
                df.at[idx, "Chromosome"] = "X"
                df.at[idx, "ambig_chrom"] = "resolved_to_X"
            elif y_id != "no_value" and x_id == "no_value":
                df.at[idx, "Chromosome"] = "Y"
                df.at[idx, "ambig_chrom"] = "resolved_to_Y"

        return df

    # ========================================================================
    # Override transform to include chromosome 23 processing
    # ========================================================================

    def transform(self, harvested_data: CBioPortalHarvestedData) -> pd.DataFrame:
        """Transform study data with custom chromosome 23 processing."""
        study = self.get_study_name()
        save_loc = CBioPortalTransformerBase.setup_save_location(study)

        # Extract data
        self.variants = pd.DataFrame(harvested_data.variants).filter(
            self.get_mut_headers()
        )
        self.patients = pd.DataFrame(harvested_data.patients).filter(
            self.get_patient_headers()
        )
        self.samples = pd.DataFrame(harvested_data.samples).filter(
            self.get_sample_headers()
        )
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # Process variants
        variant_transforms = self.get_variant_transformations()
        self.variants = CBioPortalTransformerBase.filter_and_rename_variants(
            self.variants,
            self.get_mut_headers(),
            amino_acid_change_source=variant_transforms.get("amino_acid_change_source"),
        )
        self.variants = self.apply_custom_variant_logic(self.variants)
        self.variants = CBioPortalTransformerBase.handle_duplicates(
            self.variants, study, save_loc, "mut"
        )

        # Process patients
        patient_transforms = self.get_patient_transformations()
        self.patients = CBioPortalTransformerBase.filter_and_rename_patients(
            self.patients,
            self.get_patient_headers(),
            ethnicity_source=patient_transforms.get("ethnicity_source", "RACE"),
            age_source=patient_transforms.get("age_source"),
        )
        self.patients = CBioPortalTransformerBase.handle_duplicates(
            self.patients, study, save_loc, "patient"
        )

        # Process samples
        sample_transforms = self.get_sample_transformations()
        self.samples = CBioPortalTransformerBase.filter_and_rename_samples(
            self.samples,
            self.get_sample_headers(),
        )
        self.samples = self.apply_custom_sample_logic(self.samples)
        self.samples = CBioPortalTransformerBase.handle_duplicates(
            self.samples, study, save_loc, "samples"
        )

        # Combine dataframes
        combined_df = CBioPortalTransformerBase.combine_dataframes(
            self.variants, self.samples, self.patients, self.metadata
        )

        # Resolve Sequence_Source (mutations first, then sample fallback)
        combined_df = CBioPortalTransformerBase.resolve_sequence_source(
            combined_df,
            fallback_column=sample_transforms.get("sequence_source"),
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
        combined_df = CBioPortalTransformerBase.add_gnomad_notation(combined_df)

        # Identify unique chr23 variants in males for API testing
        chr23_mask = combined_df["Chrom_23"] & (
            combined_df["SEX"].str.strip().str.lower() == "male"
        )
        unique_chr23_variants = combined_df.loc[chr23_mask, "Gnomad_Notation"].unique()

        # Process each unique chr23 variant
        _logger.info(
            "Processing %d unique chr23 variants...", len(unique_chr23_variants)
        )
        for variant in tqdm(unique_chr23_variants, desc="Chr23 variants"):
            combined_df = self._chr23_male(combined_df, variant)

        # Correct male chr23 assignments
        combined_df = self._correct_male_chrom23(combined_df)

        # Populate temp_gene_hgnc_id and resolve ambiguous cases
        combined_df["temp_gene_hgnc_id"] = "untested"
        gene_list = (
            combined_df[
                (combined_df["SEX"].str.lower() == "male") & (combined_df["Chrom_23"])
            ]["Hugo_Symbol"]
            .dropna()
            .tolist()
        )
        combined_df = self._populate_gene_hgnc_col(
            gene_list, combined_df, col="temp_gene_hgnc_id"
        )
        combined_df = self._resolve_ambiguous_chromosomes(combined_df)

        # Handle duplicates after chromosome 23 resolution
        combined_df = CBioPortalTransformerBase.handle_duplicates(
            combined_df, study, save_loc, "combined"
        )

        # ========================================================================
        # CONTINUE WITH STANDARD PROCESSING
        # ========================================================================

        # Remove patient-variant duplicates
        final_df = CBioPortalTransformerBase.remove_patient_variant_duplicates(
            combined_df, study, save_loc
        )

        # Fill missing values
        final_df = CBioPortalTransformerBase.fill_missing_values(final_df)

        # Save full file with logic columns before dropping
        CBioPortalTransformerBase.save_study_outputs(final_df, study, save_loc)

        # Drop chromosome 23 processing columns
        cols_to_drop = [
            "SAMPLE_CLASS",
            "Chrom_23",
            "Chr23_X",
            "Chr23_Y",
            "x_hgnc_id",
            "y_hgnc_id",
            "ambig_chrom",
            "temp_gene_hgnc_id",
        ]
        final_df = final_df.drop(
            columns=[c for c in cols_to_drop if c in final_df.columns]
        )

        self.final_df = final_df
        return final_df
