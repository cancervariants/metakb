"""PMKB harvester"""
import logging
from .base import Harvester
from metakb import PROJECT_ROOT, FileDownloadException
import requests
import re
from typing import List
import pandas as pd
import numpy as np
import json
from pathlib import Path


logger = logging.getLogger('Harvesters')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class PMKB(Harvester):
    """Harvester class for Weill Cornell PMKB"""

    def __init__(self):
        """Set up harvester object"""
        self.assertions = []

    def harvest(self, data_dir: Path = PROJECT_ROOT / 'data' / 'pmkb') -> bool:
        """Harvest PMKB source. Retrieve and store genes, variants, and
        interpretations.

        :param pathlib.Path data_dir: path to local PMKB data source directory
        :return: `True` if successful, `False` otherwise.
        :rtype: bool
        """
        data = self._load_dataframe(data_dir)

        genes = self._build_genes(data)
        variants = self._build_variants(data)
        (evidence, self.assertions) = self._build_ev_and_assertions(data)

        self._create_json(evidence, genes, variants, self.assertions)
        logger.info('PMKB Harvester was successful.')
        return True

    def _load_dataframe(self, data_dir: Path) -> pd.DataFrame:
        """Load source file and perform necessary transformations to build
        workable DataFrame object.

        :param pathlib.Path data_dir: path to local PMKB data source directory
        :return: formatted DataFrame with PMKB data
        :rtype: pd.DataFrame
        """
        self._data_dir = data_dir
        self._data_dir.mkdir(exist_ok=True, parents=True)
        files = [f for f in self._data_dir.iterdir()
                 if f.name.startswith('PMKB_Interpretations_Complete')]
        if not files:
            self._download_csv()
            files = [f for f in self._data_dir.iterdir()
                     if f.name.startswith('PMKB_Interpretations_Complete')]
        newest_filename = sorted(files, reverse=True)[0]   # get most recent
        infile = open(newest_filename, 'r')
        data = pd.read_csv(infile, na_filter=False)
        data = data[1:]
        data.columns = ['gene', 'tumor_types', 'tissue_types', 'variants',
                        'tier', 'interpretation', 'citations']
        for col in ['variants', 'tumor_types', 'tissue_types', 'citations']:
            data[col] = data[col].apply(lambda t: t.split('|'))
        return data

    def _download_csv(self):
        """Download source data from PMKB server. Doesn't return anything,
        but saves file in the location designated by the instance's data_dir
        attribute.
        """
        PMKB_URL = "https://pmkb.weill.cornell.edu/therapies/downloadCSV.csv"
        logger.info("Downloading PMKB source CSV...")
        response = requests.get(PMKB_URL, stream=True)
        if response.status_code == 200:
            fname = ''
            if "Content-Disposition" in response.headers.keys():
                fname = re.findall("filename=(.+)",
                                   response.headers["Content-Disposition"])[0]
                fname = fname.strip('\"')
            else:
                fname = PMKB_URL.split("/")[-1]
            with open(self._data_dir / fname, 'wb') as f:
                f.write(response.content)
            logger.info("PMKB source CSV download successful.")
        else:
            logger.error(f"PMKB source download failed with status code: {response.status_code}")  # noqa: E501
            raise FileDownloadException("PMKB source download failed")

    def _build_genes(self, data: pd.DataFrame) -> List:
        """Build list of genes.

        :param DataFrame data: PMKB input data formatted as a Pandas DataFrame.
        :return: completed List of gene items.
        :rtype: List
        """
        genes = list()
        genes_grouped = data[['gene', 'variants']].groupby('gene',
                                                           as_index=False)
        for (gene, group) in genes_grouped:
            # flatten variant lists
            var_series = group['variants'].apply(pd.Series) \
                .stack().reset_index(drop=True)
            # get counts for variants
            var_counts = pd.Series([v for v in var_series if v != ''],
                                   dtype=str).value_counts()
            genes.append({
                'type': 'gene',
                'name': gene,
                'variants': [
                    {
                        'name': name,
                        'evidence_count': count,
                    }
                    for name, count in var_counts.iteritems()
                ]
            })
        return genes

    def _build_variants(self, data: pd.DataFrame) -> List:
        """Build list of variants.

        :param pd.DataFrame data: PMKB input data formatted as a Pandas
            DataFrame.
        :return: completed List of variant items.
        :rtype: List
        """
        # break assertions out into rows for each included variant
        var_df = pd.DataFrame(
            {
                col: np.repeat(data[col].values, data['variants'].str.len())
                for col in data.columns.drop('variants')
            }).assign(**{
                'variants': np.concatenate(data['variants'].values)
            })
        var_df['variants'].replace('', np.nan, inplace=True)
        # some rows don't provide variants - drop those
        var_df.dropna(subset=['variants'], inplace=True)
        # create DF that groups variants with all associated assertions
        vars_grouped = var_df.groupby('variants')

        variants = list()
        for (variant, group) in vars_grouped:
            gene = group['gene'].iloc[0]
            variants.append({
                'type': 'variant',
                'name': variant,
                'gene': gene,
                'evidence': {
                    'type': 'evidence',
                    # flatten citation lists and reduce to unique cites
                    'sources': list(group['citations'].apply(pd.Series)
                                    .stack().reset_index(drop=True).unique())
                },
                'assertions': [
                    {
                        'type': 'assertion',
                        'description': row['interpretation'],
                        'tumor_types': row['tumor_types'],
                        'tissue_types': row['tissue_types'],
                        'tier': row['tier'],
                        'gene': gene,
                    }
                    for _, row in group.iterrows()
                ]
            })
        return variants

    def _build_ev_and_assertions(self, data: pd.DataFrame) -> (List, List):
        """Build list of evidence and assertions.

        :param pd.DataFrame data: PMKB input data formatted as a Pandas
            DataFrame.
        :return: completed Lists of evidence and assertion items
        :rtype: (List, List)
        """
        evidence = list()
        assertions = list()
        for _, row in data.iterrows():
            evidence.append({
                'type': 'evidence',
                'assertions': [
                    {
                        'type': 'assertion',
                        'description': row['interpretation'],
                        'gene': {
                            'name': row['gene']
                        },
                        'variants': [
                            {'name': v} for v in row['variants']
                        ],
                        'tier': row['tier'],
                        'tumor_types': row['tumor_types'],
                        'tissue_types': row['tissue_types']
                    }
                ],
                'source': {
                    'citations': row['citations']
                }
            })
            assertions.append({
                'type': 'assertion',
                'gene': {
                    'name': row['gene']
                },
                'description': row['interpretation'],
                'tier': row['tier'],
                'tumor_types': row['tumor_types'],
                'tissue_types': row['tissue_types'],
                'variants': [
                    {'name': v} for v in row['variants']
                ],
                'citations': row['citations']
            })
        return (evidence, assertions)

    def _create_json(self, evidence: List, genes: List, variants: List,
                     assertions: List):
        """Create and write composite JSON file containing genes, variants, and
        interpretations, and create individual JSON files for each assertion.

        :param List evidence: List of evidence objects
        :param List genes: List of genes
        :param List variants: List of variants
        :param List assertions: List of assertions
        """
        composite_dict = {
            'evidence': evidence,
            'genes': genes,
            'variants': variants,
            'assertions': assertions
        }

        data_dir = PROJECT_ROOT / 'data' / 'pmkb'
        with open(data_dir / 'pmkb_harvester.json', 'w+') as f:
            json.dump(composite_dict, f)

        for data in ['evidence', 'genes', 'variants', 'assertions']:
            with open(data_dir / f"{data}.json", 'w+') as f:
                json.dump(composite_dict[data], f)
