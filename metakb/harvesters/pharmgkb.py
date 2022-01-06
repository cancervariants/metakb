"""Provide tools for harvesting data from PharmGKB."""
import tempfile
from pathlib import Path
import logging
import zipfile
from typing import List, Dict, Any
import csv
import json

import requests

from metakb.harvesters.base import Harvester


logger = logging.getLogger('metakb.harvesters.pharmgkb')
logger.setLevel(logging.DEBUG)


class PharmGKBHarvester(Harvester):
    """Harvest PharmGKB data and prepare for transformation into data model."""

    def __init__(self):
        """Initialize harvester instance"""
        super().__init__()
        self.src_dir = self.harvest_dir.parents[0] / "source"

    def harvest(self, fn="pharmgkb_harvester.json") -> None:
        """Retrieve and store records from a resource. Records may be stored in
        any manner, but must be retrievable by :method:`iterate_records`.

        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        # check for recency of data
        file_list = [
            "variants.tsv",
            "clinical_annotations.tsv",
            "clinical_ann_evidence.tsv",
        ]
        if not all([(self.src_dir / f).exists() for f in file_list]):
            self._fetch_data()

        complete_data = {
            "variants": self._harvest_variants,
            "drug_labels": self._harvest_drug_labels,
            "clinical_annotations": self._harvest_clinical_annotations,
            "variant_annotations": self._harvest_variant_annotations
        }
        with open(fn, "w") as f:
            json.dump(complete_data, f)

    def _fetch_data(self) -> None:
        """Retrieve data from pharmgkb"""
        # add as needed
        url_list = [
            "https://api.pharmgkb.org/v1/download/file/data/clinicalAnnotations.zip",  # noqa: E501
            "https://api.pharmgkb.org/v1/download/file/data/variants.zip",
            "https://api.pharmgkb.org/v1/download/file/data/variantAnnotations.zip",  # noqa: E501
            "https://api.pharmgkb.org/v1/download/file/data/relationships.zip",
            "https://api.pharmgkb.org/v1/download/file/data/drugLabels.zip",
            "https://api.pharmgkb.org/v1/download/file/data/guidelineAnnotations.json.zip"  # noqa: E501
            "https://api.pharmgkb.org/v1/download/file/data/clinicalVariants.zip",  # noqa: E501
        ]
        for url in url_list:
            self._http_download(url)
        # delete unused stuff

    def _http_download(self, url: str) -> None:
        """Retrieve data via HTTP
        :param str url: URL to fetch data from
        """
        dl_path = Path(tempfile.gettempdir()) / "metakb_dl_tmp"
        with requests.get(url, stream=True) as r:
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                logger.error(f"{self.__class__.__name__} download failed: "
                             f"{url}")
                raise e
            with open(dl_path, "wb") as h:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        h.write(chunk)

        with zipfile.ZipFile(dl_path, "r") as zip_ref:
            zip_ref.extractall(path=self.src_dir / "source")

    def _split_comma_column(self, column: str) -> List[str]:
        """Correctly break up PharmGKB list-like columns.
        Some PharmGKB columns separate individual values with commas,
        and use double-quotes to keep compound terms together, eg
        'diclofenac,"losartan","tolbutamide"'. This method breaks them up
        while preserving those internal conjunctions.
        :param column str: a comma-separated column
        :return: List of terms taken from column
        """
        column_split = [i for i in column.split("\"") if i and (i != ",")]
        column_stripped = [i.rstrip(",") for i in column_split]
        return column_stripped

    def _harvest_variants(self) -> Dict[str, Dict]:
        """Extract variant concepts.
        :return: Dictionary keying variant ID to complete variant object
        """
        variant_file_path = self.src_dir / "variants.tsv"
        with open(variant_file_path, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        variants: Dict[str, Dict] = {}
        for row in reader:
            variant: Dict[str, Any] = {
                "variant_id": row["Variant ID"],
                "location": row["Location"],
                "synonyms": row["Synonyms"]
            }

            name = variant["Variant Name"]  # typically refSNP ID
            if name:
                variant["name"] = name

            gene_ids = variant["Gene IDs"]
            gene_symbols = variant["Gene Symbols"]
            if gene_ids and gene_symbols:
                if "," in gene_ids and "," in gene_symbols:
                    gene_ids_split = gene_ids.split(",")
                    gene_symbols_split = gene_symbols.split(",")
                    variant["genes"] = [
                        {
                            "gene_id": gene_id,
                            "gene_symbol": gene_symbol
                        }
                        for gene_id, gene_symbol
                        in zip(gene_ids_split, gene_symbols_split)
                    ]
                else:
                    variant["genes"] = [{
                        "gene_id": gene_ids,
                        "gene_symbol": gene_symbols
                    }]
            variants[row["Variant ID"]] = variant
        return variants

    def _harvest_drug_labels(self) -> List[Dict]:
        """Capture data from drug label annotations.

        "Drug label annotations are annotations on medication labels that
        contain pharmacogenomic (PGx) information. PharmGKB provides American,
        Canadian, European, Swiss and Japanese medication labels with
        pharmacogenomic information."
        https://www.pharmgkb.org/whatIsPharmgkb/annotations

        :return: List of drug label annotation objects
        """
        drug_labels_file = self.src_dir / "drugLabels.tsv"
        with open(drug_labels_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        drug_labels = []
        for row in reader:
            drug_label: Dict[str, Any] = {
                "druglabel_id": row["PharmGKB ID"],
                "pgx_level": row["Testing Level"],
                "description": row["Name"],
                "source": row["Source"],
            }

            biomarker_flag = row.get("Biomarker Flag")
            if biomarker_flag:
                drug_label["fda_biomarker_status"] = biomarker_flag

            if row.get("Prescribing"):
                drug_label["prescribing"] = True

            if row.get("Has Prescribing Info"):
                drug_label["prescribing_info"] = True

            if row.get("Has Dosing Info"):
                drug_label["dosing_info"] = True

            if row.get("Has Alternate Drug"):
                drug_label["alternate_drug"] = True

            if row.get("Cancer Genome"):
                drug_label["cancer_genome"] = True

            genes = row.get("Genes")
            if genes:
                drug_label["genes"] = [
                    {"symbol": g} for g in genes.split("; ")
                ]

            variations = row.get("Variants/Haplotypes")
            if variations:
                drug_label["variations"] = [
                    {"id": v} for v in variations.split("; ")
                ]

            therapies = row.get("Chemicals")
            if therapies:
                drug_label["therapies"] = [
                    {"label": t for t in therapies.split("; ")}
                ]

            if row.get("Cancer Genome"):
                drug_label["cancer_genome"] = True

            drug_labels.append(drug_label)
        return drug_labels

    def _harvest_clinical_annotations(self) -> Dict[str, Any]:
        """Extract clinical annotation objects.

        "Clinical annotations summarize all of PharmGKB’s annotations of
        published evidence for the relationship between a particular genetic
        variant and a medication. They are given a rating by PharmGKB depending
        on how much published evidence there is for a relationship found in
        PharmGKB, and the quality of that evidence. Clinical annotations are
        based on variant annotations, and are created by PharmGKB curators by
        bringing together all the variant annotations that discuss the same
        genetic variant and same medication response."
        https://www.pharmgkb.org/whatIsPharmgkb/clinicalAnnotations

        :return: Dict containing evidence, annotations, and alleles
        """
        clinann_meta_file = self.src_dir / "clinical_annotations.tsv"
        clinical_annotations = {}
        with open(clinann_meta_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            annotation_id = row["Clinical Annotation ID"]
            annotation = {
                "clinical_annotation_id": annotation_id,
                "variations": row["Variant/Haplotypes"].split(", "),
                "genes": row["Gene"].split(";"),
                "evidence_level": f"pharmgkb:{row['Level of Evidence']}",
                "score": row["Score"],
                "phenotype_categories": row["Phenotype Category"].split(";"),
                "drugs": row["Drug(s)"].split(";"),
                "diseases": row["Phenotype(s)"].split(";"),
            }

            override = row["Level Override"]
            if override:
                annotation["evidence_level_override"] = override

            modifiers = row["Level Modifiers"]
            if modifiers:
                annotation["level_modifiers"] = modifiers.split("; ")

            special_population = row["Specialty Population"]
            if special_population:
                annotation["specialty_population"] = special_population

            clinical_annotations[annotation_id] = annotation

        ev_file = self.src_dir / "clinical_ann_evidence.tsv"
        with open(ev_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        evidence_list = []
        for row in reader:
            evidence: Dict[str, Any] = {
                "evidence_id": row["Evidence ID"],
                "evidence_url": row["Evidence URL"],
                "evidence_type": row["Evidence Type"],
                "pmid": row["PMID"],
                "clinical_annotation_id": row["Clinical Annotation ID"],
                "description": row["Summary"],
                "score": row["Score"],
            }
            evidence_list.append(evidence)

        alleles_file = self.src_dir / "clinical_ann_alleles.tsv"
        with open(alleles_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        alleles = []
        for row in reader:
            alleles.append({
                "clinical_annotation_id": row["Clinical Annotation ID"],
                "genotype_allele": row["Genotype/Allele"],
                "description": row["Annotation Text"],
                "function": row["Allele Function"]
            })
        return {
            "clinical_annotations": clinical_annotations,
            "evidence": evidence_list,
            "alleles": alleles
        }

    def _harvest_var_file(self, file: Path) -> List:
        """Harvest individual variant annotation file.
        :param Path file: path to file
        :return: List of captured annotations
        """
        with open(file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
        annotations = []
        for row in reader:
            annotation = {
                "variant_annotation_id": row["Variant Annotation ID"],
                "variants": row["Variant/Haplotypes"].split(", "),
                "document_pmid": row["PMID"],
                "phenotype_categories": self._split_comma_column(
                    row["Phenotype Categories"]
                ),
                "significance": row["Significance"],
                "notes": row["Notes"],
                "description": row["Sentence"],
                "genotype_allele": row["Alleles"],
                "specialty_population": row["Specialty Population"]
            }
            genes = row["Gene"]
            if genes:
                annotation["genes"] = self._split_comma_column(row["Gene"])
            drugs = row["Drug(s)"]
            if drugs:
                annotation["therapies"] = self._split_comma_column(
                    row["Drug(s)"]
                )
            annotations.append(annotation)
        return annotations

    def _harvest_variant_annotations(self) -> List[Dict]:
        """Harvest data from variant annotation files.

        "PharmGKB variant annotations report the association between a variant
        (e.g. SNP, indel, repeat, haplotype) and a drug phenotype from a single
        publication."
        https://www.pharmgkb.org/variantAnnotations

        :return: List of annotation objects
        """
        var_drug_ann_file = self.src_dir / "var_drug_ann.tsv"
        annotations = self._harvest_var_file(var_drug_ann_file)
        var_fa_ann_file = self.src_dir / "var_fa_ann.tsv"
        annotations += self._harvest_var_file(var_fa_ann_file)
        var_pheno_ann_file = self.src_dir / "var_pheno_ann.tsv"
        annotations += self._harvest_var_file(var_pheno_ann_file)
        return annotations

    def _harvest_clinical_guideline_annotations(self) -> List:
        # TODO -- parsable?
        return []
