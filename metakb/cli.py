"""
Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import click
from os import environ
from metakb.database import Graph
from metakb.harvesters import CIViC, MOAlmanac
from metakb.transform import CIViCTransform, MOATransform
import logging
from metakb import PROJECT_ROOT
from disease.database import Database as DiseaseDatabase
from disease.schemas import SourceName as DiseaseSources
from disease.cli import CLI as DiseaseCLI
from therapy.database import Database as TherapyDatabase
from therapy import ACCEPTED_SOURCES as TherapySources
from therapy import SOURCES as TherapySourceLookup
from therapy.cli import CLI as TherapyCLI
from gene.database import Database as GeneDatabase
from gene.cli import CLI as GeneCLI


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CLI:
    """Update database."""

    @click.command()
    @click.option(
        '--db_url',
        help=('URL endpoint for the application Neo4j database. Can also be '
              'provided via environment variable METAKB_DB_URL.')
    )
    @click.option(
        '--db_username',
        help=('Username to provide to application database. Can also be '
              'provided via environment variable METAKB_DB_USERNAME.')
    )
    @click.option(
        '--db_password',
        help=('Password to provide to application database. Can also be '
              'provided via environment variable METAKB_DB_PASSWORD.')
    )
    @click.option(
        '--initialize_normalizers',
        '-i',
        is_flag=True,
        default=False,
        help='Check normalizer databases and initialize if necessary.'
    )
    @click.option(
        '--force_initialize_normalizers',
        '-f',
        is_flag=True,
        default=False,
        help=('Initialize all normalizer data repositories. Overrides '
              '--initialize_normalizers if both are selected.')
    )
    @click.option(
        '--normalizer_db_url',
        default='',
        help='URL endpoint of normalizer DynamoDB database.'
    )
    @click.option(
        '--load_transformed',
        '-l',
        is_flag=True,
        default=False,
        help=('Load from existing resource transform documents instead of'
              ' initiating new harvest and transformation procedures.')
    )
    def update_metakb_db(db_url, db_username, db_password,
                         initialize_normalizers,
                         force_initialize_normalizers,
                         normalizer_db_url,
                         load_transformed):
        """Execute data harvest and transformation from resources and upload
        to graph datastore.
        """
        db_url = CLI()._check_db_param(db_url, 'URL')
        db_username = CLI()._check_db_param(db_username, 'username')
        db_password = CLI()._check_db_param(db_password, 'password')

        if not load_transformed:
            if initialize_normalizers or force_initialize_normalizers:
                CLI()._handle_initialize(initialize_normalizers,
                                         force_initialize_normalizers,
                                         normalizer_db_url)

            # harvest
            logger.info("Harvesting resource data...")
            civic_harvester = CIViC()
            civic_harvest_successful = civic_harvester.harvest()
            if not civic_harvest_successful:
                logger.info("CIViC harvest failed.")
                click.get_current_context().exit()
            moa_harvester = MOAlmanac()
            moa_harvest_successful = moa_harvester.harvest()
            if not moa_harvest_successful:
                logger.info("MOAlmanac harvest failed.")
                click.get_current_context().exit()

            # transform
            logger.info("Transforming harvested data...")
            civic_transform = CIViCTransform()
            civic_items, civic_indices = civic_transform.transform()
            civic_transform._create_json(civic_items)
            moa_transform = MOATransform()
            moa_items, _ = moa_transform.transform(civic_indices)
            moa_transform._create_json(moa_items)
            logger.info("Transform successful.")

        # upload
        logger.info("Uploading to DB...")
        g = Graph(uri=db_url, credentials=(db_username, db_password))
        g.clear()
        g.load_from_json(PROJECT_ROOT / 'data' / 'civic' / 'transform' / 'civic_cdm.json')  # noqa: E501
        # g.load_from_json(PROJECT_ROOT / 'data' / 'moa' / 'transform' / 'moa_cdm.json')  # noqa: E501
        g.close()
        logger.info("DB upload successful.")

    def _handle_initialize(self, initialize, force_initialize, db_url):
        """Handle initialization of normalizer data.
        :param bool initialize: if true, check whether normalizer data is
            initialized and call initialization routines if not
        :param bool force_initialize: call initialize routines for all
            normalizers
        :param str db_url: URL endpoint for normalizer DynamoDB database
        """
        if force_initialize:
            init_disease = init_therapy = init_gene = True
        elif initialize:
            init_disease = init_therapy = init_gene = False

            click.echo("Checking Disease Normalizer...")
            disease_db = DiseaseDatabase(db_url=db_url)
            for src in [v.value for v in DiseaseSources]:
                response = disease_db.metadata.get_item(
                    Key={'src_name': src}
                )
                if not response.get('Item'):
                    init_disease = True
                    break

            click.echo("Checking Therapy Normalizer...")
            therapy_db = TherapyDatabase(db_url=db_url)
            for src in {TherapySourceLookup[src] for src in TherapySources}:
                response = therapy_db.metadata.get_item(
                    Key={'src_name': src}
                )
                if not response.get('Item'):
                    init_therapy = True
                    break

            click.echo("Checking Gene Normalizer...")
            gene_db = GeneDatabase(db_url=db_url)
            response = gene_db.metadata.get_item(
                Key={'src_name': 'HGNC'}
            )
            if not response.get('Item'):
                init_gene = True

        if init_therapy:
            click.echo("Updating Therapy Normalizer...")
            TherapyCLI.update_normalizer_db(['--db_url', db_url,
                                             '--normalizer',
                                             'chemidplus rxnorm wikidata ncit',
                                             '--update_merged'])
        if init_disease:
            click.echo("Updating Disease Normalizer...")
            DiseaseCLI.update_normalizer_db(['--db_url', db_url,
                                             '--update_all',
                                             '--update_merged'])
        if init_gene:
            click.echo("Updating Gene Normalizer...")
            GeneCLI.update_normalizer_db(['--db_url', db_url,
                                          '--normalizer', 'hgnc'])
        print("Normalizer initialization complete.")

    def _check_db_param(self, param: str, name: str) -> str:
        """Check for MetaKB database parameter.
        :param str param: value of parameter as received from command line
        :param str name: name of parameter
        :return: parameter value, or exit with error message if unavailable
        """
        if not param:
            env_var_name = f'METAKB_DB_{name.upper()}'
            if env_var_name in environ.keys():
                return environ[env_var_name]
            else:
                CLI()._help_msg(f'Must provide {name} for DB.')

    def _help_msg(self, msg: str = ""):
        """Handle invalid user input.
        :param str msg: Error message to display to user.
        """
        ctx = click.get_current_context()
        logger.fatal(f'Error: {msg}')
        click.echo(ctx.get_help())
        ctx.exit()


if __name__ == '__main__':
    CLI().update_metakb_db()
