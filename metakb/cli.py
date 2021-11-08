"""
Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import click
from os import environ
import logging
from metakb.database import Graph
from metakb import APP_ROOT
from metakb.harvesters import CIViC, MOAlmanac
from metakb.schemas import SourceName
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

        if normalizer_db_url:
            for env_var_name in ['GENE_NORM_DB_URL', 'THERAPY_NORM_DB_URL',
                                 'DISEASE_NORM_DB_URL']:
                environ[env_var_name] = normalizer_db_url

        if not load_transformed:
            if initialize_normalizers or force_initialize_normalizers:
                CLI()._handle_initialize(force_initialize_normalizers)

            CLI()._harvest_sources()
            CLI()._transform_sources()

        # upload
        start = timer()
        msg = "Loading neo4j database..."
        click.echo(msg)
        logger.info(msg)
        g = Graph(uri=db_url, credentials=(db_username, db_password))
        g.clear()
        for src in sorted({v.value for v in SourceName.__members__.values()}):
            path = \
                APP_ROOT / 'data' / src / 'transform' / f'{src}_cdm.json'
            try:
                g.load_from_json(path)
            except FileNotFoundError:
                logger.fatal(f'Could not locate transformed JSON at {path}')
                raise FileNotFoundError
        g.close()
        end = timer()
        msg = f"Successfully loaded neo4j database in {(end-start):.5f} s"
        click.echo(msg)
        logger.info(msg)

    @staticmethod
    def _harvest_sources():
        logger.info("Harvesting sources...")
        # TODO: Switch to using constant
        harvester_sources = {
            'civic': CIViC,
            'moa': MOAlmanac
        }
        total_start = timer()
        for class_str, class_name in harvester_sources.items():
            harvest_start = f"Harvesting {class_str}..."
            click.echo(harvest_start)
            logger.info(harvest_start)
            start = timer()
            source = class_name()
            source_successful = source.harvest()
            end = timer()
            if not source_successful:
                logger.info(f'{class_str} harvest failed.')
                click.get_current_context().exit()
            harvest_finish = \
                f"{class_str} harvest finished in {(end-start):.5f} s"
            click.echo(harvest_finish)
            logger.info(harvest_finish)
        total_end = timer()
        msg = f"Successfully harvested all sources in " \
              f"{(total_end-total_start):.5f} s"
        click.echo(msg)
        logger.info(msg)

    @staticmethod
    def _transform_sources():
        from metakb.transform import CIViCTransform, MOATransform
        logger.info("Transforming harvested data to CDM...")
        source_indices = None
        # TODO: Switch to using constant
        transform_sources = {
            'civic': CIViCTransform,
            'moa': MOATransform
        }
        total_start = timer()
        for class_str, class_name in transform_sources.items():
            transform_start = f"Transforming {class_str}..."
            click.echo(transform_start)
            logger.info(transform_start)
            start = timer()
            source = class_name()
            source_indices = source.transform(source_indices)
            end = timer()
            transform_end = \
                f"{class_str} transform finished in {(end - start):.5f} s."
            click.echo(transform_end)
            logger.info(transform_end)
            source._create_json()
        total_end = timer()
        msg = f"Successfully transformed all sources to CDM in " \
              f"{(total_end-total_start):.5f} s"
        click.echo(msg)
        logger.info(msg)

    def _handle_initialize(self, force_initialize):
        """Handle initialization of normalizer data.
        :param bool force_initialize: call initialize routines for all
            normalizers
        """
        if force_initialize:
            init_disease = init_therapy = init_gene = True
        else:
            init_disease = self._check_normalizer(
                DiseaseDatabase(), {v.value for v in DiseaseSources}
            )

            init_therapy = self._check_normalizer(
                TherapyDatabase(),
                {TherapySourceLookup[src] for src in TherapySources}
            )

            init_gene = self._check_normalizer(
                GeneDatabase(), {'HGNC'}
            )

        for init_source, source_cli, args in [
            (init_disease, DiseaseCLI, ['--update_all',
                                        '--update_merged']),
            (init_therapy, TherapyCLI, ['--normalizer',
                                        'hemonc chemidplus rxnorm wikidata'
                                        ' ncit drugbank', '--update_merged']),
            (init_gene, GeneCLI, ['--normalizer', 'hgnc'])
        ]:
            name = str(source_cli).split()[1].split('.')[0][1:].capitalize()
            click.echo(f'\nUpdating {name} Normalizer...')
            self._update_normalizer_db(init_source, source_cli, args)
        click.echo("Normalizer initialization complete.")

    @staticmethod
    def _check_normalizer(db, sources) -> bool:
        """Check whether or not normalizer needs to be initialized.

        :param Database db: Normalizer database
        :param set sources: Set of source's to use for normalizer
        :return: `True` If normalizer needs to be initialized.
            `False` otherwise.
        """
        name = str(db).split('.')[0][1:].capitalize()
        click.echo(f'Checking {name} Normalizer...')
        for src in sources:
            response = db.metadata.get_item(
                Key={'src_name': src}
            )
            if not response.get('Item'):
                return True
        return False

    def _update_normalizer_db(self, init_source, source_cli, args) -> None:
        """Update Normalizer database.

        :param bool init_source: Whether or not to load normalizer db
        :param CLI source_cli: Normalizer CLI class containing CLI methods
            for loading and deleting source data
        :param list args: List of arguments to use in CLI
        """
        if init_source:
            try:
                source_cli.update_normalizer_db(args)
            except SystemExit as e:
                if e.code != 0:
                    raise e

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
        else:
            return param

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
