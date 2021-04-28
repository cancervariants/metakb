"""Harvester for PMKB."""
from .base import Harvester
from metakb import PROJECT_ROOT
import logging
import requests
from datetime import datetime
import csv
import bs4
import json

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
            gene_ids, disease_ids = self._load_ids()
            genes, variants = self._process_variants(gene_ids)
            statements = self._process_interps(gene_ids, disease_ids, variants)
            self._create_json(statements, genes, variants, fn)

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

        if not list(self.pmkb_dir.glob('pmkb_id_index_*.json')):
            self._build_id_index()

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

    def _build_id_index(self):
        """Construct index keying gene and disease names to PMKB IDs. Saves
        to `PROJECT_ROOT/data/pmkb/pmkb_id_inex_YYYYMMDD.json` where YYYYMMDD
        is the current date.
        """
        logging.info("Retrieving PMKB gene and disease IDs...")
        genes = {}
        diseases = {}

        # get gene IDs
        r = requests.get('https://pmkb.org/genes/')
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.content, features='lxml')
        else:
            logger.error(f'PMKB gene index scraping failed with HTTP status'
                         f' code {r.status_code}')
            raise requests.exceptions.RequestException
        gene_table = soup.find('table', {'id': 'genetable'}).tbody
        for row in gene_table.children:
            gene_id = int(row.attrs['data-link'].split('/')[-1])
            gene_name = row.td.text
            genes[gene_name] = gene_id

        # get disease IDs
        r = requests.get('https://pmkb.weill.cornell.edu/tumors')
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.content, features='lxml')
        else:
            logger.error(f'PMKB disease index scraping failed with HTTP status'
                         f' code {r.status_code}')
            raise requests.exceptions.RequestException
        disease_table = soup.find('table', {'id': 'tumortable'}).tbody
        for row in disease_table.children:
            disease_id = int(row.attrs['data-link'].split('/')[-1])
            disease_name = row.td.text
            diseases[disease_name] = disease_id

        today = datetime.now().strftime('%Y%m%d')
        fname = self.pmkb_dir / f'pmkb_id_index_{today}.json'
        with open(fname, 'w') as outfile:
            json.dump([genes, diseases], outfile)
        logging.info("PMKB gene and disease IDs retrieved.")

    def _load_ids(self):
        """Load disease and gene IDs from index file.
        :return: Dicts keying gene and disease names to PMKB IDs.
        """
        pattern = 'pmkb_id_index_*.json'
        path = sorted(list(self.pmkb_dir.glob(pattern)))[-1]
        with open(path, 'r') as file:
            gene_ids, disease_ids = json.load(file)
        return gene_ids, disease_ids

    def _process_variants(self, gene_ids):
        """Process PMKB variants.
        :param Dict gene_ids: Dict keying gene names to PMKB ID numbers
        :return: Dicts keying gene and variant names (string) to data objects
        """
        pattern = 'pmkb_variants_*.csv'
        variants_path = sorted(list(self.pmkb_dir.glob(pattern)))[-1]
        variants_file = open(variants_path, 'r')
        reader = csv.DictReader(variants_file)
        genes = {}
        variants = {}

        for variant in reader:
            name = variant['Description']
            if name in variants:
                logger.error(f"Multiple records for variant: {name}")
                continue
            variant_id = variant['PMKB URL'].split('/')[-1]

            gene = variant['Gene']
            gene_id = gene_ids.get(gene)
            if not gene_id:
                logger.error(f"Could not retrieve ID for gene: {gene}")
                continue
            if gene not in genes:
                genes[gene] = {
                    "id": gene_id,
                    "name": gene,
                    "variants": [{
                        "name": name,
                        "id": variant_id
                    }]
                }
            else:
                genes[gene]['variants'].append({
                    "name": name,
                    "id": variant_id
                })

            variants[name] = {
                "name": name,
                "gene": {
                    "name": gene,
                    "id": gene_id
                },
                "id": variant_id,
                "origin": variant['Germline/Somatic'],
                "variation_type": variant['Variant'],
                "dna_change": variant['DNA Change'],
                "amino_acid_change": variant['Amino Acid Change'],
                "ensembl_id": variant['Transcript ID (GRCh37/hg19)'],
                "cosmic_id": variant['COSMIC ID'],
            }

        variants_file.close()
        return genes, variants

    def _process_interps(self, gene_ids, disease_ids, variants):
        """Process interpretations.

        :return: list of Statement objects, and set of included genes and
            diseases.
        """
        statements = []

        pattern = 'data/pmkb/pmkb_interps_*.csv'
        interp_path = sorted(list(PROJECT_ROOT.glob(pattern)), reverse=True)[0]
        interp_file = open(interp_path, 'r')
        interps = csv.DictReader(interp_file)
        for interp in interps:
            interp_id = interp['PMKB URL'].split('/')[-1]

            interp_gene = interp['Gene']
            interp_gene_id = gene_ids.get(interp_gene)
            if not interp_gene_id:
                logger.error(f"Could not retrieve ID for gene: {interp_gene}")
                continue

            interp_ev = interp['Citations'].split('|')
            interp_tissue_types = interp['Tissue Type(s)'].split('|')

            count = 0
            for interp_descr in set(interp['Interpretations'].split('|')):
                for disease in set(interp['Tumor Type(s)'].split('|')):
                    if not disease:
                        continue

                    disease_id = disease_ids.get(disease)
                    if not disease_id:
                        logger.error(f"Could not retrieve ID for disease: {disease}")  # noqa: E501
                        continue

                    for variant in set(interp['Variant(s)'].split('|')):
                        if not variant:
                            continue

                        variant_data = variants.get(variant)
                        if not variant_data:
                            logger.error(f"Could not retrieve data for variant: {variant}")  # noqa: E501
                            continue

                        statements.append({
                            "id": f"{interp_id}-{count}",
                            "description": interp_descr,
                            "gene": {
                                "name": interp_gene,
                                "id": interp_gene_id,
                            },
                            "variant": variant_data,
                            "disease": {
                                "name": disease,
                                "id": disease_id,
                            },
                            "tissue_types": interp_tissue_types,
                            "evidence_items": interp_ev
                        })
                        count += 1

        interp_file.close()
        return statements

    def _create_json(self, statements, genes, variants, filename):
        statements_path = self.pmkb_dir / 'statements.json'
        with open(statements_path, 'w') as outfile:
            json.dump(statements, outfile)

        gene_path = self.pmkb_dir / 'genes.json'
        with open(gene_path, 'w') as outfile:
            json.dump(genes, outfile)

        var_path = self.pmkb_dir / 'variants.json'
        with open(var_path, 'w') as outfile:
            json.dump(variants, outfile)

        composite_path = self.pmkb_dir / filename
        with open(composite_path, 'w') as outfile:
            json.dump([statements, genes, variants], outfile)
