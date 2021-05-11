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
            variants = self._get_all_variants()
            interpretations = self._get_all_interpretations(variants)
            self._create_json(interpretations, variants, fn)
            return True
        except Exception as e:  # noqa: E722
            logger.error(f"PMKB Harvester was not successful: {e}")
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
            }
            coords = variant['Genomic Coordinates (GRCh37/hg19)']
            if coords:
                variant_object['coordinates'] = coords.split(', ')
            else:
                variant_object['coordinates'] = []
            variants[name] = variant_object

        variants_file.close()
        return variants

    def _get_all_interpretations(self, variants):
        """Read interpretations and build harvested Interpretation objects.
        :param dict variants: dictionary keying variant names to full data
        :return: list of Interpretation objects
        """
        interps_out = []

        pattern = 'data/pmkb/pmkb_interps_*.csv'
        interp_file_path = sorted(list(PROJECT_ROOT.glob(pattern)))[-1]
        interp_file = open(interp_file_path, 'r')
        interps_reader = csv.DictReader(interp_file)
        for interp in interps_reader:
            interp_id = interp['PMKB URL'].split('/')[-1]
            interp_gene = interp['Gene']

            descriptions = interp['Interpretations'].split('|')
            if len(descriptions) != 1:
                logger.warning(f"Interpretation ID#{interp_id} does not have "
                               f"exactly 1 description.")
                continue

            interp_out = {
                "id": interp_id,
                "gene": {
                    "name": interp_gene
                },
                "evidence_items": interp['Citations'].split('|'),
                "pmkb_evidence_tier": interp['Tier'],
                "variants": [],
                "diseases": list(set(interp['Tumor Type(s)'].split('|'))),
            }

            tissue_types = list(set(interp['Tissue Type(s)'].split('|')))
            description = descriptions[0].strip().replace('\n', ' ')
            words = description.split(' ')
            if tissue_types == ['Unknown']:
                if len(words) == 1:
                    interp_out['therapies'] = words
                    interp_out['description'] = ''
                    interp_out['tissue_types'] = []
                else:
                    interp_out['therapies'] = ['therapeutic procedure']
                    interp_out['description'] = description
                    interp_out['tissue_types'] = []  # retain unknown?
            else:
                interp_out['therapies'] = ['therapeutic procedure']
                interp_out['description'] = description
                interp_out['tissue_types'] = tissue_types

            interp_variants = set(interp['Variant(s)'].split('|'))
            for interp_variant in interp_variants:
                if not interp_variant:
                    continue  # will log below
                variant_data = variants.get(interp_variant)
                if not variant_data:
                    # variant not found in Variants data
                    logger.error(f"Could not retrieve data for variant: "
                                 f"{interp_variant}")
                    continue
                interp_out['variants'].append({
                    "name": variant_data['name'],
                    "id": variant_data['id']
                })
                origin = variant_data.get('origin')
                if origin and 'origin' not in interp_out:
                    interp_out['origin'] = origin

            valid_statement = True
            for field in ('variants', 'diseases', 'evidence_items'):
                if not interp_out[field]:
                    logger.warning(f"Interpretation ID#{interp_id} has no "
                                   f"valid {field} values.")
                    valid_statement = False
            if valid_statement:
                interps_out.append(interp_out)

        interp_file.close()
        return interps_out

    def _create_json(self, interpretations, variants, filename):
        """Export data to JSON.
        :param List interpretations: list of Interpretation objects
        :param Dict variants: Dictionary where values are Variant objects
        :param str filename: name of composite output file
        """
        variants_list = list(variants.values())

        interpretations_path = self.pmkb_dir / 'interpretations.json'
        with open(interpretations_path, 'w') as outfile:
            json.dump(interpretations, outfile)

        var_path = self.pmkb_dir / 'variants.json'
        with open(var_path, 'w') as outfile:
            json.dump(variants_list, outfile)

        composite_path = self.pmkb_dir / filename
        with open(composite_path, 'w') as outfile:
            json.dump({'interpretations': interpretations,
                       'variants': variants_list},
                      outfile)
