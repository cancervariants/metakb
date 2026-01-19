# metakb/transformers/cbioportal/base.py
from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import os
from os import environ
import requests
import time

environ["AWS_ACCESS_KEY_ID"] = "dummy"
environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
environ["AWS_SESSION_TOKEN"] = "dummy"

from metakb.transformers.base import Transformer

from tqdm import tqdm
import pandas as pd

from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)

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
}

# -----------------------------
# Map study → genome build
# Default is GRCh37, only specify exceptions
# -----------------------------
STUDY_GENOME_BUILD = {
    "pancan_mappyacts_2022": "GRCh38",
}

DEFAULT_GENOME_BUILD = "GRCh37"

TRANSFORMER_CLASS_NAME = "cBioportalTransformer"


class cBioportalTransformerBase(Transformer):
    """
    Orchestrates per-study cBioportal transformers AND performs centralized
    gene mapping via the VICC normalizers.
    """

    def __init__(
        self,
        study_to_module: Dict[str, str] | None = None,
        transformer_class_name: str = TRANSFORMER_CLASS_NAME,
        rate_limit_delay: float = 0.1,  # 100ms between API calls
        study_genome_build: Dict[str, str] | None = None,
    ) -> None:
        super().__init__()  # initialize Transformer's internals
        self.study_to_module = study_to_module or STUDY_TO_MODULE
        self.transformer_class_name = transformer_class_name
        self.rate_limit_delay = rate_limit_delay
        self.study_genome_build = study_genome_build or STUDY_GENOME_BUILD

        # Collect mappable genes + QC per study so we can write combined outputs at the end
        self.mappable_genes_by_study: Dict[str, List[MappableConcept]] = {}
        self.gene_qc_by_study: Dict[str, Dict[str, Any]] = {}
        
        # Track failed normalizations
        self.failed_genes: List[Dict[str, str]] = []
        self.failed_variants: List[Dict[str, str]] = []
        
        # Cache for normalized genes and variants to avoid duplicate API calls
        self.gene_cache: Dict[str, Tuple[Any, Optional[str]]] = {}  # symbol -> (response, normalized_id)
        self.variant_cache: Dict[str, Optional[str]] = {}  # variant_notation -> vrs_id
        
        # Track current study being processed (for genome build lookup)
        self.current_study: Optional[str] = None

    # ======================================================
    #  Required abstract methods from Transformer
    # ======================================================

    def _create_cache(self) -> None:
        return None

    def _get_therapeutic_substitute_group(
        self, therapeutic_sub_group_id, therapies, therapy_interaction_type
    ):
        return None

    def _get_therapy(self, therapy):
        return None

    def transform(self, harvested_data):
        raise NotImplementedError(
            "cBioportalTransformerBase is an orchestrator. "
            "Use `run_transformers({study: harvested_data})` instead of `.transform()`."
        )

    # ======================================================
    #  Gene-mapping utilities (instance methods)
    # ======================================================

    def _get_exact_gene_mappings(
        self, hgnc_id: str | None, gene_symbol: str
    ) -> List[ConceptMapping]:
        """Return EXACT_MATCH mapping for HGNC ID, if we have one."""
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
        self, transformer, df: pd.DataFrame
    ) -> Tuple[List[MappableConcept], Dict[str, Any]]:
        """
        Central gene mapping: runs for EVERY study automatically.
        Uses the transformer's `vicc_normalizers`.

        Returns:
          (mappable_genes, qc_dict)
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

        # Ensure a column exists to store HGNC IDs resolved from the normalizer
        if "gene_hgnc_id" not in df.columns:
            df["gene_hgnc_id"] = pd.NA

        # Unique gene symbols across the DataFrame
        symbols = df["Hugo_Symbol"].dropna().drop_duplicates().tolist()

        mappable: List[MappableConcept] = []
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
                    norm_response, normalized_id = transformer.vicc_normalizers.normalize_gene(
                        symbol
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
                        self.failed_genes.append({
                            "study_id": row.get("STUDY_ID", ""),
                            "sample_id": row.get("SAMPLE_ID", ""),
                            "gene_symbol": symbol
                        })

            if hgnc_numeric:
                df.loc[df["Hugo_Symbol"] == symbol, "gene_hgnc_id"] = hgnc_numeric

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

        total = len(symbols)
        pct = (normalized_hgnc / total * 100.0) if total else 0.0

        qc = {
            "total_unique_symbols": total,
            "normalized_hgnc": normalized_hgnc,
            "failed": failed,
            "pct_normalized": round(pct, 2),
        }
        return mappable, qc

    def _normalize_variant(self, variant_notation: str) -> Optional[str]:
        """
        Normalize variant using VICC variation normalizer with caching.
        Uses the genome build appropriate for the current study.
        
        Args:
            variant_notation: Genomic notation (e.g., "8-67380528-T-C")
            
        Returns:
            VRS variant ID or None if normalization fails
        """
        # Determine genome build for current study
        genome_build = self.study_genome_build.get(self.current_study, DEFAULT_GENOME_BUILD)
        
        # Create cache key that includes genome build
        cache_key = f"{variant_notation}|{genome_build}"
        
        # Check cache first
        if cache_key in self.variant_cache:
            return self.variant_cache[cache_key]
        
        base_url = "https://normalize.cancervariants.org/variation/"
        params = {
            "q": variant_notation,
            "hgvs_dup_del_mode": "default",
            "input_assembly": genome_build
        }
        
        vrs_id = None
        try:
            response = requests.get(
                f"{base_url}normalize",
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "variation" in data and "id" in data["variation"]:
                    vrs_id = data["variation"]["id"]
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        except Exception as e:
            logger.warning(f"Variant normalization failed for {variant_notation} ({genome_build}): {e}")
        
        # Store in cache with genome build in key
        self.variant_cache[cache_key] = vrs_id
        return vrs_id
    
    def _create_tumor_variant_frequency_result(
        self,
        variant_notation: str,
        affected_count: int,
        total_count: int,
        study_id: str,
        study_label: str,
        cancer_type: Optional[str] = None,
        cancer_type_detailed: Optional[str] = None,
        oncotree_code: Optional[str] = None,
        sample_ids: Optional[List[str]] = None,
    ) -> Optional[dict]:
        """
        Create a TumorVariantFrequencyStudyResult object.
        
        Args:
            variant_notation: Genomic notation (e.g., "8-67380528-T-C")
            affected_count: Number of samples with the variant
            total_count: Total number of samples in the study
            study_id: cBioPortal study ID
            study_label: Human-readable study name
            cancer_type: Cancer type (optional)
            cancer_type_detailed: Detailed cancer type (optional)
            oncotree_code: OncoTree code (optional)
            sample_ids: List of sample IDs with this variant (optional)
            
        Returns:
            TumorVariantFrequencyStudyResult dict or None if normalization fails
        """
        # Normalize variant to get VRS ID (uses cache internally)
        vrs_id = self._normalize_variant(variant_notation)
        if not vrs_id:
            logger.warning(f"Could not normalize variant: {variant_notation}")
            # Track failed variant normalizations
            # Check if this variant has already been recorded for this study
            if sample_ids:
                already_tracked = any(
                    f["variant_notation"] == variant_notation and f["study_id"] == study_id
                    for f in self.failed_variants
                )
                if not already_tracked:
                    for sid in sample_ids:
                        self.failed_variants.append({
                            "study_id": study_id,
                            "sample_id": sid,
                            "variant_notation": variant_notation
                        })
            return None
        
        # Calculate frequency
        affected_frequency = float(affected_count) / float(total_count)
        
        # Build study group
        study_group = {
            "id": study_id,
            "label": study_label,
            "type": "StudyGroup"
        }
        
        # Add characteristics to study group if available
        characteristics = []
        if cancer_type:
            characteristics.append({
                "label": cancer_type,
                "value": cancer_type
            })
        if oncotree_code:
            characteristics.append({
                "label": f"OncoTree: {oncotree_code}",
                "value": oncotree_code
            })
        
        if characteristics:
            study_group["characteristics"] = characteristics
        
        # Build the study result
        result = {
            "type": "TumorVariantFrequencyStudyResult",
            "id": f"{study_id}:{vrs_id}",
            "focusVariant": vrs_id,
            "affectedSampleCount": affected_count,
            "totalSampleCount": total_count,
            "affectedFrequency": round(affected_frequency, 6),
            "sampleGroup": study_group
        }
        
        # Add optional description
        if cancer_type_detailed:
            result["description"] = (
                f"Frequency of variant in {cancer_type_detailed} samples "
                f"from {study_label}"
            )
        
        return result
    
    def _calculate_variant_frequencies(
            self, 
            df: pd.DataFrame, 
            study_id: str) -> List[dict]:
        """
        Calculate variant frequencies for all unique variants in a study.
        
        Args:
            df: DataFrame with variant data (must have Gnomad_Notation column)
            study_id: Study identifier
            
        Returns:
            List of TumorVariantFrequencyStudyResult objects
        """
        if "Gnomad_Notation" not in df.columns:
            logger.warning(f"No Gnomad_Notation column in study {study_id}")
            return []
        
        # Get study metadata from first row
        study_label = df["STUDY_ID"].iloc[0] if "STUDY_ID" in df.columns else study_id
        
        # Get total unique samples in study
        total_samples = df["SAMPLE_ID"].nunique() if "SAMPLE_ID" in df.columns else len(df)
        
        # Group by variant and count unique samples with each variant
        variant_counts = df.groupby("Gnomad_Notation")["SAMPLE_ID"].nunique().reset_index()
        variant_counts.columns = ["Gnomad_Notation", "affected_count"]
        
        results = []
        
        for _, row in tqdm(
            variant_counts.iterrows(), 
            total=len(variant_counts),
            desc=f"Creating frequency results for {study_id}",
            unit="variant"
        ):
            variant = row["Gnomad_Notation"]
            affected = int(row["affected_count"])
            
            # Get additional metadata from first occurrence of this variant
            variant_rows = df[df["Gnomad_Notation"] == variant]
            first_row = variant_rows.iloc[0]
            
            cancer_type = first_row.get("CANCER_TYPE")
            cancer_type_detailed = first_row.get("CANCER_TYPE_DETAILED")
            oncotree_code = first_row.get("ONCOTREE_CODE")
            
            # Get sample IDs for failure tracking
            sample_ids = variant_rows["SAMPLE_ID"].tolist() if "SAMPLE_ID" in variant_rows.columns else None
            
            # Create study result (uses cached normalization)
            study_result = self._create_tumor_variant_frequency_result(
                variant_notation=variant,
                affected_count=affected,
                total_count=total_samples,
                study_id=study_id,
                study_label=study_label,
                cancer_type=cancer_type,
                cancer_type_detailed=cancer_type_detailed,
                oncotree_code=oncotree_code,
                sample_ids=sample_ids
            )
            
            if study_result:
                results.append(study_result)
        
        return results

    def _write_frequency_results_json(
        self,
        study: str,
        frequency_results: List[dict],
        out_dir: str
    ) -> str:
        """Write TumorVariantFrequencyStudyResult objects to JSON file."""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_path = os.path.join(out_dir, f"{study}_tumor_variant_frequencies.json")
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(frequency_results, f, indent=2)
        
        return out_path


    def _write_all_frequency_results_json(self, out_path: str) -> str:
        """Merge all studies' frequency results into one JSON file."""
        payload = {
            "frequency_results_by_study": self.frequency_results_by_study
        }
        
        Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        return out_path


    def _create_frequency_qc_summary(self) -> pd.DataFrame:
        """Create QC summary for frequency results."""
        qc_data = []
        
        for study, results in self.frequency_results_by_study.items():
            total = len(results)
            normalized = sum(1 for r in results if r.get("focusVariant"))
            failed = total - normalized
            pct = (normalized / total * 100.0) if total else 0.0
            
            qc_data.append({
                "STUDY_ID": study,
                "total_variants": total,
                "normalized_variants": normalized,
                "failed_normalization": failed,
                "pct_normalized": round(pct, 2)
            })
        
        return pd.DataFrame(qc_data).sort_values("STUDY_ID")

    def _write_mappable_genes_json(
        self, study: str, mappable_genes: List[MappableConcept], out_dir: str
    ) -> str:
        """Write this study's mappable genes to JSON and return the output path."""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_path = os.path.join(out_dir, f"{study}_mappable_genes.json")

        payload = [mg.model_dump(exclude_none=True) for mg in mappable_genes]

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return out_path

    def _write_all_mappable_genes_json(self, out_path: str) -> str:
        """
        Merge all studies' mappable genes into one JSON file.

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
        Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return out_path

    # ======================================================
    #  Loading and running transformers (instance methods)
    # ======================================================

    def _load_transformer(self, study: str):
        mod_path = self.study_to_module.get(study)
        if not mod_path:
            raise ImportError(
                f"No transformer module registered for '{study}'. "
                f"Add to STUDY_TO_MODULE in base.py."
            )

        module = importlib.import_module(mod_path)
        try:
            return getattr(module, self.transformer_class_name)
        except AttributeError:
            raise ImportError(
                f"Module '{mod_path}' does not define class '{self.transformer_class_name}'."
            )

    def _transform_one(self, study: str, harvested: Any) -> pd.DataFrame:
        # Set current study for genome build lookup
        self.current_study = study
        genome_build = self.study_genome_build.get(study, DEFAULT_GENOME_BUILD)
        logger.info("Processing study %s with genome build: %s", study, genome_build)
        
        transformer_cls = self._load_transformer(study)
        transformer = transformer_cls()

        df = transformer.transform(harvested)

        logger.info("Adding gene mappings for study: %s", study)
        mappable_genes, gene_qc = self._add_genes(transformer, df)

        # Persist in-memory so we can write merged JSON + QC table at the end
        self.mappable_genes_by_study[study] = mappable_genes
        self.gene_qc_by_study[study] = gene_qc

        #calculte variant frequencies for study
        logger.info("Calculating variant frequencies for study: %s", study)
        frequency_results = self._calculate_variant_frequencies(df, study)

        # Store frequency results
        if not hasattr(self, "frequency_results_by_study"):
            self.frequency_results_by_study = {}
        self.frequency_results_by_study[study] = frequency_results

        # Write per-study frequency results JSON
        if hasattr(self, "_frequency_results_out_dir"):
            freq_out_path = self._write_frequency_results_json(
                study, frequency_results, self._frequency_results_out_dir
            )
            print(f"Saved [{study}] variant frequency results to: {freq_out_path}")

        print(f"[{study}] Created {len(frequency_results)} frequency results")

        # Attach them so caller can use `.mappable_genes`
        transformer.mappable_genes = mappable_genes

        # Write per-study mappable genes JSON
        if hasattr(self, "_mappable_genes_out_dir"):
            out_path = self._write_mappable_genes_json(
                study, mappable_genes, self._mappable_genes_out_dir
            )
            print(f"Saved [{study}] mappable genes JSON to: {out_path}")

        # Simple debug output
        print(f"[{study}] mappable_genes count: {len(mappable_genes)}")
        logger.info("[%s] mappable_genes count: %d", study, len(mappable_genes))

        if "STUDY_ID" not in df.columns:
            df = df.assign(STUDY_ID=study)

        return df

    def run_transformers(self, harvested: Dict[str, Any]) -> pd.DataFrame:
        if not isinstance(harvested, dict):
            raise TypeError("run_transformers() requires a dict:  {study: harvested_data}")

        # -----------------------------------------
        # Output directory (define ONCE, BEFORE loop)
        # -----------------------------------------
        loc = os.getcwd()
        base_dir = os.path.join(loc, "..", "transformers")
        base_dir = os.path.abspath(base_dir)
        study_out_dir = os.path.join(base_dir, "munged_data")
        save_loc = os.path.join(study_out_dir, "combined")
        os.makedirs(save_loc, exist_ok=True)

        # -----------------------------------------
        # Per-study mappable genes JSON output dir
        # -----------------------------------------
        self._mappable_genes_out_dir = os.path.join(save_loc, "mappable_genes")

        #frequency results
        self._frequency_results_out_dir = os.path.join(save_loc, "frequency_results")
        os.makedirs(self._frequency_results_out_dir, exist_ok=True)
        print(f"Writing per-study frequency results JSON to: {self._frequency_results_out_dir}")

        # Initialize storage for frequency results
        self.frequency_results_by_study = {}

        os.makedirs(self._mappable_genes_out_dir, exist_ok=True)
        print(f"Writing per-study mappable genes JSON to: {self._mappable_genes_out_dir}")

        dfs: List[pd.DataFrame] = []

        for study, hdata in tqdm(
            harvested.items(), desc="Transforming studies", unit="study"
        ):
            logger.info("Transforming study %s...", study)
            df = self._transform_one(study, hdata)
            dfs.append(df)

        if not dfs:
            raise ValueError("No frames returned by transformers.")

        combined = pd.concat(dfs, ignore_index=True, sort=False)

        # -----------------------------------------
        # Create subdirectories for organized output
        # -----------------------------------------
        mappable_genes_dir = os.path.join(save_loc, "mappable_genes")
        frequencies_dir = os.path.join(save_loc, "frequencies")
        norm_failures_dir = os.path.join(save_loc, "norm_failures")
        
        os.makedirs(mappable_genes_dir, exist_ok=True)
        os.makedirs(frequencies_dir, exist_ok=True)
        os.makedirs(norm_failures_dir, exist_ok=True)

        # -----------------------------------------
        # Gene QC summary table and mappable genes
        # -----------------------------------------
        gene_qc_df = (
            pd.DataFrame.from_dict(self.gene_qc_by_study, orient="index")
            .reset_index()
            .rename(columns={"index": "STUDY_ID"})
            .sort_values("STUDY_ID")
        )
        gene_qc_out_path = os.path.join(mappable_genes_dir, "gene_qc_summary_per_study.csv")
        gene_qc_df.to_csv(gene_qc_out_path, index=False)
        print(f"Saved gene QC summary table to: {gene_qc_out_path}")

        # Merged mappable genes JSON (all studies in one file)
        merged_genes_out_path = os.path.join(mappable_genes_dir, "mappable_genes_all_studies.json")
        self._write_all_mappable_genes_json(merged_genes_out_path)
        print(f"Saved merged mappable genes JSON to: {merged_genes_out_path}")

        # -----------------------------------------
        # Frequency results and QC
        # -----------------------------------------
        # Write merged frequency results
        merged_freq_out_path = os.path.join(frequencies_dir, "frequency_results_all_studies.json")
        self._write_all_frequency_results_json(merged_freq_out_path)
        print(f"Saved merged frequency results JSON to: {merged_freq_out_path}")

        # Frequency QC summary
        freq_qc_df = self._create_frequency_qc_summary()
        freq_qc_out_path = os.path.join(frequencies_dir, "frequency_qc_summary_per_study.csv")
        freq_qc_df.to_csv(freq_qc_out_path, index=False)
        print(f"Saved frequency QC summary to: {freq_qc_out_path}")

        # -----------------------------------------
        # ETHNICITY counts: rows=ETHNICITY, cols=STUDY_ID
        # -----------------------------------------
        # TODO: why does chl_sccc_2023 study show up as "type_of_cancer: chl" in these age and ethnicity
        eth_df = combined.copy()
        eth_df["ETHNICITY"] = eth_df.get("ETHNICITY", pd.Series(pd.NA, index=eth_df.index))
        eth_df["ETHNICITY"] = eth_df["ETHNICITY"].replace("", pd.NA).fillna("Unknown")

        ethnicity_table = (
            eth_df.groupby(["ETHNICITY", "STUDY_ID"])
            .size()
            .unstack("STUDY_ID", fill_value=0)
            .sort_index()
        )
        ethnicity_out_path = os.path.join(save_loc, "ethnicity_counts_per_study_wide.csv")
        ethnicity_table.to_csv(ethnicity_out_path, index=True)
        print(f"Saved ETHNICITY wide table to: {ethnicity_out_path}")

        # -----------------------------------------
        # AGE bucket counts: rows=STUDY_ID, cols=AGE_RANGE
        # -----------------------------------------
        AGE_COL = "AGE"
        age_bins = [-1, 0, 5, 10, 15, 18, 25, 40, 60, 120]
        age_labels = ["<1", "1–5", "6–10", "11–15", "16–18", "19–25", "26–40", "41–60", "60+"]

        age_df = combined.copy()
        age_df[AGE_COL] = pd.to_numeric(
            age_df.get(AGE_COL, pd.Series(pd.NA, index=age_df.index)), errors="coerce"
        )
        age_df["AGE_RANGE"] = pd.cut(
            age_df[AGE_COL],
            bins=age_bins,
            labels=age_labels,
            right=True,
        )
        age_df["AGE_RANGE"] = age_df["AGE_RANGE"].cat.add_categories(["Unknown"]).fillna("Unknown")

        age_table = (
            age_df.groupby(["STUDY_ID", "AGE_RANGE"])
            .size()
            .unstack("AGE_RANGE", fill_value=0)
            .reindex(columns=age_labels + ["Unknown"], fill_value=0)
            .sort_index()
        )
        age_out_path = os.path.join(save_loc, "age_range_counts_per_study_wide.csv")
        age_table.to_csv(age_out_path, index=True)
        print(f"Saved AGE wide table to: {age_out_path}")

        # -----------------------------------------
        # Failed normalizations CSVs
        # -----------------------------------------
        if self.failed_genes:
            failed_genes_df = pd.DataFrame(self.failed_genes)
            
            # Write combined file with all studies
            combined_genes_path = os.path.join(norm_failures_dir, "combined_failed_gene_normalizations.csv")
            failed_genes_df.to_csv(combined_genes_path, index=False)
            print(f"Saved combined failed gene normalizations to: {combined_genes_path}")
            
            # Write per-study files
            for study_id in failed_genes_df['study_id'].unique():
                study_genes = failed_genes_df[failed_genes_df['study_id'] == study_id]
                failed_genes_path = os.path.join(norm_failures_dir, f"{study_id}_failed_gene_normalizations.csv")
                study_genes.to_csv(failed_genes_path, index=False)
                print(f"Saved failed gene normalizations for {study_id} to: {failed_genes_path}")
        
        if self.failed_variants:
            failed_variants_df = pd.DataFrame(self.failed_variants)
            
            # Write combined file with all studies
            combined_variants_path = os.path.join(norm_failures_dir, "combined_failed_variant_normalizations.csv")
            failed_variants_df.to_csv(combined_variants_path, index=False)
            print(f"Saved combined failed variant normalizations to: {combined_variants_path}")
            
            # Write per-study files
            for study_id in failed_variants_df['study_id'].unique():
                study_variants = failed_variants_df[failed_variants_df['study_id'] == study_id]
                failed_variants_path = os.path.join(norm_failures_dir, f"{study_id}_failed_variant_normalizations.csv")
                study_variants.to_csv(failed_variants_path, index=False)
                print(f"Saved failed variant normalizations for {study_id} to: {failed_variants_path}")

        # -----------------------------------------
        # Cache statistics
        # -----------------------------------------
        print(f"\nCache Statistics:")
        print(f"  Unique genes cached: {len(self.gene_cache)}")
        print(f"  Unique variants cached: {len(self.variant_cache)}")
        print(f"  Total API calls saved by caching: ~{len(self.gene_cache) + len(self.variant_cache)}")

        # -----------------------------------------
        # Save combined dataframe to CSV on disk
        # -----------------------------------------
        output_path = os.path.join(save_loc, "combined_cBioPortal_transformed.csv")
        combined.to_csv(output_path, index=False)
        print(f"Saved combined transformer output to: {output_path}")

        return combined


# Convenience function to keep old API working if you want
def run_transformers(harvested: Dict[str, Any]) -> pd.DataFrame:
    base = cBioportalTransformerBase()
    return base.run_transformers(harvested)


# Optional: CLI runner
if __name__ == "__main__":
    from metakb.harvesters.cbioportal import cBioportalHarvester

    harvester = cBioportalHarvester()
    data = harvester.harvest()  # all studies

    base = cBioportalTransformerBase()
    df = base.run_transformers(data)
    print(df.head())
    print("Combined shape:", df.shape)
