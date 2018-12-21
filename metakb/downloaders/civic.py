"""Download all data from civic.

A downloader simply retrieves data from a source and writes it to a file for downstream processing
"""

import os

from metakb.utils.requests import Client
from metakb.utils.ioutils import JSONEmitter
from metakb.utils.cli import default_argument_parser

DEFAULT_OUTPUT_DIR = 'downloads/civic'


def fetch(gene_count):
    """Retrieve all gene data for `gene_count` genes."""
    requests = Client('civic')
    r = requests.get('https://civic.genome.wustl.edu/api/genes?count={}'.format(gene_count))
    for record in r.json()['records']:
        variants = record['variants']
        gene = record['name']
        variants_details = []
        for variant in variants:
            r = requests.get('https://civic.genome.wustl.edu/api/variants/{}'.format(variant['id']))
            variants_details.append(r.json())
        gene_data = {'gene': gene, 'civic': {'variants': variants_details}}
        yield gene_data


def download(path='source/civic.json.gz', gene_count=9999999, compresslevel=9):
    """Download data from civic, write to a file."""
    with JSONEmitter(path, compresslevel=compresslevel) as emitter:
        for gene_data in fetch(gene_count):
            emitter.write(gene_data)


if __name__ == "__main__":
    parser = default_argument_parser(
        output_dir=DEFAULT_OUTPUT_DIR,
        description='Retrieves all genes from civic and writes to file.'
    )
    args = parser.parse_args()
    path = os.path.join(args.output_dir, 'civic.json.gz')
    download(path=path)
