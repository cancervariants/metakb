"""Higher order transformer for cBioPortal study transformation"""
# metakb/transformers/cbioportal/base.py

from __future__ import annotations

import importlib
import json
import logging
import time
from abc import abstractmethod
from os import environ
from pathlib import Path
from typing import Any

import requests

environ["AWS_ACCESS_KEY_ID"] = "dummy"
environ["AWS_SECRET_ACCESS_KEY"] = "dummy"  # noqa: S105
environ["AWS_SESSION_TOKEN"] = "dummy"  # noqa: S105

import pandas as pd
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)
from tqdm import tqdm

from metakb.harvesters.cbioportal import CBioPortalHarvestedData
from metakb.transformers.base import Transformer

logger = logging.getLogger(__name__)

# -----------------------------
# Map study → transformer file
# -----------------------------
STUDY_TO_MODULE = {
    "pptc_2019": "metakb.transformers.cbioportal.transformer_pptc_2019",
    "all_phase2_target_2018_pub": "metakb.transformers.cbioportal.transformer_all_phase2_target_2018_pub",
    "rt_target_2018_pub": "metakb.transformers.cbioportal.transformer_rt_target_2018_pub",
    "wt_target_2018_pub": "metakb.transformers.cbioportal.transformer_wt_target_2018_pub",
    "aml_target_2018_pub": "metakb.transformers.cbioportal.transformer_aml_target_2018_pub",
    "nbl_target_2018_pub": "metakb.transformers.cbioportal.transformer_nbl_target_2018_pub",
    "pediatric_dkfz_2017": "metakb.transformers.cbioportal.transformer_pediatric_dkfz_2017",
    "mixed_pipseq_2017": "metakb.transformers.cbioportal.transformer_mixed_pipseq_2017",
    "all_stjude_2016": "metakb.transformers.cbioportal.transformer_all_stjude_2016",
    "all_stjude_2015": "metakb.transformers.cbioportal.transformer_all_stjude_2015",
    "es_dfarber_broad_2014": "metakb.transformers.cbioportal.transformer_es_dfarber_broad_2014",
    "es_iocurie_2014": "metakb.transformers.cbioportal.transformer_es_iocurie_2014",
    "mbl_pcgp": "metakb.transformers.cbioportal.transformer_mbl_pcgp",
    "pancan_mappyacts_2022": "metakb.transformers.cbioportal.transformer_pancan_mappyacts_2022",
    "chl_sccc_2023": "metakb.transformers.cbioportal.transformer_chl_sccc_2023",
    "pancan_pdx_uthsa_2023": "metakb.transformers.cbioportal.transformer_pancan_pdx_uthsa_2023",
}

# Genome build is defined per-study via get_genome_build() in each study transformer.
# Default is GRCh37. Override get_genome_build() in a study transformer for GRCh38.

DEFAULT_GENOME_BUILD = "GRCh37"

TRANSFORMER_CLASS_NAME = "CBioPortalTransformer"


class CBioPortalTransformerBase(Transformer):
    """Orchestrates per-study cBioportal transformers AND performs centralized
    gene mapping via the VICC normalizers.
    """

    def __init__(
        self,
        study_to_module: dict[str, str] | None = None,
        transformer_class_name: str = TRANSFORMER_CLASS_NAME,
        rate_limit_delay: float = 0.1,  # 100ms between API calls
    ) -> None:
        """Initialize cBioPortal transformer base orchestrator.

        :param study_to_module: Mapping of study names to transformer module paths
        :param transformer_class_name: Name of the transformer class to load from each module
        :param rate_limit_delay: Delay in seconds between API calls
        """
        super().__init__()  # initialize Transformer's internals
        self.study_to_module = study_to_module or STUDY_TO_MODULE
        self.transformer_class_name = transformer_class_name
        self.rate_limit_delay = rate_limit_delay

        # Collect mappable genes + QC per study so we can write combined outputs at the end
        self.mappable_genes_by_study: dict[str, list[MappableConcept]] = {}
        self.mappable_variants_by_study: dict[str, list[MappableConcept]] = {}
        self.gene_qc_by_study: dict[str, dict[str, Any]] = {}
        self.variant_qc_by_study: dict[str, dict[str, Any]] = {}

        # Frequency results stores
        self.freq_results_this_study: dict[str, list[dict]] = {}
        self.freq_results_all_studies: list[dict] = []
        self.freq_results_cancer_this_study: dict[str, list[dict]] = {}
        self.freq_results_cancer_all_studies: list[dict] = []

        # Track failed normalizations
        self.failed_genes: list[dict[str, str]] = []
        self.failed_variants: list[dict[str, str]] = []

        # Cache for normalized genes and variants to avoid duplicate API calls
        self.gene_cache: dict[
            str, tuple[Any, str | None]
        ] = {}  # symbol -> (response, normalized_id)
        self.variant_cache: dict[str, str | None] = {}  # variant_notation -> vrs_id

        self.current_genome_build: str = DEFAULT_GENOME_BUILD

    # ======================================================
    #  Required abstract methods from Transformer
    # ======================================================

    def _create_cache(self) -> None:
        return None

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,  # noqa: ARG002
        therapies: list[MappableConcept],  # noqa: ARG002
        therapy_interaction_type: str,  # noqa: ARG002
    ) -> None:
        return None

    def _get_therapy(self, therapy: dict) -> None:  # noqa: ARG002
        return None

    def transform(self, harvested_data: CBioPortalHarvestedData) -> pd.DataFrame:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        :raises NotImplementedError: cBioportalTransformerBase is an orchestrator
        """
        msg = (
            "CBioPortalTransformerBase is an orchestrator. "
            "Use `run_transformers({study: harvested_data})` instead of `.transform()`."
        )
        raise NotImplementedError(msg)

    # ======================================================
    #  Gene-mapping utilities (instance methods)
    # ======================================================

    def _get_entrez_id(self, norm_response: object) -> str | None:
        """Extract NCBI Entrez Gene ID from VICC normalizer response mappings."""
        if not norm_response:
            return None
        try:
            # First check mappings
            for mapping in getattr(norm_response.gene, "mappings", []) or []:
                coding_id = getattr(mapping.coding, "id", "")
                if coding_id.lower().startswith("ncbigene:"):
                    return coding_id.split(":", 1)[1]

            # Fall back to primaryCoding if not found in mappings
            primary = getattr(norm_response.gene, "primaryCoding", None)
            if primary:
                primary_id = getattr(primary, "id", "")
                if primary_id.lower().startswith("ncbigene:"):
                    return primary_id.split(":", 1)[1]

        except AttributeError:
            pass
        return None

    def _get_refseq_id(self, norm_response: object) -> str | None:
        """Extract RefSeq accession from VICC normalizer response mappings."""
        if not norm_response:
            return None
        try:
            for mapping in getattr(norm_response.gene, "mappings", []) or []:
                coding_id = getattr(mapping.coding, "id", "")
                if coding_id.lower().startswith("refseq:"):
                    return coding_id.split(":", 1)[1]
        except AttributeError:
            pass
        return None

    def _get_exact_gene_mappings(
        self, hgnc_id: str | None, gene_symbol: str
    ) -> list[ConceptMapping]:
        """Return EXACT_MATCH mapping for HGNC ID, if we have one.

        :param hgnc_id: HGNC identifier string (e.g. "8619"), or None if unavailable.
        :param gene_symbol: Hugo gene symbol used as the display name in the mapping.
        :return: List containing a single EXACT_MATCH ConceptMapping if a valid
            HGNC ID is provided, otherwise an empty list.
        """
        if not hgnc_id or hgnc_id == "untested":
            return []

        gene_id = f"hgnc:{hgnc_id}"

        return [
            ConceptMapping(
                coding=Coding(
                    id=gene_id,
                    name=gene_symbol,
                    code=gene_id.upper(),
                    system="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/",
                ),
                relation=Relation.EXACT_MATCH,
                extensions=[Extension(name="cbioportal_annotation", value=True)],
            )
        ]

    def _add_genes(
        self, transformer: Transformer, df: pd.DataFrame
    ) -> tuple[list[MappableConcept], dict[str, Any]]:
        """Central gene mapping: runs for EVERY study automatically.
        Uses the transformer's `vicc_normalizers`.

        :param transformer: The study-level transformer instance, used to access
            ``vicc_normalizers`` for gene symbol normalization.
        :param df: Combined DataFrame for the study, must contain a ``Hugo_Symbol``
            column. A ``gene_hgnc_id`` column will be added or updated in place.
        :return: A tuple of (mappable_genes, qc_dict) where ``mappable_genes`` is a
            list of GA4GH MappableConcept objects and ``qc_dict`` contains summary
            metrics with keys ``total_unique_symbols``, ``normalized_hgnc``,
            ``failed``, and ``pct_normalized``.
        """
        if "Hugo_Symbol" not in df.columns:
            logger.warning("No 'Hugo_Symbol' column found; skipping gene mapping.")
            return [], {
                "total_unique_symbols": 0,
                "normalized_hgnc": 0,
                "failed": 0,
                "pct_normalized": 0.0,
                "note": "missing Hugo_Symbol column",
            }

        # Ensure columns exist to store HGNC and Entrez IDs resolved from the normalizer
        if "gene_hgnc_id" not in df.columns:
            df["gene_hgnc_id"] = pd.NA

        if "Entrez_Gene_Id" not in df.columns:
            df["Entrez_Gene_Id"] = pd.NA

        if "RefSeq" not in df.columns:
            df["RefSeq"] = pd.NA

        # Unique gene symbols across the DataFrame
        symbols = df["Hugo_Symbol"].dropna().drop_duplicates().tolist()

        mappable: list[MappableConcept] = []
        normalized_hgnc = 0
        failed = 0

        for symbol in tqdm(symbols, desc="Normalizing genes", unit="gene"):
            # Check cache first
            if symbol in self.gene_cache:
                norm_response, normalized_id = self.gene_cache[symbol]
            else:
                # Not in cache - make API call
                normalized_id = None
                norm_response = None

                try:
                    norm_response, normalized_id = (
                        transformer.vicc_normalizers.normalize_gene(symbol)
                    )
                    # Rate limiting
                    time.sleep(self.rate_limit_delay)
                except Exception as e:
                    logger.warning("Normalizer error for symbol %s: %s", symbol, e)
                    normalized_id = None
                    norm_response = None

                # Store in cache
                self.gene_cache[symbol] = (norm_response, normalized_id)

            # Decide success/failure (for QC) and store HGNC numeric ID if applicable
            hgnc_numeric: str | None = None
            if (
                normalized_id
                and isinstance(normalized_id, str)
                and normalized_id.lower().startswith("hgnc:")
            ):
                hgnc_numeric = normalized_id.split(":", 1)[1]
                normalized_hgnc += 1
            else:
                failed += 1
                # Track failed gene normalizations with sample IDs
                # Check if this symbol has already been recorded for this study
                study_id_val = df.iloc[0].get("STUDY_ID", "") if len(df) > 0 else ""
                already_tracked = any(
                    f["gene_symbol"] == symbol and f["study_id"] == study_id_val
                    for f in self.failed_genes
                )
                if not already_tracked:
                    for _, row in df[df["Hugo_Symbol"] == symbol].iterrows():
                        self.failed_genes.append(
                            {
                                "study_id": row.get("STUDY_ID", ""),
                                "sample_id": row.get("SAMPLE_ID", ""),
                                "gene_symbol": symbol,
                            }
                        )

            if hgnc_numeric:
                df.loc[df["Hugo_Symbol"] == symbol, "gene_hgnc_id"] = hgnc_numeric

            # get entrez id
            entrez_id = self._get_entrez_id(norm_response)
            if entrez_id:
                df.loc[
                    (df["Hugo_Symbol"] == symbol)
                    & (
                        df["Entrez_Gene_Id"].isna() | df["Entrez_Gene_Id"].eq("No_Data")
                    ),
                    "Entrez_Gene_Id",
                ] = entrez_id

            # get RefSeq:
            refseq_id = self._get_refseq_id(norm_response)
            if refseq_id:
                df.loc[
                    (df["Hugo_Symbol"] == symbol)
                    & (df["RefSeq"].isna() | df["RefSeq"].eq("No_Data")),
                    "RefSeq",
                ] = refseq_id

            # Build GA4GH mapping objects
            if not normalized_id:
                mappings = self._get_exact_gene_mappings(None, symbol)
                extensions = [self._get_vicc_normalizer_failure_ext()]
            else:
                mappings = self._get_vicc_normalizer_mappings(
                    normalized_id, norm_response
                )
                extensions = None

            mappable.append(
                MappableConcept(
                    conceptType="Gene",
                    name=symbol,
                    mappings=mappings,
                    extensions=extensions,
                )
            )

        df["gene_hgnc_id"] = df["gene_hgnc_id"].fillna("No_Data")
        df["Entrez_Gene_Id"] = df["Entrez_Gene_Id"].fillna("No_Data")
        df["RefSeq"] = df["RefSeq"].fillna("No_Data")

        total = len(symbols)
        pct = (normalized_hgnc / total * 100.0) if total else 0.0

        qc = {
            "total_unique_symbols": total,
            "normalized_hgnc": normalized_hgnc,
            "failed": failed,
            "pct_normalized": round(pct, 2),
        }
        return mappable, qc

    def _add_variants(self, df: pd.DataFrame) -> list[MappableConcept]:
        """Build MappableConcept objects for normalized variants in the DataFrame."""
        if "Gnomad_Notation" not in df.columns or "vrs_id" not in df.columns:
            logger.warning(
                "Missing Gnomad_Notation or vrs_id column; skipping variant mapping."
            )
            return []

        mappable: list[MappableConcept] = []

        variant_df = (
            df[["Gnomad_Notation", "vrs_id", "Hugo_Symbol"]]
            .dropna(subset=["Gnomad_Notation"])
            .drop_duplicates(subset=["Gnomad_Notation"])
        )

        for _, row in variant_df.iterrows():
            notation = row["Gnomad_Notation"]
            vrs_id = row.get("vrs_id")
            row.get("Hugo_Symbol", "")

            if vrs_id and not pd.isna(vrs_id):
                mappings = [
                    ConceptMapping(
                        coding=Coding(
                            id=vrs_id,
                            name=notation,
                            code=vrs_id,
                            system="https://vrs.ga4gh.org/",
                        ),
                        relation=Relation.EXACT_MATCH,
                    )
                ]
                extensions = None
            else:
                mappings = []
                extensions = [self._get_vicc_normalizer_failure_ext()]

            mappable.append(
                MappableConcept(
                    conceptType="Variant",
                    name=notation,
                    mappings=mappings,
                    extensions=extensions,
                )
            )

        return mappable

    def _normalize_variant(self, variant_notation: str) -> str | None:
        """Normalize variant using VICC variation normalizer with caching.
        Uses the genome build appropriate for the current study.

        Args:
            variant_notation: Genomic notation (e.g., "8-67380528-T-C")

        Returns:
            VRS variant ID or None if normalization fails

        """
        # Determine genome build for current study
        genome_build = self.current_genome_build

        # Create cache key that includes genome build
        cache_key = f"{variant_notation}|{genome_build}"

        # Check cache first
        if cache_key in self.variant_cache:
            return self.variant_cache[cache_key]

        base_url = "https://normalize.cancervariants.org/variation/"
        params = {
            "q": variant_notation,
            "hgvs_dup_del_mode": "default",
            "input_assembly": genome_build,
        }

        vrs_id = None
        try:
            response = requests.get(f"{base_url}normalize", params=params, timeout=10)
            if response.ok:
                data = response.json()
                if "variation" in data and "id" in data["variation"]:
                    vrs_id = data["variation"]["id"]

            # Rate limiting
            # time.sleep(self.rate_limit_delay)
        except Exception as e:
            logger.warning(
                "Variant normalization failed for %s (%s): %s",
                variant_notation,
                genome_build,
                e,
            )

        # Store in cache with genome build in key
        self.variant_cache[cache_key] = vrs_id
        return vrs_id

    def _normalize_variants(self, df: pd.DataFrame, study_id: str) -> pd.DataFrame:
        """Normalize all unique variants in the DataFrame and add a vrs_id column.

        Uses the VICC variation normalizer (with caching) to resolve each unique
        Gnomad_Notation to a VRS identifier. Failed normalizations are tracked in
        ``self.failed_variants``.

        :param df: DataFrame with a Gnomad_Notation column
        :param study_id: Study identifier for failure tracking
        :return: DataFrame with a ``vrs_id`` column added
        """
        if "Gnomad_Notation" not in df.columns:
            logger.warning(
                "No Gnomad_Notation column in study %s; skipping variant normalization.",
                study_id,
            )
            df["vrs_id"] = None
            return df

        unique_variants = df["Gnomad_Notation"].dropna().drop_duplicates().tolist()
        vrs_map: dict[str, str | None] = {}

        for variant in tqdm(
            unique_variants, desc=f"Normalizing variants for {study_id}", unit="variant"
        ):
            vrs_id = self._normalize_variant(variant)
            vrs_map[variant] = vrs_id

            if not vrs_id:
                # Track failed variant normalizations
                already_tracked = any(
                    f["variant_notation"] == variant and f["study_id"] == study_id
                    for f in self.failed_variants
                )
                if not already_tracked:
                    sample_ids = (
                        df.loc[df["Gnomad_Notation"] == variant, "SAMPLE_ID"].tolist()
                        if "SAMPLE_ID" in df.columns
                        else []
                    )
                    for sid in sample_ids:
                        self.failed_variants.append(
                            {
                                "study_id": study_id,
                                "sample_id": sid,
                                "variant_notation": variant,
                            }
                        )

        df["vrs_id"] = df["Gnomad_Notation"].map(vrs_map).fillna("No_Data")

        total = len(unique_variants)
        normalized = sum(1 for v in vrs_map.values() if v is not None)
        failed = total - normalized
        pct = (normalized / total * 100.0) if total else 0.0
        logger.info(
            "[%s] Variant normalization: %d/%d (%.1f%%) succeeded, %d failed",
            study_id,
            normalized,
            total,
            pct,
            failed,
        )

        self.variant_qc_by_study[study_id] = {
            "total_unique_variants": total,
            "normalized_vrs": normalized,
            "failed": failed,
            "pct_normalized": round(pct, 2),
        }

        return df

    def _add_variant_frequency_columns(
        self, combined: pd.DataFrame, multi_study: bool
    ) -> pd.DataFrame:
        """Add four variant frequency columns to the combined DataFrame.

        Columns added:
          - freq_variant_inter_study: variant count / total samples across ALL studies
          - freq_variant_intra_study: variant count in study / total samples in study
          - freq_variant_cancer_inter_study: variant count for cancer type across ALL
              studies / total samples of that cancer type across ALL studies
          - freq_variant_cancer_intra_study: variant count for cancer type in study /
              total samples of that cancer type in study

        When only a single study is being transformed, the cross-study columns
        are set to ``"uncalculated"``.

        :param combined: Combined DataFrame with Gnomad_Notation, STUDY_ID,
            ONCOTREE_CODE, and SAMPLE_ID columns
        :param multi_study: True when more than one study was transformed
        :return: DataFrame with the four new frequency columns added
        """
        uncalculated = "uncalculated"

        if "Gnomad_Notation" not in combined.columns:
            logger.warning("No Gnomad_Notation column; skipping frequency columns.")
            combined["freq_variant_inter_study"] = uncalculated
            combined["freq_variant_intra_study"] = uncalculated
            combined["freq_variant_cancer_inter_study"] = uncalculated
            combined["freq_variant_cancer_intra_study"] = uncalculated
            return combined

        sample_col = "SAMPLE_ID" if "SAMPLE_ID" in combined.columns else None
        variant_col = "Gnomad_Notation"
        study_col = "STUDY_ID"
        cancer_col = "ONCOTREE_CODE"

        # -- freq_variant_intra_study --
        # variant count within study / total unique samples in study
        if sample_col:
            study_total = combined.groupby(study_col)[sample_col].transform("count")
            study_variant_count = combined.groupby([study_col, variant_col])[
                sample_col
            ].transform("count")
            combined["freq_variant_intra_study"] = (
                study_variant_count / study_total
            ).round(6)
        else:
            study_total = combined.groupby(study_col)[variant_col].transform("count")
            study_variant_count = combined.groupby([study_col, variant_col])[
                variant_col
            ].transform("count")
            combined["freq_variant_intra_study"] = (
                study_variant_count / study_total
            ).round(6)

        # -- freq_variant_cancer_intra_study --
        # variant count for cancer type in study / total samples of cancer type in study
        if cancer_col in combined.columns and sample_col:
            cancer_study_total = combined.groupby([study_col, cancer_col])[
                sample_col
            ].transform("count")
            cancer_study_variant = combined.groupby(
                [study_col, cancer_col, variant_col]
            )[sample_col].transform("count")
            combined["freq_variant_cancer_intra_study"] = (
                cancer_study_variant / cancer_study_total
            ).round(6)
        else:
            combined["freq_variant_cancer_intra_study"] = uncalculated

        # -- Cross-study columns (only when multiple studies) --
        if multi_study:
            # freq_variant_inter_study
            if sample_col:
                global_total = combined[sample_col].count()
                global_variant_count = combined.groupby(variant_col)[
                    sample_col
                ].transform("count")
                combined["freq_variant_inter_study"] = (
                    global_variant_count / global_total
                ).round(6)
            else:
                global_total = len(combined)
                global_variant_count = combined.groupby(variant_col)[
                    variant_col
                ].transform("count")
                combined["freq_variant_inter_study"] = (
                    global_variant_count / global_total
                ).round(6)

            # freq_variant_cancer_inter_study
            if cancer_col in combined.columns and sample_col:
                cancer_global_total = combined.groupby(cancer_col)[
                    sample_col
                ].transform("count")
                cancer_global_variant = combined.groupby([cancer_col, variant_col])[
                    sample_col
                ].transform("count")
                combined["freq_variant_cancer_inter_study"] = (
                    cancer_global_variant / cancer_global_total
                ).round(6)
            else:
                combined["freq_variant_cancer_inter_study"] = uncalculated
        else:
            combined["freq_variant_inter_study"] = uncalculated
            combined["freq_variant_cancer_inter_study"] = uncalculated

        logger.info("Added variant frequency columns (multi_study=%s)", multi_study)
        return combined

    def _build_frequency_results(
        self,
        df: pd.DataFrame,
        freq_col: str,
        study_id: str | None = None,
        group_by_cancer: bool = False,
    ) -> list[dict]:
        """Build frequency result dicts for a given frequency column.

        :param df: DataFrame (already filtered to study if study_id provided)
        :param freq_col: Column name to use for frequency value
        :param study_id: Study identifier, or None for cross-study results
        :param group_by_cancer: Whether to include cancer type grouping
        :return: List of frequency result dicts
        """
        if "Gnomad_Notation" not in df.columns:
            return []

        results = []
        group_cols = ["Gnomad_Notation"]
        if group_by_cancer and "ONCOTREE_CODE" in df.columns:
            group_cols.append("ONCOTREE_CODE")

        for _keys, group in df.groupby(group_cols):
            first_row = group.iloc[0]
            vrs_id = first_row.get("vrs_id")
            if pd.isna(vrs_id) or not vrs_id or vrs_id == "No_Data":
                continue

            freq_value = first_row.get(freq_col)
            if freq_value == "uncalculated" or pd.isna(freq_value):
                continue

            label = study_id or "all_studies"
            result = {
                "type": "TumorVariantFrequencyStudyResult",
                "id": f"{label}:{vrs_id}",
                "focusVariant": vrs_id,
                "affectedFrequency": float(freq_value),
                "frequencyType": freq_col,
            }

            if study_id:
                result["studyId"] = study_id

            if group_by_cancer and "ONCOTREE_CODE" in df.columns:
                oncotree_code = first_row.get("ONCOTREE_CODE")
                if oncotree_code and oncotree_code != "No_Data":
                    result["oncotreeCode"] = oncotree_code

            results.append(result)

        return results

    def _write_frequency_json(
        self,
        payload: dict[str, list[dict]] | list[dict],
        filename: str,
        out_dir: Path,
    ) -> Path:
        """Write frequency results to a JSON file.

        :param payload: Data to serialize
        :param filename: Output filename (without directory)
        :param out_dir: Output directory
        :return: Path to the written file
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return out_path

    def _create_frequency_qc_summary(self, combined: pd.DataFrame) -> pd.DataFrame:
        """Create QC summary across all 4 frequency types.

        :param combined: Combined DataFrame with all frequency columns
        :return: DataFrame with one row per study and QC metrics for all 4 frequency types
        """
        qc_rows = []

        for study_id in combined["STUDY_ID"].unique():
            study_df = combined[combined["STUDY_ID"] == study_id]
            total = study_df["Gnomad_Notation"].dropna().nunique()

            row = {"STUDY_ID": study_id, "total_unique_variants": total}

            for freq_col in [
                "freq_variant_intra_study",
                "freq_variant_cancer_intra_study",
                "freq_variant_inter_study",
                "freq_variant_cancer_inter_study",
            ]:
                if freq_col in study_df.columns:
                    calculable = (
                        study_df[freq_col]
                        .apply(lambda v: v != "uncalculated" and not pd.isna(v))
                        .sum()
                    )
                else:
                    calculable = 0

                failed = total - calculable
                pct = round((calculable / total * 100.0) if total else 0.0, 2)
                row[f"{freq_col}_calculable"] = int(calculable)
                row[f"{freq_col}_failed"] = int(failed)
                row[f"{freq_col}_pct"] = pct

            qc_rows.append(row)

        return pd.DataFrame(qc_rows).sort_values("STUDY_ID")

    def _write_mappable_genes_json(
        self, study: str, mappable_genes: list[MappableConcept], out_dir: str
    ) -> str:
        """Write this study's mappable genes to JSON and return the output path."""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir) / f"{study}_mappable_genes.json"

        payload = [mg.model_dump(exclude_none=True) for mg in mappable_genes]

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return out_path

    def _write_all_mappable_genes_json(self, out_path: str) -> str:
        """Merge all studies' mappable genes into one JSON file.

        Format:
          {
            "qc_by_study": {...},
            "mappable_genes_by_study": { "studyA": [ ... ], "studyB": [ ... ] }
          }
        """
        payload = {
            "qc_by_study": self.gene_qc_by_study,
            "mappable_genes_by_study": {
                study: [mg.model_dump(exclude_none=True) for mg in genes]
                for study, genes in self.mappable_genes_by_study.items()
            },
        }
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with Path(out_path).open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return out_path

    def _write_mappable_variants_json(
        self, study: str, mappable_variants: list[MappableConcept], out_dir: str | Path
    ) -> Path:
        """Write this study's mappable variants to JSON."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{study}_mappable_variants.json"

        payload = [mv.model_dump(exclude_none=True) for mv in mappable_variants]
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return out_path

    def _write_all_mappable_variants_json(self, out_path: str | Path) -> Path:
        """Merge all studies' mappable variants into one JSON file."""
        out_path = Path(out_path)
        payload = {
            "mappable_variants_by_study": {
                study: [mv.model_dump(exclude_none=True) for mv in variants]
                for study, variants in self.mappable_variants_by_study.items()
            }
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return out_path

    # ======================================================
    #  Loading and running transformers (instance methods)
    # ======================================================

    def _load_transformer(self, study: str) -> type[Transformer]:
        mod_path = self.study_to_module.get(study)
        if not mod_path:
            msg = (
                f"No transformer module registered for '{study}'. "
                f"Add to STUDY_TO_MODULE in base.py."
            )
            raise ImportError(msg)

        module = importlib.import_module(mod_path)
        try:
            return getattr(module, self.transformer_class_name)
        except AttributeError as err:
            msg = f"Module '{mod_path}' does not define class '{self.transformer_class_name}'."
            raise ImportError(msg) from err

    def _transform_one(
        self, study: str, harvested: CBioPortalHarvestedData
    ) -> pd.DataFrame:
        transformer_cls = self._load_transformer(study)
        transformer = transformer_cls()

        self.current_genome_build = transformer.get_genome_build()
        logger.info(
            "Processing study %s with genome build: %s",
            study,
            self.current_genome_build,
        )

        df = transformer.transform(harvested)

        # Add AGE_TERM column based on AGE values
        logger.info("Adding AGE_TERM classifications for study: %s", study)
        if "AGE" in df.columns:
            # Convert AGE to numeric, handling any non-numeric values
            df["AGE"] = pd.to_numeric(df["AGE"], errors="coerce")

            # Age range cutoffs (in years)
            _age_congenital_max = 0.07
            _age_pediatric_max = 16

            # Create AGE_TERM based on age ranges
            def classify_age(age: object) -> str:
                if pd.isna(age):
                    return "Unknown"
                if age <= _age_congenital_max:
                    return "Congenital"
                if age <= _age_pediatric_max:
                    return "Pediatric"
                return "Adult"

            df["AGE_TERM"] = df["AGE"].apply(classify_age)
            logger.info(
                "[%s] AGE_TERM distribution: %s",
                study,
                df["AGE_TERM"].value_counts().to_dict(),
            )
        else:
            logger.warning(
                "[%s] No AGE column found; setting AGE_TERM to 'Unknown'", study
            )
            df["AGE_TERM"] = "Unknown"

        # Harmonize RACE column
        logger.info("Harmonizing RACE terms for study: %s", study)
        if "RACE" in df.columns:
            # Mapping dictionary for ethnicity harmonization
            race_mapping = {
                # White/European
                "European": "White",
                "White/Europe": "White",
                "White/Latin America": "White",
                "White/North Africa": "White",
                # Black/African
                "African": "Black or African American",
                "Black": "Black or African American",
                "Black/Sub-Saharan Africa": "Black or African American",
                "African American": "Black or African American",
                # Asian
                "EastAsian": "Asian",
                "Asian Indian": "Asian",
                # South Asian or Hispanic (Option A - combined category)
                "SouthAsianOrHispanic": "Asian or Hispanic",
                # Hispanic/Latino
                "Hispanic": "Hispanic or Latino",
                # Pacific Islander
                "Native Hawaiian or other Pacific Islander": "Native Hawaiian or Pacific Islander",
                # Native American
                "American Indian or Alaska Native": "American Indian or Alaska Native",
                # Mixed/Other/Unknown -> No_Data
                "Mixed_or_Unknown": "Other or Mixed",
                "Other": "Other or Mixed",
                "Unknown": "No_Data",
                "Not reported": "No_Data",
                "Not Reported": "No_Data",
                "No_data": "No_Data",
                "No_Data": "No_Data",
            }

            # Keep original ethnicity in a separate column
            df["RACE_ORIGINAL"] = df["RACE"]

            # Apply mapping to create harmonized column
            df["RACE_HARMONIZED"] = df["RACE"].replace(race_mapping)

            # Log the harmonized distribution
            logger.info(
                "[%s] RACE_HARMONIZED distribution: %s",
                study,
                df["RACE_HARMONIZED"].value_counts().to_dict(),
            )
        else:
            logger.warning(
                "[%s] No RACE column found; setting RACE_HARMONIZED to 'No_Data'",
                study,
            )
            df["RACE_ORIGINAL"] = "No_Data"
            df["RACE_HARMONIZED"] = "No_Data"

        logger.info("Adding gene mappings for study: %s", study)
        mappable_genes, gene_qc = self._add_genes(transformer, df)

        # Persist in-memory so we can write merged JSON + QC table at the end
        self.mappable_genes_by_study[study] = mappable_genes
        self.gene_qc_by_study[study] = gene_qc

        # Attach them so caller can use `.mappable_genes`
        transformer.mappable_genes = mappable_genes

        # Write per-study mappable genes JSON
        if hasattr(self, "_mappable_genes_out_dir"):
            self._write_mappable_genes_json(
                study, mappable_genes, self._mappable_genes_out_dir
            )

        # Simple debug output
        logger.info("[%s] mappable_genes count: %d", study, len(mappable_genes))

        # Normalize variants to VRS IDs
        logger.info("Normalizing variants for study: %s", study)
        df = self._normalize_variants(df, study)

        # Build mappable variants (after vrs_id column exists)
        mappable_variants = self._add_variants(df)
        self.mappable_variants_by_study[study] = mappable_variants
        logger.info("[%s] mappable_variants count: %d", study, len(mappable_variants))

        if "STUDY_ID" not in df.columns:
            df = df.assign(STUDY_ID=study)

        return df

    def run_transformers(self, harvested: dict[str, Any]) -> pd.DataFrame:
        """Run transformers for all harvested studies and combine results.

        :param harvested: Mapping of study names to their harvested data
        :return: Combined DataFrame of all transformed study data
        :raises TypeError: if ``harvested`` is not a dict
        :raises ValueError: if no frames are returned by transformers
        """
        if not isinstance(harvested, dict):
            msg = "run_transformers() requires a dict:  {study: harvested_data}"
            raise TypeError(msg)

        # -----------------------------------------
        # Output directory (define ONCE, BEFORE loop)
        # -----------------------------------------
        loc = Path.cwd()
        base_dir = (loc / ".." / "transformers").resolve()
        study_out_dir = base_dir / "munged_data"
        save_loc = study_out_dir / "combined"
        save_loc.mkdir(parents=True, exist_ok=True)

        # -----------------------------------------
        # Per-study mappable genes JSON output dir
        # -----------------------------------------
        self._mappable_genes_out_dir = save_loc / "mappable_genes"

        self._mappable_genes_out_dir.mkdir(parents=True, exist_ok=True)

        dfs: list[pd.DataFrame] = []

        for study, hdata in tqdm(
            harvested.items(), desc="Transforming studies", unit="study"
        ):
            logger.info("Transforming study %s...", study)
            df = self._transform_one(study, hdata)
            dfs.append(df)

        if not dfs:
            msg = "No frames returned by transformers."
            raise ValueError(msg)

        combined = pd.concat(dfs, ignore_index=True, sort=False)

        # -----------------------------------------
        # Add variant frequency columns
        # -----------------------------------------
        multi_study = len(harvested) > 1
        combined = self._add_variant_frequency_columns(combined, multi_study)

        # -----------------------------------------
        # Create subdirectories for organized output
        # -----------------------------------------
        mappable_genes_dir = save_loc / "mappable_genes"
        mappable_variants_dir = save_loc / "mappable_variants"
        frequencies_dir = save_loc / "frequencies"
        norm_failures_dir = save_loc / "norm_failures"

        mappable_genes_dir.mkdir(parents=True, exist_ok=True)
        mappable_variants_dir.mkdir(parents=True, exist_ok=True)
        frequencies_dir.mkdir(parents=True, exist_ok=True)
        norm_failures_dir.mkdir(parents=True, exist_ok=True)

        # -----------------------------------------
        # Gene QC summary table and mappable genes
        # -----------------------------------------
        gene_qc_df = (
            pd.DataFrame.from_dict(self.gene_qc_by_study, orient="index")
            .reset_index()
            .rename(columns={"index": "STUDY_ID"})
            .sort_values("STUDY_ID")
        )
        gene_qc_out_path = mappable_genes_dir / "gene_qc_summary_per_study.csv"
        gene_qc_df.to_csv(gene_qc_out_path, index=False)

        variant_qc_df = (
            pd.DataFrame.from_dict(self.variant_qc_by_study, orient="index")
            .reset_index()
            .rename(columns={"index": "STUDY_ID"})
            .sort_values("STUDY_ID")
        )
        variant_qc_out_path = mappable_variants_dir / "variant_qc_summary_per_study.csv"
        variant_qc_df.to_csv(variant_qc_out_path, index=False)

        # Merged mappable genes JSON (all studies in one file)
        merged_genes_out_path = mappable_genes_dir / "mappable_genes_all_studies.json"
        self._write_all_mappable_genes_json(merged_genes_out_path)

        # Per-study variant JSON files
        for study_id, mappable_variants in self.mappable_variants_by_study.items():
            self._write_mappable_variants_json(
                study_id, mappable_variants, mappable_variants_dir
            )

        # Merged variants JSON (all studies in one file)
        merged_variants_out_path = (
            mappable_variants_dir / "mappable_variants_all_studies.json"
        )
        self._write_all_mappable_variants_json(merged_variants_out_path)

        # -----------------------------------------
        # Frequency results — all 4 types
        # -----------------------------------------

        # freq_variant_intra_study — per study
        for study_id in combined["STUDY_ID"].unique():
            study_df = combined[combined["STUDY_ID"] == study_id]
            self.freq_results_this_study[study_id] = self._build_frequency_results(
                study_df, freq_col="freq_variant_intra_study", study_id=study_id
            )

        self._write_frequency_json(
            payload=self.freq_results_this_study,
            filename="freq_variant_intra_study.json",
            out_dir=frequencies_dir,
        )

        # freq_variant_inter_study — single combined list
        self.freq_results_all_studies = self._build_frequency_results(
            combined, freq_col="freq_variant_inter_study"
        )
        self._write_frequency_json(
            payload=self.freq_results_all_studies,
            filename="freq_variant_inter_study.json",
            out_dir=frequencies_dir,
        )

        # freq_variant_cancer_intra_study — per study, grouped by cancer
        for study_id in combined["STUDY_ID"].unique():
            study_df = combined[combined["STUDY_ID"] == study_id]
            self.freq_results_cancer_this_study[study_id] = (
                self._build_frequency_results(
                    study_df,
                    freq_col="freq_variant_cancer_intra_study",
                    study_id=study_id,
                    group_by_cancer=True,
                )
            )

        self._write_frequency_json(
            payload=self.freq_results_cancer_this_study,
            filename="freq_variant_cancer_intra_study.json",
            out_dir=frequencies_dir,
        )

        # freq_variant_cancer_inter_study — single combined list, grouped by cancer
        self.freq_results_cancer_all_studies = self._build_frequency_results(
            combined, freq_col="freq_variant_cancer_inter_study", group_by_cancer=True
        )
        self._write_frequency_json(
            payload=self.freq_results_cancer_all_studies,
            filename="freq_variant_cancer_inter_study.json",
            out_dir=frequencies_dir,
        )

        # Frequency QC summary (all 4 types in one CSV)
        freq_qc_df = self._create_frequency_qc_summary(combined)
        freq_qc_out_path = frequencies_dir / "frequency_qc_summary_per_study.csv"
        freq_qc_df.to_csv(freq_qc_out_path, index=False)

        # -----------------------------------------
        # Failed normalizations CSVs
        # -----------------------------------------
        if self.failed_genes:
            failed_genes_df = pd.DataFrame(self.failed_genes)

            # Write combined file with all studies
            combined_genes_path = (
                norm_failures_dir / "combined_failed_gene_normalizations.csv"
            )
            failed_genes_df.to_csv(combined_genes_path, index=False)

            # Write per-study files
            for study_id in failed_genes_df["study_id"].unique():
                study_genes = failed_genes_df[failed_genes_df["study_id"] == study_id]
                failed_genes_path = (
                    norm_failures_dir / f"{study_id}_failed_gene_normalizations.csv"
                )
                study_genes.to_csv(failed_genes_path, index=False)

        if self.failed_variants:
            failed_variants_df = pd.DataFrame(self.failed_variants)

            # Write combined file with all studies
            combined_variants_path = (
                norm_failures_dir / "combined_failed_variant_normalizations.csv"
            )
            failed_variants_df.to_csv(combined_variants_path, index=False)

            # Write per-study files
            for study_id in failed_variants_df["study_id"].unique():
                study_variants = failed_variants_df[
                    failed_variants_df["study_id"] == study_id
                ]
                failed_variants_path = (
                    norm_failures_dir / f"{study_id}_failed_variant_normalizations.csv"
                )
                study_variants.to_csv(failed_variants_path, index=False)

        # -----------------------------------------
        # Save combined dataframe to CSV on disk
        # -----------------------------------------
        output_path = save_loc / "combined_cBioPortal_transformed.csv"
        combined.to_csv(output_path, index=False)

        return combined

    # ====================
    # Static utility methods for study transformers
    # ====================

    @staticmethod
    def setup_save_location(study: str, base_dir: Path | None = None) -> Path:
        """Create and return the save location for a study's output files.

        Args:
            study: Study identifier
            base_dir: Base directory (defaults to current directory's parent/transformers)

        Returns:
            Path object for the study's save location

        """
        if base_dir is None:
            loc = Path.cwd()
            base_dir = loc.parent / "transformers"

        study_out_dir = base_dir / "munged_data"
        save_loc = study_out_dir / study
        save_loc.mkdir(parents=True, exist_ok=True)

        return save_loc

    @staticmethod
    def filter_and_rename_variants(
        variants_df: pd.DataFrame,
        mut_headers: list[str],
        amino_acid_change_source: str | None = None,
    ) -> pd.DataFrame:
        """Filter variant columns and perform common transformations."""
        # Keep Sequence_Source from mutations if it exists, even if not in mut_headers
        keep_cols = list(mut_headers)
        if (
            "Sequence_Source" in variants_df.columns
            and "Sequence_Source" not in keep_cols
        ):
            keep_cols.append("Sequence_Source")

        df = variants_df.filter(keep_cols)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"Tumor_Sample_Barcode": "SAMPLE_ID"})

        if amino_acid_change_source and amino_acid_change_source in df.columns:
            df = df.rename(columns={amino_acid_change_source: "Amino_Acid_Change"})

        if "Amino_Acid_Change" not in df.columns:
            df["Amino_Acid_Change"] = "No_data"

        return df

    @staticmethod
    def filter_and_rename_patients(
        patients_df: pd.DataFrame,
        patient_headers: list[str],
        ethnicity_source: str | None = "ETHNICITY",
        race_source: str | None = "RACE",
        age_source: str | None = None,
    ) -> pd.DataFrame:
        """Filter patient columns and perform common transformations."""
        df = patients_df.filter(patient_headers)

        if age_source and age_source in df.columns:
            df = df.rename(columns={age_source: "AGE"})

        # Handle RACE
        if race_source and race_source in df.columns and race_source != "RACE":
            df = df.rename(columns={race_source: "RACE"})
        if "RACE" not in df.columns:
            df["RACE"] = "No_Data"

        # Handle ETHNICITY
        if ethnicity_source and ethnicity_source in df.columns and ethnicity_source != "ETHNICITY":
            df = df.rename(columns={ethnicity_source: "ETHNICITY"})
        if "ETHNICITY" not in df.columns:
            df["ETHNICITY"] = "No_Data"

        if "SEX" not in df.columns:
            df["SEX"] = "No_data"

        return df

    @staticmethod
    def filter_and_rename_samples(
        samples_df: pd.DataFrame,
        sample_headers: list[str],
    ) -> pd.DataFrame:
        """Filter sample columns and perform common transformations."""
        df = samples_df.filter(sample_headers)

        if "ONCOTREE_CODE_CANCER_TYPE" in df.columns:
            df = df.rename(columns={"ONCOTREE_CODE_CANCER_TYPE": "ONCOTREE_CODE"})

        return df

    @staticmethod
    def resolve_sequence_source(
        df: pd.DataFrame,
        fallback_column: str | None = None,
    ) -> pd.DataFrame:
        """Resolve the Sequence_Source column with row-level fallback.

        Priority:
          1. ``Sequence_Source`` from the mutations data (if populated)
          2. A study-specific fallback column from the samples data
          3. ``"No_Data"``

        :param df: Combined DataFrame (variants + samples + patients)
        :param fallback_column: Column name to use as fallback (e.g. GENE_PANEL,
            PLATFORM). Provided by each study's ``get_sample_transformations()``.
        :return: DataFrame with a ``Sequence_Source`` column
        """
        # If Sequence_Source came from mutations, fill gaps with fallback
        if "Sequence_Source" not in df.columns:
            df["Sequence_Source"] = pd.NA

        if fallback_column and fallback_column in df.columns:
            mask = (
                df["Sequence_Source"].isna()
                | (df["Sequence_Source"] == "")
                | (df["Sequence_Source"] == "No_Data")
            )
            df.loc[mask, "Sequence_Source"] = df.loc[mask, fallback_column]
            # Drop the original fallback column now that it's merged
            if fallback_column != "Sequence_Source":
                df = df.drop(columns=[fallback_column])

        df["Sequence_Source"] = df["Sequence_Source"].fillna("No_Data")

        return df

    @staticmethod
    def handle_duplicates(
        df: pd.DataFrame, study: str, save_loc: Path, df_type: str
    ) -> pd.DataFrame:
        """Check for and handle duplicates in a DataFrame."""
        num_duplicates = df.duplicated().sum()

        if num_duplicates > 0:
            dupes = df[df.duplicated(keep=False)]
            file_path = save_loc / f"{study}_{df_type}_dupes.csv"
            dupes.to_csv(file_path, index=False)
            logger.info(
                "Saved %s %s duplicates to %s", num_duplicates, df_type, file_path
            )
            df = df.drop_duplicates()

        return df

    @staticmethod
    def combine_dataframes(
        variants: pd.DataFrame,
        samples: pd.DataFrame,
        patients: pd.DataFrame,
        metadata: pd.DataFrame,
        study_id_override: str | None = None,
    ) -> pd.DataFrame:
        """Combine variant, sample, and patient dataframes."""
        init_combined_df = variants.merge(samples, on="SAMPLE_ID", how="left")
        combined_df = init_combined_df.merge(patients, on="PATIENT_ID", how="left")

        if study_id_override:
            study_id = study_id_override
        else:
            study_id = metadata.iloc[0, 0]
            study_id = study_id.replace("cancer_study_identifier: ", "")

        combined_df["STUDY_ID"] = study_id

        return combined_df

    @staticmethod
    def add_gnomad_notation(df: pd.DataFrame) -> pd.DataFrame:
        """Add Gnomad variant notation column."""
        df["Gnomad_Notation"] = df.apply(
            lambda row: f"{row['Chromosome']}-{row['Start_Position']}-{row['Reference_Allele']}-{row['Tumor_Seq_Allele2']}",
            axis=1,
        )
        return df

    @staticmethod
    def remove_patient_variant_duplicates(
        df: pd.DataFrame, study: str, save_loc: Path
    ) -> pd.DataFrame:
        """Remove duplicate variants per patient."""
        dupe_mask = df.duplicated(
            subset=["PATIENT_ID", "Gnomad_Notation"], keep="first"
        )
        patient_variant_dupes = df[dupe_mask]
        final_df = df[~dupe_mask]

        if len(patient_variant_dupes) > 0:
            file_path = save_loc / f"{study}_patient_variant_dupes.csv"
            patient_variant_dupes.to_csv(file_path, index=False)
            logger.info(
                "Removed %s patient-variant duplicates", len(patient_variant_dupes)
            )

        return final_df

    @staticmethod
    def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """Fill NaN and empty string values with 'No_Data'."""
        df = df.fillna("No_Data")
        return df.replace(r"^\s*$", pd.NA, regex=True).fillna("No_Data")

    @staticmethod
    def save_study_outputs(df: pd.DataFrame, study: str, save_loc: Path) -> None:
        """Save final study outputs to CSV files."""
        file_path = save_loc / f"{study}_df_premerge.csv"
        df.to_csv(file_path, index=False)
        logger.info("Saved clean final data to %s", file_path)


class CBioPortalStudyTransformer(Transformer):
    """Base class for individual study transformers with common transformation logic."""

    def __init__(self) -> None:
        """Initialize cBioPortal study transformer."""
        super().__init__()
        self.final_df = None
        self.variants = None
        self.patients = None
        self.samples = None
        self.metadata = None

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[MappableConcept],
        therapy_interaction_type: str,
    ) -> None:
        return super()._get_therapeutic_substitute_group(
            therapeutic_sub_group_id, therapies, therapy_interaction_type
        )

    def _get_therapy(self, therapy: dict) -> None:
        return super()._get_therapy(therapy)

    def _create_cache(self) -> None:
        return None

    @abstractmethod
    def get_study_name(self) -> str:
        """Return the study identifier."""

    @abstractmethod
    def get_mut_headers(self) -> list[str]:
        """Return the list of mutation/variant column headers to keep."""

    @abstractmethod
    def get_patient_headers(self) -> list[str]:
        """Return the list of patient column headers to keep."""

    @abstractmethod
    def get_sample_headers(self) -> list[str]:
        """Return the list of sample column headers to keep."""

    def get_variant_transformations(self) -> dict[str, Any]:
        """Return study-specific variant transformations."""
        return {}

    def get_patient_transformations(self) -> dict[str, Any]:
        """Return study-specific patient transformations."""
        return {}

    def get_sample_transformations(self) -> dict[str, Any]:
        """Return study-specific sample transformations."""
        return {}

    def get_genome_build(self) -> str:
        """Return the genome build for this study. Override for non-default builds."""
        return DEFAULT_GENOME_BUILD  # "GRCh37"

    def apply_custom_variant_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply any custom variant transformations."""
        return df

    def apply_custom_sample_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply any custom sample transformations."""
        return df

    def transform(self, harvested_data: CBioPortalHarvestedData) -> pd.DataFrame:
        """Run the standard transformation pipeline for cBioportal studies."""
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

        if "center_value" in variant_transforms:
            self.variants["Center"] = variant_transforms["center_value"]

        if "additional_columns" in variant_transforms:
            for col, default_val in variant_transforms["additional_columns"].items():
                if col not in self.variants.columns:
                    self.variants[col] = default_val

        self.variants = self.apply_custom_variant_logic(self.variants)

        # Process patients
        patient_transforms = self.get_patient_transformations()
        self.patients = CBioPortalTransformerBase.filter_and_rename_patients(
            self.patients,
            self.get_patient_headers(),
            ethnicity_source=patient_transforms.get("ethnicity_source", "ETHNICITY"),
            race_source=patient_transforms.get("race_source", "RACE"),
            age_source=patient_transforms.get("age_source"),
        )

        # Process samples
        sample_transforms = self.get_sample_transformations()
        self.samples = CBioPortalTransformerBase.filter_and_rename_samples(
            self.samples,
            self.get_sample_headers(),
        )
        self.samples = self.apply_custom_sample_logic(self.samples)

        # Combine dataframes
        combined_df = CBioPortalTransformerBase.combine_dataframes(
            self.variants, self.samples, self.patients, self.metadata
        )
        combined_df = CBioPortalTransformerBase.handle_duplicates(
            combined_df, study, save_loc, "combined"
        )

        # Resolve Sequence_Source (mutations first, then sample fallback)
        combined_df = CBioPortalTransformerBase.resolve_sequence_source(
            combined_df,
            fallback_column=sample_transforms.get("sequence_source"),
        )

        # Add Gnomad notation
        combined_df = CBioPortalTransformerBase.add_gnomad_notation(combined_df)

        # Remove patient-variant duplicates
        final_df = CBioPortalTransformerBase.remove_patient_variant_duplicates(
            combined_df, study, save_loc
        )

        # Fill missing values
        final_df = CBioPortalTransformerBase.fill_missing_values(final_df)

        # Save outputs
        CBioPortalTransformerBase.save_study_outputs(final_df, study, save_loc)

        self.final_df = final_df
        return final_df


# Convenience function to keep old API working if you want
def run_transformers(harvested: dict[str, Any]) -> pd.DataFrame:
    """Run all cBioPortal study transformers and combine results.

    :param harvested: Mapping of study names to their harvested data
    :return: Combined DataFrame of all transformed study data
    """
    base = CBioPortalTransformerBase()
    return base.run_transformers(harvested)


# Optional: CLI runner
if __name__ == "__main__":
    from metakb.harvesters.cbioportal import cBioportalHarvester

    harvester = cBioportalHarvester()
    data = harvester.harvest()  # all studies

    base = CBioPortalTransformerBase()
    df = base.run_transformers(data)
