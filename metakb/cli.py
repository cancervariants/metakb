"""
Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import click
from os import environ
from metakb.database import Graph
from metakb.harvesters import CIViC
from metakb.transform import CIViCTransform
import logging
from metakb import PROJECT_ROOT
from disease.database import Database as DiseaseDatabase
from disease.schemas import SourceName as DiseaseSources
from therapy.database import Database as TherapyDatabase
from therapy import ACCEPTED_SOURCES as TherapySources
from therapy import SOURCES as TherapySourceLookup
from disease.cli import CLI as DiseaseCLI
from therapy.cli import CLI as TherapyCLI
from gene.cli import CLI as GeneCLI
from gene.database import Database as GeneDatabase


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CLI:
    """Update database."""

    @click.command()
    @click.option(
        '--db_url',
        help=('URL endpoint for the application database. Can also be '
              'provided via environment variable METAKB_DB_URL.')
    )
    @click.option(
        '--db_username',
        help='Username to provide to application database.'
    )
    @click.option(
        '--db_password',
        help='Password to provide to application database.'
    )
    @click.option(
        '--check_normalizers',
        is_flag=True,
        help=('Check normalizer data repositories and exit if not '
              'initialized.')
    )
    @click.option(
        '--initialize',
        is_flag=True,
        help=('Initialize all normalizer data repositories.')
    )
    @click.option(
        '--normalizer_db_url',
        help=('URL endpoint of normalizer database.')
    )
    def update_metakb_db(db_url, db_username, db_password,
                         check_normalizers=False, initialize=False,
                         normalizer_db_url=''):
        """Receive parsed args and initiate update if valid."""
        uninitialized_srcs = []
        if check_normalizers:
            click.echo("Checking Disease Normalizer...")
            disease_db = DiseaseDatabase(db_url=normalizer_db_url)
            for src in [v.value for v in DiseaseSources]:
                response = disease_db.metadata.get_item(
                    Key={'src_name': src}
                )
                if not response.get('Item'):
                    uninitialized_srcs.append(f"Disease: {src}")
            click.echo("Disease Normalizer checks complete.")
            click.echo("Checking Therapy Normalizer...")
            therapy_db = TherapyDatabase(db_url=normalizer_db_url)
            for src in {TherapySourceLookup[src] for src in TherapySources}:
                response = therapy_db.metadata.get_item(
                    Key={'src_name': src}
                )
                if not response.get('Item'):
                    uninitialized_srcs.append(f"Therapy: {src}")
            click.echo("Therapy Normalizer checks complete.")
            click.echo("Checking Gene Normalizer...")
            gene_db = GeneDatabase(db_url=normalizer_db_url)
            response = gene_db.metadata.get_item(
                Key={'src_name': 'HGNC'}
            )
            if not response.get('Item'):
                uninitialized_srcs.append("Gene: HGNC")
            click.echo("Gene Normalizer checks complete.")
            if uninitialized_srcs:
                print("\nNormalizater initialization incomplete:")
                print("---------------------------------------")
                for src in uninitialized_srcs:
                    print(src)
            else:
                print("\nNormalizers fully initialized.")
            click.get_current_context().exit()

        if initialize:
            TherapyCLI.update_normalizer_db(['--db_url', normalizer_db_url,
                                             '--normalizer',
                                             'chemidplus rxnorm wikidata ncit',
                                             '--update_merged'
                                             ])
            DiseaseCLI.update_normalizer_db(['--db_url', normalizer_db_url,
                                             '--update_all',
                                             '--update_merged'])
            GeneCLI.update_normalizer_db(['--db_url', normalizer_db_url,
                                          '--normalizer', 'hgnc'])

        if not db_url:
            if 'METAKB_DB_URL' in environ.keys():
                db_url = environ['METAKB_DB_URL']
            else:
                CLI()._help_msg('Must provide database URL.')
        if not db_username:
            if 'METAKB_DB_USERNAME' in environ.keys():
                db_username = environ['METAKB_DB_USERNAME']
            else:
                CLI()._help_msg('Must provide username for DB.')
        if not db_password:
            if 'METAKB_DB_PASSWORD' in environ.keys():
                db_password = environ['METAKB_DB_PASSWORD']
            else:
                CLI()._help_msg('Must provide password for DB.')

        # harvest
        click.echo("Harvesting resource data...")
        civic_harvester = CIViC()
        harvest_successful = civic_harvester.harvest()
        if not harvest_successful:
            click.get_current_context().exit()
        else:
            click.echo("Harvest successful.")

        # transform
        click.echo("Transforming harvested data...")
        civic_transform = CIViCTransform()
        civic_transform._create_json(civic_transform.transform())
        click.echo("Transform successful.")

        # upload
        click.echo("Uploading to DB...")
        g = Graph(uri=db_url, credentials=(db_username, db_password))
        g.clear()
        g.load_from_json(PROJECT_ROOT / 'data' / 'civic' / 'transform' / 'civic_cdm.json')  # noqa: E501
        g.close()
        click.echo("DB upload successful.")

    def _help_msg(self, msg: str = ""):
        """Handle invalid user input.
        :param str msg: Error message to display to user.
        """
        ctx = click.get_current_context()
        click.echo(msg)
        click.echo(ctx.get_help())
        ctx.exit()


if __name__ == '__main__':
    CLI().update_metakb_db()
