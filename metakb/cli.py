"""
Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import click
from os import environ
import logging
from metakb.database import Graph
from metakb import PROJECT_ROOT
from metakb.harvesters import CIViC, MOAlmanac, PMKB
from metakb.transform import CIViCTransform, MOATransform, PMKBTransform
from disease.database import Database as DiseaseDatabase
from disease.schemas import SourceName as DiseaseSources
from disease.cli import CLI as DiseaseCLI
from therapy.database import Database as TherapyDatabase
from therapy import ACCEPTED_SOURCES as TherapySources
from therapy import SOURCES as TherapySourceLookup
from therapy.cli import CLI as TherapyCLI
from gene.database import Database as GeneDatabase
from gene.cli import CLI as GeneCLI
from timeit import default_timer as timer


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CLI:
    """Update database."""

    @staticmethod
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
        default='http://localhost:8000',
        help=('URL endpoint of normalizer DynamoDB database. Set to '
              '`http://localhost:8000` by default.')
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

            CLI()._harvest_sources()
            CLI()._transform_sources()

        # upload
        start = timer()
        logger.info("Uploading to DB...")
        g = Graph(uri=db_url, credentials=(db_username, db_password))
        g.clear()
        civic_path = PROJECT_ROOT / 'data' / 'civic' / 'transform' / 'civic_cdm.json'  # noqa: E501
        moa_path = PROJECT_ROOT / 'data' / 'moa' / 'transform' / 'moa_cdm.json'
        pmkb_path = PROJECT_ROOT / 'data' / 'pmkb' / 'transform' / 'pmkb_cdm.json'  # noqa: E501
        for path in (civic_path, moa_path, pmkb_path):
            try:
                g.load_from_json(path)
            except FileNotFoundError:
                logger.fatal(f'Could not locate transformed JSON at {path}')
                raise FileNotFoundError
        g.close()
        end = timer()
        click.echo(f"DB loaded in {(end-start):.5f} s.")
        logger.info("DB upload successful.")

    @staticmethod
    def _harvest_sources():
        logger.info("Harvesting resource data...")
        # TODO: Switch to using constant
        harvester_sources = {
            'civic': CIViC,
            'moa': MOAlmanac,
            'pmkb': PMKB
        }
        for class_str, class_name in harvester_sources.items():
            click.echo(f"Harvesting {class_str}...")
            start = timer()
            source = class_name()
            source_successful = source.harvest()
            end = timer()
            if not source_successful:
                logger.info(f'{class_str} harvest failed.')
                click.get_current_context().exit()
            click.echo(f"{class_str} harvest finished in {(end-start):.5f} s.")

    @staticmethod
    def _transform_sources():
        logger.info("Transforming harvested data...")
        source_indices = None
        # TODO: Switch to using constant
        transform_sources = {
            'civic': CIViCTransform,
            'moa': MOATransform,
            'pmkb': PMKBTransform
        }
        for class_str, class_name in transform_sources.items():
            click.echo(f"Transforming {class_str}...")
            start = timer()
            source = class_name()
            source_indices = source.transform(source_indices)
            end = timer()
            click.echo(
                f"{class_str} transform finished in {(end - start):.5f} s.")
            source._create_json()

    @staticmethod
    def _handle_initialize(initialize, force_initialize, db_url):
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
            args = ['--db_url', db_url, '--normalizer',
                    'chemidplus rxnorm wikidata ncit', '--update_merged']
            try:
                TherapyCLI.update_normalizer_db(args)
            except SystemExit as e:
                if e.code != 0:
                    raise e
        if init_disease:
            click.echo("Updating Disease Normalizer...")
            args = ['--db_url', db_url, '--update_all', '--update_merged']
            try:
                DiseaseCLI.update_normalizer_db(args)
            except SystemExit as e:
                if e.code != 0:
                    raise e
        if init_gene:
            click.echo("Updating Gene Normalizer...")
            args = ['--db_url', db_url, '--normalizer', 'hgnc']
            try:
                GeneCLI.update_normalizer_db(args)
            except SystemExit as e:
                if e.code != 0:
                    raise e
        click.echo("Normalizer initialization complete.")

    @staticmethod
    def _check_db_param(param: str, name: str) -> str:
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
                # Default is local
                if name == 'URL':
                    return "bolt://localhost:7687"
                elif name == 'username':
                    return 'neo4j'
                else:
                    return 'admin'

    @staticmethod
    def _help_msg(msg: str = ""):
        """Handle invalid user input.
        :param str msg: Error message to display to user.
        """
        ctx = click.get_current_context()
        logger.fatal(f'Error: {msg}')
        click.echo(ctx.get_help())
        ctx.exit()


if __name__ == '__main__':
    CLI().update_metakb_db()
