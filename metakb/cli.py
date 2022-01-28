"""
Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
from timeit import default_timer as timer
from os import environ
import logging
from typing import Optional
from pathlib import Path

import click
from disease.database import Database as DiseaseDatabase
from disease.schemas import SourceName as DiseaseSources
from disease.cli import CLI as DiseaseCLI
from therapy.database import Database as TherapyDatabase
from therapy.schemas import SourceName as TherapySources
from therapy.cli import CLI as TherapyCLI
from gene.database import Database as GeneDatabase
from gene.schemas import SourceName as GeneSources
from gene.cli import CLI as GeneCLI

from metakb import APP_ROOT
from metakb.database import Graph
from metakb.schemas import SourceName
from metakb.harvesters import Harvester, CIViCHarvester, MOAHarvester
from metakb.transform import Transform, CIViCTransform, MOATransform


logger = logging.getLogger('metakb.cli')
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
        '--load_normalizers_db',
        '-i',
        is_flag=True,
        default=False,
        help='Check normalizers database and load data if necessary.'
    )
    @click.option(
        '--force_load_normalizers_db',
        '-f',
        is_flag=True,
        default=False,
        help=('Load all normalizers data into database. Overrides '
              '--load_normalizers_db if both are selected.')
    )
    @click.option(
        '--normalizers_db_url',
        default='http://localhost:8000',
        help=('URL endpoint of normalizers DynamoDB database. Set to '
              '`http://localhost:8000` by default.')
    )
    @click.option(
        "--load_latest_cdms",
        "-l",
        is_flag=True,
        default=False,
        help=("Clear MetaKB database and load most recent available source "
              "CDM files. Does not run harvest and transform methods to "
              "generate new CDM files.")
    )
    @click.option(
        "--load_target_cdm",
        "-t",
        type=click.Path(exists=True, dir_okay=False, readable=True,
                        path_type=Path),
        required=False,
        help=("Load transformed CDM file at specified path. Overrides "
              "--load_normalizers_db, --force_load_normalizers_db, "
              "and --load_latest_cdms.")
    )
    def update_metakb_db(db_url: str, db_username: str, db_password: str,
                         load_normalizers_db: bool,
                         force_load_normalizers_db: bool,
                         normalizers_db_url: str,
                         load_latest_cdms: bool,
                         load_target_cdm: Optional[Path]):
        """Execute data harvest and transformation from resources and upload
        to graph datastore.
        """
        db_url = CLI()._check_db_param(db_url, 'URL')
        db_username = CLI()._check_db_param(db_username, 'username')
        db_password = CLI()._check_db_param(db_password, 'password')

        if normalizers_db_url:
            for env_var_name in ['GENE_NORM_DB_URL', 'THERAPY_NORM_DB_URL',
                                 'DISEASE_NORM_DB_URL']:
                environ[env_var_name] = normalizers_db_url

        if not (load_latest_cdms or load_target_cdm):
            if load_normalizers_db or force_load_normalizers_db:
                CLI()._load_normalizers_db(force_load_normalizers_db)

            CLI()._harvest_sources()
            CLI()._transform_sources()

        # Load neo4j database
        start = timer()
        msg = "Loading neo4j database..."
        click.echo(msg)
        logger.info(msg)
        g = Graph(uri=db_url, credentials=(db_username, db_password))
        if load_target_cdm:
            g.load_from_json(load_target_cdm)
        else:
            g.clear()
            for src in sorted({v.value for v
                               in SourceName.__members__.values()}):
                pattern = f"{src}_cdm_*.json"
                globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)
                try:
                    path = sorted(globbed)[-1]
                except IndexError:
                    raise FileNotFoundError(f"No valid transform file found "
                                            f"for {src}")
                g.load_from_json(path)
        g.close()
        end = timer()
        msg = f"Successfully loaded neo4j database in {(end-start):.5f} s"
        click.echo(f"{msg}\n")
        logger.info(msg)

    @staticmethod
    def _harvest_sources() -> None:
        """Run harvesting procedure for all sources."""
        logger.info("Harvesting sources...")
        # TODO: Switch to using constant
        harvester_sources = {
            'civic': CIViCHarvester,
            'moa': MOAHarvester
        }
        total_start = timer()
        for source_str, source_class in harvester_sources.items():
            harvest_start = f"Harvesting {source_str}..."
            click.echo(harvest_start)
            logger.info(harvest_start)
            start = timer()
            source: Harvester = source_class()
            source_successful = source.harvest()
            end = timer()
            if not source_successful:
                logger.info(f'{source_str} harvest failed.')
                click.get_current_context().exit()
            harvest_finish = \
                f"{source_str} harvest finished in {(end - start):.5f} s"
            click.echo(harvest_finish)
            logger.info(harvest_finish)
        total_end = timer()
        msg = f"Successfully harvested all sources in " \
              f"{(total_end - total_start):.5f} s"
        click.echo(f"{msg}\n")
        logger.info(msg)

    @staticmethod
    def _transform_sources() -> None:
        """Run transformation procedure for all sources."""
        logger.info("Transforming harvested data to CDM...")
        # TODO: Switch to using constant
        transform_sources = {
            'civic': CIViCTransform,
            'moa': MOATransform
        }
        total_start = timer()
        for src_str, src_name in transform_sources.items():
            transform_start = f"Transforming {src_str}..."
            click.echo(transform_start)
            logger.info(transform_start)
            start = timer()
            source: Transform = src_name()
            source.transform()
            end = timer()
            transform_end = \
                f"{src_str} transform finished in {(end - start):.5f} s."
            click.echo(transform_end)
            logger.info(transform_end)
            source.create_json()
        total_end = timer()
        msg = f"Successfully transformed all sources to CDM in " \
              f"{(total_end-total_start):.5f} s"
        click.echo(f"{msg}\n")
        logger.info(msg)

    def _load_normalizers_db(self, load_normalizer_db):
        """Load normalizer database source data.

        :param bool load_normalizer_db: Load normalizer database for each
            normalizer
        """
        if load_normalizer_db:
            load_disease = load_therapy = load_gene = True
        else:
            load_disease = self._check_normalizer(
                DiseaseDatabase(), {src.value for src in DiseaseSources})
            load_therapy = self._check_normalizer(
                TherapyDatabase(), {src for src in TherapySources})
            load_gene = self._check_normalizer(
                GeneDatabase(), {src.value for src in GeneSources})

        for load_source, normalizer_cli in [
            (load_disease, DiseaseCLI), (load_therapy, TherapyCLI),
            (load_gene, GeneCLI)
        ]:
            name = \
                str(normalizer_cli).split()[1].split('.')[0][1:].capitalize()
            self._update_normalizer_db(name, load_source, normalizer_cli)
        click.echo("Normalizers database loaded.\n")

    @staticmethod
    def _check_normalizer(db, sources) -> bool:
        """Check whether or not normalizer data needs to be loaded.

        :param Database db: Normalizer database
        :param set sources: Sources that are needed in the normalizer db
        :return: `True` If normalizer needs to be loaded. `False` otherwise.
        """
        for src in sources:
            response = db.metadata.get_item(
                Key={'src_name': src}
            )
            if not response.get('Item'):
                return True
        return False

    @staticmethod
    def _update_normalizer_db(name, load_normalizer, source_cli) -> None:
        """Update Normalizer database.

        :param str name: Name of the normalizer
        :param bool load_normalizer: Whether or not to load normalizer db
        :param CLI source_cli: Normalizer CLI class for loading and
            deleting source data
        """
        if load_normalizer:
            try:
                click.echo(f'\nLoading {name} Normalizer data...')
                source_cli.update_normalizer_db(
                    ['--update_all', '--update_merged'])
                click.echo(f'Successfully Loaded {name} Normalizer data.\n')
            except SystemExit as e:
                if e.code != 0:
                    raise e
        else:
            click.echo(f'{name} Normalizer is already loaded.\n')

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
