"""PMKB harvester"""
import logging
from .base import Harvester
from metakb import PROJECT_ROOT, FileDownloadException
import requests
import re
import pandas as pd
import numpy as np
import json


logger = logging.getLogger('Harvesters')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class PMKB(Harvester):
    """Harvester class for Weill Cornell PMKB"""

    def __init__(self):
        """Set up harvester object"""
        self.assertions = []

    def harvest(self) -> bool:
        """Harvest PMKB source. Retrieve and store genes, variants, and
        interpretations.

        :return: `True` if successful, `False` otherwise.
        :rtype: bool
        """
        self._data_dir = PROJECT_ROOT / 'data' / 'pmkb'
        self._data_dir.mkdir(exist_ok=True, parents=True)
        files = [f for f in self._data_dir.iterdir()
                 if f.name.startswith('PMKB_Interpretations_Complete')]
        if not files:
            self._download_csv()
            files = [f for f in self._data_dir.iterdir()
                     if f.name.startswith('PMKB_Interpretations_Complete')]
        newest_filename = sorted(files, reverse=True)[0]   # get most recent
        infile = open(newest_filename, 'r')
        df = pd.read_csv(infile, na_filter=False)
        df = df[1:]
        df.columns = ['gene', 'tumor_types', 'tissue_types', 'variants',
                      'tier', 'interpretation', 'citations']
        df['variants'] = df['variants'].apply(lambda t: t.split('|'))
        df['tumor_types'] = df['tumor_types'].apply(lambda t: t.split('|'))
        df['tissue_types'] = df['tissue_types'].apply(lambda t: t.split('|'))
        df['citations'] = df['citations'].apply(lambda t: t.split('|'))

        # build genes
        genes = list()
        genes_grouped = df[['gene', 'variants']].groupby('gene',
                                                         as_index=False)
        for (gene, grouped) in genes_grouped:
            # flatten variant values
            var_series = grouped['variants'].apply(pd.Series)\
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

        # build variants
        variants = list()
        # create duplicate entries with unique variants for each row
        v = pd.DataFrame(
            {
                col: np.repeat(df[col].values, df['variants'].str.len())
                for col in df.columns.drop('variants')
            }).assign(**{
                'variants': np.concatenate(df['variants'].values)
            })
        v['variants'].replace('', np.nan, inplace=True)
        v.dropna(subset=['variants'], inplace=True)
        v = v.groupby('variants')
        for (variant, grouped) in v:
            gene = grouped['gene'].iloc[0]
            variants.append({
                'type': 'variant',
                'name': variant,
                'gene': gene,
                'evidence': {
                    'type': 'evidence',
                    # flatten citation lists and reduce to unique cites
                    'sources': list(grouped['citations'].apply(pd.Series)
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
                    for _, row in grouped.iterrows()
                ]
            })

        # build evidence and assertions
        evidence = list()
        assertions = list()
        for _, row in df.iterrows():
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
                ]

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

        self._create_json(evidence, genes, variants, assertions)
        logger.info('PMKB Harvester was successful.')
        return True

    def _download_csv(self):
        """Download source data from PMKB server."""
        PMKB_URL = "https://pmkb.weill.cornell.edu/therapies/downloadCSV.csv"
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
        else:
            logger.error(f"PMKB source download failed with status code: {response.status_code}")  # noqa: E501
            raise FileDownloadException("PMKB source download failed")

    def _create_json(self, evidence, genes, variants, assertions):
        """Create composite JSON file containing genes, variants, and
        interpretations, and create individual JSON files for each assertion.

        :param list genes: List of genes
        :param list variants: List of variants
        :param list interpretations: List of interpretations
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

        for d in ['evidence', 'genes', 'variants', 'assertions']:
            with open(data_dir / f"{d}.json", 'w+') as f:
                json.dump(composite_dict[d], f)
