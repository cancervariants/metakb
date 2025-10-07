import os
from os import environ
environ["AWS_ACCESS_KEY_ID"]="dummy"
environ["AWS_SECRET_ACCESS_KEY"]="dummy"
environ["AWS_SESSION_TOKEN"]="dummy"
# environ["SEQREPO_ROOT_DIR"]="/usr/local/share/seqrepo/2024-12-20"
# os.environ["SEQREPO_ROOT_DIR"] = "/usr/local/share/seqrepo/2024-12-20"
# os.environ["SEQREPO_ROOT"] = "/usr/local/share/seqrepo/2024-12-20"

from metakb.transformers.base import (
    Transformer
)
import pandas as pd
import requests
import time
import pprint
from urllib.parse import quote_plus
import re
import json
from tqdm import tqdm
from typing import List

import logging
_logger = logging.getLogger(__name__)

from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)



MUT_HEADERS = ['Hugo_Symbol',
            'Chromosome',
            'Start_Position', 
            'End_Position',
            'Consequence',
            'Variant_Classification',
            'Variant_Type',
            'Reference_Allele',
            'Tumor_Seq_Allele2',
            'Tumor_Sample_Barcode',
            'Sequence_Source',
            'HGVSc',
            'HGVSp',
            'HGVSp_Short',
            'Transcript_ID',
            'RefSeq',
            'Protein_position']

PATIENT_HEADERS = ['PATIENT_ID',
                   'AGE',
                   'SEX',
                   'ETHNICITY',
                   'Consequence']

SAMPLE_HEADERS = ['PATIENT_ID',
                  'SAMPLE_ID',
                  'SAMPLE_CLASS',
                  'ONCOTREE_CODE',
                  'CANCER_TYPE',
                  'CANCER_TYPE_DETAILED',
                  'TMB_NONSYNONYMOUS']

PATTERN = re.compile(r'^23-')

class cBioportalTransformer(Transformer):
    """A class for transforming cBioportal Data to the common data model."""

    # TODO: TypeError: Can't instantiate abstract class cBioportalTransformer without an implementation for abstract method '_create_cache'

    def __init__(self):
        super().__init__()
        self.final_df = None

    # TODO: These private methods don't do anything meaningful right towards cbioportal data now
    def _get_therapeutic_substitute_group(self, therapeutic_sub_group_id, therapies, therapy_interaction_type):
        return super()._get_therapeutic_substitute_group(therapeutic_sub_group_id, therapies, therapy_interaction_type)


    def _get_therapy(self, therapy):
        return super()._get_therapy(therapy)
    
    def _create_cache(self):
        pass

    def _flag_rows_chrom_23(self, df):
        """
        Create "Chrom_23" column, True for those with Chromosome = 23

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        
        Returns
        -------
        dataframe
        """
        df["Chrom_23"] = False
        # print(combined_df.head)
        df["Chrom_23"] = df["Chromosome"].astype(str).str.strip().eq("23")
        df.loc[df["Chromosome"] == 23, "Chrom_23"] = True
        return df
    
    def _chr23_female(self, df):
        """
        Convert Chromosome 23 to 'X' for rows where SEX is female.
        
        Parameters
        ----------
        df : pd.DataFrame
            Must contain columns 'Chromosome' and 'SEX'.
        
        Returns
        -------
        dataframe
        """
        # Ensure we’re comparing like with like
        chr_col = df["Chromosome"].astype(str).str.strip()
        sex_col = df["SEX"].astype(str).str.upper().str.strip()   # handles 'F', 'f', 'Female', etc.
        
        mask = (chr_col == "23") & (sex_col.str.startswith("F"))
        df.loc[mask, "Chromosome"] = "X"
        return df
    
    def _add_cols_chrom_23_male(self, df):
        """
        Create "Chr23_X and Chr23_Y" columns, fill with false

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        
        Returns
        -------
        dataframe
        """
        df["Chr23_X"] = False
        df["Chr23_Y"] = False
        return df
    
    def _chr23_to_X(self, variant: str) -> str:
        """
        Convert a single '23-' prefix in a variant string to 'X-'.

        Parameters
        ----------
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        
        Returns
        -------
        variant: str
        """
        return PATTERN.sub('X-', variant) if isinstance(variant, str) else variant
    
    def _chr23_to_Y(self, variant: str) -> str:
        """
        Convert a single '23-' prefix in a variant string to 'Y-'.

        Parameters
        ----------
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        
        Returns
        -------
        variant: str
        """
        return PATTERN.sub('Y-', variant) if isinstance(variant, str) else variant
    
    def _test_variant_tokenization(self, variant: str, delay=0.5):
        """
        Fetch normalized variant info from VICC API for a single variant string.

        Parameters
        ----------
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        delay : float
            Seconds to wait between API requests (default 0.5).

        Returns
        -------
        pd.DataFrame
            DataFrame with original variant and raw JSON string response.
        """
        BASE_URL = "http://localhost:8001/variation/"
        HEADERS = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  # mimics a browser
            }
        results = []
        url = f"{BASE_URL}normalize?q={variant}&hgvs_dup_del_mode=default&input_assembly=GRCh37"
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "variant": variant,
                    "response": json.dumps(data)
                })
            else:
                results.append({
                    "variant": variant,
                    "response": f"Error {response.status_code}: {response.text}"
                })
        except Exception as e:
            results.append({
                "variant": variant,
                "response": f"Exception: {str(e)}"
            })
        time.sleep(delay)
        return pd.DataFrame(results)
    
    #test tokenization on X chromosome
    def _check_for_x_variant(self, df, variant):
        """
        Test tokenization of chromosome 23 variants as X variants

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        
        Returns
        -------
        dataframe
        """
        # Convert the variant to X-style format (e.g., "23-..." → "X-...")
        variant_x = self._chr23_to_X(variant)
        # Query the API and get a one-row DataFrame
        x_df = self._test_variant_tokenization(variant_x)  # returns a one-row DataFrame
        # Extract and parse JSON string from the response
        raw_response = x_df.loc[0, "response"]
        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError:
            print(f"❌ Failed to parse JSON for: {variant_x}")
            return df
        # Ensure 'variation' is in the parsed response
        if "variation" not in parsed_response:
            print(f"⚠️ 'variation' key not found for: {variant_x}")
            return df
        # Try to extract hgnc_id if available
        hgnc_id = None
        try:
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0]["hgnc_id"]
            print(f"✅ Extracted HGNC ID for {variant_x}: {hgnc_id}")
        except (KeyError, IndexError, TypeError):
            print(f"⚠️ No HGNC ID found for: {variant_x}")
        # Initialize columns if needed
        if "x_hgnc_id" not in df.columns:
            df["x_hgnc_id"] = "no_value"
        if "Chr23_X" not in df.columns:
            df["Chr23_X"] = False
        # Reconstruct variant string from each row to match normalized variant_x
        reconstructed = (
            "X-" +
            df["Start_Position"].astype(str).str.strip() + "-" +
            df["Reference_Allele"].astype(str).str.strip() + "-" +
            df["Tumor_Seq_Allele2"].astype(str).str.strip()
        )
        # Mask: match rows on reconstructed X-variant and Chromosome == 23
        chrom_col = df["Chromosome"].astype(str).str.strip()
        mask = (chrom_col == "23") & (reconstructed == variant_x)
        print(f"🧪 Matched {mask.sum()} row(s) for {variant_x}")
        # Set Chr23_X = True
        df.loc[mask, "Chr23_X"] = True
        # Set x_hgnc_id if available
        if hgnc_id is not None:
            df.loc[mask, "x_hgnc_id"] = hgnc_id
        return df
    
    #test tokenizationo n Y chromosome
    def _check_for_y_variant(self, df, variant):
        """
        Test tokenization of chromosome 23 variants as Y variants

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        
        Returns
        -------
        dataframe
        """
        # Convert the variant to Y-style format (e.g., "23-..." → "Y-...")
        variant_y = self._chr23_to_Y(variant)
        # Query the API and get a one-row DataFrame
        y_df = self._test_variant_tokenization(variant_y)  # returns a one-row DataFrame
        # Extract and parse JSON string from the response
        raw_response = y_df.loc[0, "response"]
        try:
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError:
            print(f"❌ Failed to parse JSON for: {variant_y}")
            return df
        # Ensure 'variation' is in the parsed response
        if "variation" not in parsed_response:
            print(f"⚠️ 'variation' key not found for: {variant_y}")
            return df
        # Try to extract hgnc_id if available
        hgnc_id = None
        try:
            hgnc_id = parsed_response["variation"]["extensions"][0]["value"][0]["hgnc_id"]
            print(f"✅ Extracted HGNC ID for {variant_y}: {hgnc_id}")
        except (KeyError, IndexError, TypeError):
            print(f"⚠️ No HGNC ID found for: {variant_y}")
        # Initialize columns if needed
        if "y_hgnc_id" not in df.columns:
            df["y_hgnc_id"] = "no_value"
        if "Chr23_Y" not in df.columns:
            df["Chr23_Y"] = False
        # Reconstruct variant string from each row to match normalized variant_y
        reconstructed = (
            "Y-" +
            df["Start_Position"].astype(str).str.strip() + "-" +
            df["Reference_Allele"].astype(str).str.strip() + "-" +
            df["Tumor_Seq_Allele2"].astype(str).str.strip()
        )
        # Mask: match rows on reconstructed Y-variant and Chromosome == 23
        chrom_col = df["Chromosome"].astype(str).str.strip()
        mask = (chrom_col == "23") & (reconstructed == variant_y)
        print(f"🧪 Matched {mask.sum()} row(s) for {variant_y}")
        # Set Chr23_Y = True
        df.loc[mask, "Chr23_Y"] = True
        # Set y_hgnc_id if available
        if hgnc_id is not None:
            df.loc[mask, "y_hgnc_id"] = hgnc_id
        return df

    # driver function for chr23
    def _chr23_male(self, df, variant):
        """
        Driver function for _check_for_x_variant and _check_for_y_variant.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        variant : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        
        Returns
        -------
        dataframe
        """
        if "Chr23_X" not in df.columns:
            df["Chr23_X"] = False
        if "Chr23_Y" not in df.columns:
            df["Chr23_Y"] = False
        df = self._check_for_x_variant(df, variant)    # pass **both** args
        df = self._check_for_y_variant(df, variant)
        return df

    #reassign chromosome for male chromosome 23 variants
    def _correct_male_chrom23(self, df):
        """
        Correct male chromosome 23 variants. 
        Notes if variant is ambiguous in new col ("XY" for tokenizes to both X and Y. "neither if it tokenizes to neither X nor Y)

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        
        Returns
        -------
        dataframe
        """
        # Initialize ambig_chrom column
        df["ambig_chrom"] = "non-ambiguous"
        def update_row(row):
            if row.get("Chrom_23") is True and str(row.get("SEX", "")).strip().lower() == "male":
                if row["Chr23_X"] and not row["Chr23_Y"]:
                    row["Chromosome"] = "X"
                elif row["Chr23_Y"] and not row["Chr23_X"]:
                    row["Chromosome"] = "Y"
                elif row["Chr23_X"] and row["Chr23_Y"]:
                    row["ambig_chrom"] = "XY"
                else:  # neither Chr23_X nor Chr23_Y is True
                    row["ambig_chrom"] = "neither"
            return row
        # Apply corrections row-by-row
        df = df.apply(update_row, axis=1)
        # Check for ambiguous rows
        ambig_rows = df[df["ambig_chrom"].isin(["XY", "neither"])]
        if not ambig_rows.empty:
            print(f"⚠️ Found {len(ambig_rows)} row(s) with ambiguous chromosome identification.")
            print(ambig_rows[["temp_Gnomad_Notation", "Hugo_Symbol", "ambig_chrom"]].head())
        return df

    def _resolve_ambiguous_chromosomes(self, df):
        """
        Resolve ambiguous Chr23 variants in male samples and flag problematic rows.

        - For Chrom_23 == True and SEX == male:
        - If both x_hgnc_id and y_hgnc_id have values → ⚠️ warn
        - If neither has values → ❌ warn
        - If ambig_chrom == "XY" or "neither", try to resolve Chromosome field

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'Chromosome'.
        
        Returns
        -------
        dataframe
        """
        chrom23_male_mask = (
            (df["Chrom_23"] == True) &
            (df["SEX"].str.lower().str.strip() == "male")
        )

        for idx, row in df[chrom23_male_mask].iterrows():
            x_id = str(row.get("x_hgnc_id", "")).strip()
            y_id = str(row.get("y_hgnc_id", "")).strip()
            ambig_status = row.get("ambig_chrom", "not_set")

            # ⚠️ Raise general warnings, regardless of ambig_chrom
            if x_id != "no_value" and y_id != "no_value":
                print(f"⚠️ Row {idx}: Both x_hgnc_id and y_hgnc_id have values. Manual check recommended.")
            elif x_id == "no_value" and y_id == "no_value":
                print(f"❌ Row {idx}: Neither x_hgnc_id nor y_hgnc_id has a value.")

            # ✅ Try resolving ambiguous chromosomes
            if ambig_status in ["XY", "neither"]:
                if x_id != "no_value" and y_id == "no_value":
                    df.at[idx, "Chromosome"] = "X"
                    df.at[idx, "ambig_chrom"] = "resolved_X"
                    print(f"✅ Resolved index {idx} to Chromosome X")
                elif y_id != "no_value" and x_id == "no_value":
                    df.at[idx, "Chromosome"] = "Y"
                    df.at[idx, "ambig_chrom"] = "resolved_Y"
                    print(f"✅ Resolved index {idx} to Chromosome Y")
                elif x_id != "no_value" and y_id != "no_value":
                    print(f"⚠️ Index {idx}: Ambiguous Chromosome with both HGNC IDs present.")
                else:
                    print(f"❌ Index {idx}: Ambiguous Chromosome with no HGNC ID found.")

        return df

    #get hgnc id from gene normalizer
    def _test_gene_tokenization(self, gene: str, delay=0.5):
        """
        Fetch normalized gene info from VICC API for a single gene.

        Parameters
        ----------
        gene : str
            A GnomAD-style variant (e.g., '23-2408485-G-C').
        delay : float
            Seconds to wait between API requests (default 0.5).

        Returns
        -------
        pd.DataFrame
            DataFrame with original variant and raw JSON string response.
        """
        BASE_URL = "https://normalize.cancervariants.org/gene/"
        HEADERS = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        results = []
        url = f"{BASE_URL}normalize?q={gene}"
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "gene": gene,
                    "response": json.dumps(data)
                })
            else:
                results.append({
                    "gene": gene,
                    "response": f"Error {response.status_code}: {response.text}"
                })
        except Exception as e:
            results.append({
                "gene": gene,
                "response": f"Exception: {str(e)}"
            })
        time.sleep(delay)
        return pd.DataFrame(results)

    #TODO: is this not used?
    #update hgnc_id gene column
    def _update_gene_hgnc_id_inplace(self, df):
        for idx, row in df.iterrows():
            if row.get("Chrom_23") and str(row.get("SEX", "")).strip().lower() == "male":
                try:
                    result = self._test_gene_tokenization(row["Hugo_Symbol"])
                    full_id = result["gene"]["id"]  # e.g., "normalize.gene.hgnc:447"
                    hgnc_id = full_id.split(":")[-1]  # Extract "447"
                    df.at[idx, "gene_hgnc_id"] = hgnc_id
                except Exception as e:
                    print(f"⚠️ Could not extract HGNC ID for {row['Hugo_Symbol']}: {e}")
        print(df.head())
        return df
    
    # query gene normalizer
    def _populate_gene_hgnc_col(self, gene_list, df):
        # Add the column once
        if "gene_hgnc_id" not in df.columns:
            df["gene_hgnc_id"] = None
        for gene in tqdm(gene_list, desc="Processing genes"):
        # for gene in gene_list:
            print(f"▶️ Checking gene: {gene}")
            gene_df = self._test_gene_tokenization(gene)
            # Extract and parse JSON string from the response
            raw_response = gene_df.loc[0, "response"]
            try:
                parsed_response = json.loads(raw_response)
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON for: {gene}")
                continue
            if "gene" not in parsed_response:
                print(f"⚠️ 'gene' key not found for: {gene}")
                continue
            try:
                hgnc_id = parsed_response["gene"]["id"].split(":")[-1]
                print(f"✅ Extracted HGNC ID for {gene}: {hgnc_id}")
            except (KeyError, IndexError, TypeError):
                print(f"⚠️ No HGNC ID found for: {gene}")
                continue
            # Apply to matching rows
            df.loc[
                (df["Chrom_23"] == True) & 
                (df["SEX"].str.strip().str.lower() == "male") & 
                (df["Hugo_Symbol"].str.strip() == gene.strip()),
                "gene_hgnc_id"
            ] = hgnc_id
        return df
    
    #check to see if gene hgnc id matches x/y variant hgnc id
    def _validate_gene_hgnc_match(self, df):
        """
        Compare gene_hgnc_id to x_hgnc_id or y_hgnc_id for Chromosome 23 variants in male samples.
        
        Adds a column 'hgnc_id_match':
            - "untested" (default)
            - set to matching hgnc_id if match is found
            - "no_match" if mismatch is found

        Prints warnings for mismatches.
        """
        # Initialize column
        if "hgnc_id_match" not in df.columns:
            df["hgnc_id_match"] = "untested"
        # Define mask for male Chr23 variants
        mask = (df["Chrom_23"] == True) & (df["SEX"].str.strip().str.lower() == "male")
        for idx, row in df[mask].iterrows():
            gene_id = str(row.get("gene_hgnc_id", "")).strip()
            chrom = str(row.get("Chromosome", "")).strip()
            x_id = str(row.get("x_hgnc_id", "")).strip()
            y_id = str(row.get("y_hgnc_id", "")).strip()
            if chrom == "X":
                if gene_id == x_id and gene_id != "no_value":
                    df.at[idx, "hgnc_id_match"] = gene_id
                else:
                    df.at[idx, "hgnc_id_match"] = "no_match"
                    print(f"❌ Row {idx}: X chromosome mismatch. gene_hgnc_id={gene_id}, x_hgnc_id={x_id}")
            elif chrom == "Y":
                if gene_id == y_id and gene_id != "no_value":
                    df.at[idx, "hgnc_id_match"] = gene_id
                else:
                    df.at[idx, "hgnc_id_match"] = "no_match"
                    print(f"❌ Row {idx}: Y chromosome mismatch. gene_hgnc_id={gene_id}, y_hgnc_id={y_id}")
        return df
    # Gene mappable concept
    # loop to get variant data processed
    def _get_exact_gene_mappings(self, hgnc_id: str, gene_symbol: str) -> list[ConceptMapping]:
        """ Get HGNC gene mapping 

        param hgnc_id: the unique numeric identifier provided by HGNC to each gene (with no "hgnc:" prefix) that is present in the CBP data in the column gene_hgnc_id
        param gene_symbol: the gene symbol provided in the CBP data in the column Hugo_Symbol

        return: Concept Mapping for HGNC Gene
        """

        #if there is a value in the gene_hgnc_id column that is the string "untested"
        if not hgnc_id or hgnc_id == "untested":
            return []
        
        #add the "hgnc:" prefix to the unique numeric identifier
        gene_id = f"hgnc:{hgnc_id}"

        return[
            ConceptMapping(
                coding=Coding(
                    id= gene_id,
                    name=gene_symbol,
                    code=gene_id.upper(),
                    system="https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/",
                ),
                relation=Relation.EXACT_MATCH,
                extensions= [Extension(name="cbioportal_annotation", value=True)],
            )]

    def _add_genes(self, genes:list[dict]) -> list:
            """Create gene objects for all CBP records.

            Mutates instance variables ``_cache.genes`` and ``processed_data.genes``

            :param genes: All genes in CBP
            """
            transform_genes = []

        #for gene in genes: #if want ot remove tqdm for backend
            for gene in tqdm(genes, desc="Processing genes"):

                gene_symbol = gene.get("Hugo_Symbol")
                hgnc_id = gene.get("gene_hgnc_id")


                queries = [hgnc_id, gene_symbol] if hgnc_id and hgnc_id != "untested" else [gene_symbol]
                extensions = []

                normalized_gene_id = None
                gene_norm_resp = None

                for query in queries:
                    gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(query)
                    if normalized_gene_id:
                        break

                cbp_mappings = self._get_exact_gene_mappings(hgnc_id,gene_symbol)

                if not normalized_gene_id:
                    _logger.debug(
                        "Gene Normalizer unable to normalize: using queries %s",
                        queries,
                    )
                    mappings = cbp_mappings
                    extensions.append(self._get_vicc_normalizer_failure_ext())
                else:
                    mappings = self._get_vicc_normalizer_mappings(normalized_gene_id, gene_norm_resp)
                    #self._update_normalizer_mappings(mappings, _get_exact_gene_mappings) 
                    #TODO: add this back, figure out how

                cbp_gene = MappableConcept(
                    conceptType="Gene",
                    name=gene_symbol,
                    mappings=mappings,
                    extensions=extensions or None,
                )
                transform_genes.append(cbp_gene)

                #self._cache.genes[gene_symbol] = cbp_gene
            return transform_genes


    def transform(self, harvested_data):

        # for harvested_data_obj in harvested_data:
        self.variants = pd.DataFrame(harvested_data.variants).filter(MUT_HEADERS)
        self.patients = pd.DataFrame(harvested_data.patients).filter(PATIENT_HEADERS)
        self.samples = pd.DataFrame(harvested_data.samples).filter(SAMPLE_HEADERS)
        self.metadata = pd.DataFrame(harvested_data.metadata)

        # TODO: Heather's methods for data cleanup, normalization, and formating to common data model goes here

        # MUT DF
        # Strip whitespace and rename col
        self.variants.columns = self.variants.columns.str.strip()
        self.variants = self.variants.rename(columns={'Tumor_Sample_Barcode': 'SAMPLE_ID'})
        # Check duplicate count
        num_duplicates = self.variants.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.variants[self.variants.duplicated()])
        # save duplicate rows to file
            dupes = self.variants[self.variants.duplicated(keep=False)]
            dupes.to_csv('mut_dupes.csv', index=False)
        # remove duplicates, but keep first occurrence
            self.variants = self.variants.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.variants.shape}")
        else:
            print("No duplicate rows found.")

        # PATIENT DF
        # Check duplicate count
        num_duplicates = self.patients.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.patients[self.patients.duplicated()])
        # remove duplicates, but keep first occurrence
            self.patients = self.patients.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.patients.shape}")
        else:
            print("No duplicate rows found.")
        
        # SAMPLE DF
        # Check duplicate count
        num_duplicates = self.samples.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(self.samples[self.samples.duplicated()])
        # remove duplicates, but keep first occurrence
            self.samples = self.samples.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {self.samples.shape}")
        else:
            print("No duplicate rows found.")
        
        # combine dataframes
        init_combined_df = self.variants.merge(self.samples, on='SAMPLE_ID', how='left')
        combined_df = init_combined_df.merge(self.patients, on='PATIENT_ID', how='left')

        # add study_id column
        study_id = self.metadata.iloc[0, 0]
        study_id = study_id.replace('cancer_study_identifier: ', '')
        combined_df['STUDY_ID'] = study_id

        # remove duplicates from combined dataframe
        # Check duplicate count
        num_duplicates = combined_df.duplicated().sum()
        print(f"Number of duplicate rows : {num_duplicates}")
        # print duplicates (excluding first instance)
        if num_duplicates > 0:
            print("\nDuplicate rows (excluding first instance):")
            print(combined_df[combined_df.duplicated()])
        # remove duplicates, but keep first occurrence
            combined_df = combined_df.drop_duplicates()
            print(f"\nDataFrame shape after removing duplicates: {combined_df.shape}")
        else:
            print("No duplicate rows found.")
        
        # remove data from cell lines
        original_shape = combined_df.shape
        print(f"Original shape: {original_shape}")
        #lines to remove
        removed_df = combined_df[combined_df['SAMPLE_CLASS'] == 'Cell line']
        # remove cell lines
        filtered_df = combined_df[combined_df['SAMPLE_CLASS'] != 'Cell line']
        # calculate how many rows were removed
        rows_removed = original_shape[0] - filtered_df.shape[0]
        print(f"Removed {rows_removed} rows where SAMPLE_CLASS == 'Cell line'")
        # print new shape
        print(f"New shape: {filtered_df.shape}")
        # reassign df
        combined_df = filtered_df
        removed_df.to_csv('cell_lines_removed.csv', index=False)
        removed_df.value_counts("SAMPLE_CLASS")

        #filling in NaNs - AGE, ETHNICITY, Consequence
        cols_to_fill = ['Consequence', 'AGE', 'ETHNICITY']
        fill_value = "No_Data"
        for col in cols_to_fill:
            combined_df[col] = combined_df[col].fillna(fill_value)
        
    
        # correcting Chromosome 23 samples
        # construct temporary Gnomad variant ID column
        combined_df["temp_Gnomad_Notation"] = combined_df.apply(
            lambda row: f"{row['Chromosome']}-{row['Start_Position']}-{row['Reference_Allele']}-{row['Tumor_Seq_Allele2']}",
            axis=1
        )

        #flag rows with chromosome 23
        combined_df = self._flag_rows_chrom_23(combined_df)
        #change chromosome to X for female chromosome 23 samples
        combined_df = self._chr23_female(combined_df)
        # add cols for Chr23_X and Chr23_Y, fill with false
        combined_df = self._add_cols_chrom_23_male(combined_df)

        #set chromosome 23 variants as list
        chrom_23_list = combined_df[
        (combined_df["SEX"].str.lower() == "male") &
        (combined_df["Chrom_23"] == True)
        ]["temp_Gnomad_Notation"].dropna().tolist()
        print("Total variants in list:", len(chrom_23_list))

        #initialize x_hgnc_id and y_hgnc_id
        if "x_hgnc_id" not in combined_df.columns:
            combined_df["x_hgnc_id"] = "no_value"
        if "y_hgnc_id" not in combined_df.columns:
            combined_df["y_hgnc_id"] = "no_value"

        # run driver function
        # Start with a copy of your combined_df
        result_df = combined_df.copy()
        # Iterate through each chromosome 23 variant for male samples
        for variant in tqdm (chrom_23_list, desc="Processing variants"):
        # for variant in chrom_23_list:
            print(f"▶️ Checking variant: {variant}")  # Add this line
            result_df = self._chr23_male(result_df, variant)
        # Now all updates are preserved in result_df
        print(result_df["Chr23_X"].value_counts(dropna=False))
        print(result_df["Chr23_Y"].value_counts(dropna=False))

        #correct male 23 chromosomes and check for ambiguous results
        result_df = self._correct_male_chrom23(result_df)
        print(result_df["ambig_chrom"].value_counts())

        #resolve ambiguous chromosomes
        result_df = self._resolve_ambiguous_chromosomes(result_df)

        #set genes to be queried as list
        # Ensure column exists and is initialized to "untested"
        if "gene_hgnc_id" not in result_df.columns:
            result_df["gene_hgnc_id"] = "untested"
        gene_list = result_df[
            (result_df["SEX"].str.lower() == "male") &
            (result_df["Chrom_23"] == True)
        ]["Hugo_Symbol"].dropna().tolist()
        print("Total genes in list:", len(gene_list))
        print("Sample of gene_list:", gene_list[:5])


        #run gene tokenization
        # Start with a copy of your combined_df
        result_post_23_df = result_df.copy()
        result_post_23_df = self._populate_gene_hgnc_col(gene_list, result_post_23_df)
        print(result_post_23_df["gene_hgnc_id"].value_counts(dropna=False))

        # check hgnc id matches between variation and gene normalizers
        post_validation_df = self._validate_gene_hgnc_match(result_post_23_df)

        #create final gnomAD notation column and populate
        # construct Gnomad variant ID column
        post_validation_df["Gnomad_Notation"] = post_validation_df.apply(
            lambda row: f"{row['Chromosome']}-{row['Start_Position']}-{row['Reference_Allele']}-{row['Tumor_Seq_Allele2']}",
            axis=1
        )

        # remove variant dupes per patient
        # find duplicated (PATIENT_ID, Gnomad_Notation) pairs
        dupe_mask = post_validation_df.duplicated(subset=["PATIENT_ID", "Gnomad_Notation"], keep="first")
        # new DataFrame with the duplicated rows
        patient_variant_dupes = post_validation_df[dupe_mask]
        # remove those rows from the original DataFrame
        post_validation_df_cleaned = post_validation_df[~dupe_mask]
        # write removed rows to file
        patient_variant_dupes.to_csv("patient_variant_dupes.csv", index=False)
        # print the number of rows removed
        print(f"Removed {patient_variant_dupes.shape[0]} rows with duplicated Gnomad_Notation per PATIENT_ID.")
        # post_validation_df_cleaned.to_csv("final_cbp_df.csv", index=False)


        #filling NaNs
        final_df = post_validation_df_cleaned.fillna("No_Data")
        final_df = final_df.replace(r'^\s*$', pd.NA, regex=True).fillna("No_Data")
        final_df.to_csv("final_cbp_df.csv", index=False)

        self.final_df = final_df
        print('Done!')
        # return final_df
    
        # Mappable gene object
        genes = final_df.to_dict(orient='records')
        print(genes[0:5])

        mappable_genes = self._add_genes(genes)
        print(mappable_genes)



        return final_df

        
    
        #Convert CBP data df to a list of dictionaries (each row its own dictionary)
        # genes = df.to_dict(orient='records')
        #Take just a subset to test
        # sub_genes = genes[0:5]


        # TODO: Method's for mapping cleaned up data to Common Data Model format
        # civic.py transformer may have some logic to reuse here
        # test fixture is the end result for a single entry
        #   
        # TODO: Output one CDM per study or one CDM total?

        pass