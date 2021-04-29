"""Harvester for PMKB."""
from .base import Harvester
from metakb import PROJECT_ROOT
import logging
import requests
from datetime import datetime
import csv
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
            variants = self._process_variants()
            statements = self._process_interps(variants)
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

    def _process_variants(self):
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

    def _process_interps(self, variants):
        """Process interpretations.

        :return: list of Statement objects
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

            interp_ev = interp['Citations'].split('|')

            interp_diseases = set(interp['Tumor Type(s)'].split('|'))
            interp_variants = set(interp['Variant(s)'].split('|'))
            if len(interp_diseases) > 1 or len(interp_variants) > 1:
                continue  # skip multiple diseases/variants for this pass

            variant = interp_variants.pop()
            if not variant:
                continue

            variant_data = variants.get(variant)
            if not variant_data:
                logger.error(f"Could not retrieve data for variant: {variant}")
                continue

            statements.append({
                "id": interp_id,
                "description": interp['Interpretations'],
                "gene": {
                    "name": interp_gene,
                },
                "variant": variant_data,
                "disease": {
                    "name": interp_diseases.pop(),
                    "tissue_types": set(interp['Tissue Type(s)'].split('|'))
                },
                "evidence_items": interp_ev
            })

        interp_file.close()
        return statements

    def _create_json(self, statements, variants, filename):
        statements_path = self.pmkb_dir / 'statements.json'
        with open(statements_path, 'w') as outfile:
            json.dump(statements, outfile)

        var_path = self.pmkb_dir / 'variants.json'
        with open(var_path, 'w') as outfile:
            json.dump(variants, outfile)

        composite_path = self.pmkb_dir / filename
        with open(composite_path, 'w') as outfile:
            json.dump([statements, variants], outfile)
