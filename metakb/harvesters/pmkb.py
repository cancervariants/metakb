"""Harvester for PMKB."""
from .base import Harvester
from metakb import PROJECT_ROOT
import logging
import requests
from datetime import datetime
import csv
import json
from ftplib import FTP
import gzip
import shutil
from os import remove
import pandas as pd
import re

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class PMKB(Harvester):
    """Class for harvesting from PMKB."""

    def harvest(self, fn='pmkb_harvester.json'):
        """Retrieve and store all interpretations, genes, variants, tumor
        types, and evidence in composite and individual JSON files.

        :param string fn: file name of composite JSON document
        :return: bool True if operation is successful, False otherwise
        """
        try:
            self.pmkb_dir = PROJECT_ROOT / 'data' / 'pmkb'
            self._check_files()
            variants = self._get_all_variants()
            statements = self._get_all_interpretations(variants)
            self._create_json(statements, variants, fn)

        except NotImplementedError:  # noqa: E722
            logger.info("PMKB Harvester was not successful.")
            return False

    def _check_files(self):
        """Check PMKB data directory for requisite files and call download
        methods if needed.
        """
        self.pmkb_dir.mkdir(exist_ok=True, parents=True)

        if not list(self.pmkb_dir.glob('pmkb_variants_*.csv')) and \
                not list(self.pmkb_dir.glob('pmkb_interps_*.csv')):
            self._download_data()

        if not list(self.pmkb_dir.glob('pmkb_ids_*.csv')):
            self._download_pmid_index()

    def _download_data(self):
        """Retrieve PMKB data from remote host."""
        logging.info("Downloading PMKB source data...")
        self.pmkb_dir.mkdir(exist_ok=True, parents=True)
        version = datetime.now().strftime('%Y%m%d')

        response_interps = requests.get('http://pmkb.org/therapies/download.csv')  # noqa: E501
        if response_interps.status_code == 200:
            fname = self.pmkb_dir / f'pmkb_interps_{version}.csv'
            with open(fname, 'wb') as f:
                f.write(response_interps.content)
        else:
            msg = 'PMKB interpretations CSV download failed.'
            logger.error(msg)
            raise requests.exceptions.RequestException(msg)

        response_variants = requests.get('http://pmkb.org/variants/download.csv')  # noqa: E501
        if response_variants.status_code == 200:
            fname = self.pmkb_dir / f'pmkb_variants_{version}.csv'
            with open(fname, 'wb') as f:
                f.write(response_variants.content)
        else:
            msg = 'PMKB interpretations CSV download failed.'
            logger.error(msg)
            raise requests.exceptions.RequestException(msg)
        logging.info("PMKB source data downloads complete.")

    # TODO remove unneeded columns?
    def _download_pmid_index(self):
        """Acquire PubMed IDs file from NIH."""
        logger.info('Downloading PMID data...')
        gzname = 'PMC-ids.csv.gz'
        gzpath = self.pmkb_dir / gzname
        try:
            with FTP('ftp.ncbi.nlm.nih.gov') as ftp:
                ftp.login()
                logger.debug('FTP login successful.')
                ftp.cwd('pub/pmc/')
                with open(gzpath, 'wb') as fp:
                    ftp.retrbinary(f'RETR {gzname}', fp.write)
            logger.info('Downloaded PMID source file.')
        except TimeoutError:
            logger.error('Connection to NIH FTP server timed out.')
        today = datetime.now().strftime('%Y%m%d')
        with gzip.open(gzpath, 'rb') as f_in:
            with open(self.pmkb_dir / f'pm_ids_{today}.csv', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        remove(gzpath)

        logger.info('Finished downloading PMID data')

    def _get_all_variants(self):
        """Process PMKB variants.
        :return: Dict keying variant names (string) to data objects
        """
        pattern = 'pmkb_variants_*.csv'
        variants_path = sorted(list(self.pmkb_dir.glob(pattern)))[-1]
        variants_file = open(variants_path, 'r')
        reader = csv.DictReader(variants_file)
        variants = {}

        for variant in reader:
            name = variant['Description']
            if name in variants:
                logger.error(f"Multiple records for variant: {name}")
                continue
            variant_id = variant['PMKB URL'].split('/')[-1]

            variant_object = {
                "name": name,
                "gene": {
                    "name": variant['Gene'],
                },
                "id": variant_id,
                "origin": variant['Germline/Somatic'],
                "variation_type": variant['Variant'],
                "dna_change": variant['DNA Change'],
                "amino_acid_change": variant['Amino Acid Change'],
                "ensembl_id": variant['Transcript ID (GRCh37/hg19)'],
                "cosmic_id": variant['COSMIC ID'],
                "chromosome": variant['Chromosome'],
                "arm_cytoband": variant['Arm/Cytoband'],
                "partner_gene": variant['Partner Gene'],
                "codons": variant['Codons'],
                "exons": variant['Exons'],
                "coordinates": variant['Genomic Coordinates (GRCh37/hg19)'],
            }

            variants[name] = variant_object

        variants_file.close()
        return variants

    def _get_all_interpretations(self, variants):
        """Process interpretations.
        :param dict variants: dictionary keying variant names to full data
        :return: list of Statement objects
        """
        statements = []
        self.pmids = pd.read_csv(list(self.pmkb_dir.glob('pm_ids_*.csv'))[-1])

        pattern = 'data/pmkb/pmkb_interps_*.csv'
        interp_path = sorted(list(PROJECT_ROOT.glob(pattern)))[-1]
        interp_file = open(interp_path, 'r')
        interps = csv.DictReader(interp_file)
        for interp in interps:
            interp_id = interp['PMKB URL'].split('/')[-1]

            interp_gene = interp['Gene']

            interp_ev = interp['Citations'].split('|')

            interp_diseases = set(interp['Tumor Type(s)'].split('|'))
            interp_variants = set(interp['Variant(s)'].split('|'))
            interp_tissues = set(interp['Tissue Type(s)'].split('|'))
            if len(interp_diseases) > 1 or len(interp_variants) > 1 or \
                    len(interp_tissues) > 1:
                # skip multiple diseases/variants/tissues for this pass
                continue

            variant = interp_variants.pop()
            if not variant:
                continue

            variant_data = variants.get(variant)
            if not variant_data:
                logger.error(f"Could not retrieve data for variant: {variant}")
                continue

            for cite in interp['Citations'].split('|'):
                self._get_pmid(cite)

            statements.append({
                "id": interp_id,
                "description": interp['Interpretations'],
                "gene": {
                    "name": interp_gene,
                },
                "variant": {
                    "name": variant_data['name'],
                    "id": variant_data['id'],
                },
                "disease": {
                    "name": interp_diseases.pop(),
                    "tissue_type": interp_tissues.pop(),
                },
                "evidence_items": interp_ev
            })

        interp_file.close()
        return statements

    def _get_pmid(self, cite):
        """Get PubMed ID from citation.
        :param str cite: free text citation
        :return: PMID as str if lookup is successful, empty string otherwise
        """
        pattern = re.compile('(.+\.) (.+\.) ([A-Za-z ]+) ([0-9]+);([0-9]+)\(([0-9]+)\):([0-9]+)')  # noqa: E501 W605
        match = re.match(pattern, cite)
        if not match:
            return ""
        groups = match.groups()
        if len(groups) < 7:
            return ""
        _, _, title, year, vol, issue, pg = groups
        row = self.pmids[
            (self.pmids['Journal Title'] == title) &  # noqa: W504
            (self.pmids['Year'] == year) &  # noqa: W504
            (self.pmids['Volume'] == vol) &  # noqa: W504
            (self.pmids['Issue'] == issue) &  # noqa: W504
            (self.pmids['Page'] == pg)
        ]
        if len(row) == 1:
            return str(int(row['PMID'].iloc[0]))

    def _create_json(self, statements, variants, filename):
        """Export data to JSON.
        :param List statements: list of Statement objects
        :param Dict variants: Dictionary where values are Variant objects
        :param str filename: name of composite output file
        """
        variants_list = [v for k, v in variants.items()]

        statements_path = self.pmkb_dir / 'statements.json'
        with open(statements_path, 'w') as outfile:
            json.dump(statements, outfile)

        var_path = self.pmkb_dir / 'variants.json'
        with open(var_path, 'w') as outfile:
            json.dump(variants_list, outfile)

        composite_path = self.pmkb_dir / filename
        with open(composite_path, 'w') as outfile:
            json.dump([statements, variants_list], outfile)
