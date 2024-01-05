"""Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
from timeit import default_timer as timer
from os import environ
import logging
from typing import Optional
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

import asyncclick as click
from disease.schemas import SourceName as DiseaseSourceName
from disease.cli import _update_sources as update_disease_sources
from disease.database import create_db as create_disease_db
from therapy.schemas import SourceName as TherapySourceName
from therapy.cli import _update_normalizer as update_therapy_sources
from therapy.database import create_db as create_therapy_db
from gene.schemas import SourceName as GeneSourceName
from gene.cli import _update_normalizer as update_gene_sources
from gene.database import create_db as create_gene_db
import boto3
from boto3.exceptions import ResourceLoadException
from botocore.config import Config

from metakb import APP_ROOT
from metakb.database import Graph
from metakb.schemas.app import SourceName
from metakb.harvesters import CivicHarvester, MoaHarvester
from metakb.transform import CivicTransform, MoaTransform


logger = logging.getLogger(__name__)


def echo_info(msg: str) -> None:
    """Log (as INFO) and echo given message.

    :param msg: message to emit
    """
    click.echo(msg)
    logger.info(msg)


@click.command()
@click.option(
    '--db_url',
    help=('URL endpoint for the application Neo4j database. Can also be provided via '
          'environment variable METAKB_DB_URL.')
)
@click.option(
    '--db_username',
    help=('Username to provide to application database. Can also be provided via '
          'environment variable METAKB_DB_USERNAME.')
)
@click.option(
    '--db_password',
    help=('Password to provide to application database. Can also be provided via '
          'environment variable METAKB_DB_PASSWORD.')
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
    help=('Load all normalizers data into database. Overrides --load_normalizers_db if '
          'both are selected.')
)
@click.option(
    '--normalizers_db_url',
    default='http://localhost:8000',
    help=('URL endpoint of normalizers DynamoDB database. Set to '
          '`http://localhost:8000` by default.')
)
@click.option(
    "--normalizers_use_existing",
    is_flag=True,
    default=False,
    help=("If loading normalizers database, use the most recent local source data "
          "instead of fetching latest version")
)
@click.option(
    "--load_latest_cdms",
    "-l",
    is_flag=True,
    default=False,
    help=("Clear MetaKB database and load most recent available source CDM files. Does "
          "not run harvest and transform methods to generate new CDM files. Exclusive "
          "with --load_target_cdm and --load_latest_s3_cdms.")
)
@click.option(
    "--load_target_cdm",
    "-t",
    type=click.Path(exists=True, dir_okay=False, readable=True,
                    path_type=Path),
    required=False,
    help=("Load transformed CDM file at specified path. Exclusive with "
          "--load_latest_cdms and --load_latest_s3_cdms.")
)
@click.option(
    "--load_latest_s3_cdms",
    "-s",
    is_flag=True,
    default=False,
    required=False,
    help=("Clear MetaKB database, retrieve most recent data available from VICC S3 "
          "bucket, and load the database with retrieved data. Exclusive with "
          "--load_latest_cdms and load_target_cdm.")
)
@click.option(
    "--update_cached",
    "-u",
    is_flag=True,
    default=False,
    required=False,
    help=("`True` if civicpy cache should be updated. Note this will take several"
          "minutes. `False` if local cache should be used")
)
async def update_metakb_db(
    db_url: str, db_username: str, db_password: str,
    load_normalizers_db: bool, force_load_normalizers_db: bool,
    normalizers_db_url: str, normalizers_use_existing: bool, load_latest_cdms: bool,
    load_target_cdm: Optional[Path], load_latest_s3_cdms: bool,
    update_cached: bool,
) -> None:
    """Execute data harvest and transformation from resources and upload
    to graph datastore.
    """
    if sum([load_latest_cdms, bool(load_target_cdm), load_latest_s3_cdms]) > 1:
        _help_msg(
            "Error: Can only use one of `--load_latest_cdms`, `--load_target_cdm`, "
            "`--load_latest_s3_cdms`."
        )

    db_url = _check_db_param(db_url, 'URL')
    db_username = _check_db_param(db_username, 'username')
    db_password = _check_db_param(db_password, 'password')

    if normalizers_db_url:
        for env_var_name in ['GENE_NORM_DB_URL', 'THERAPY_NORM_DB_URL',
                             'DISEASE_NORM_DB_URL']:
            environ[env_var_name] = normalizers_db_url

    if not any([load_latest_cdms, load_target_cdm, load_latest_s3_cdms]):
        if load_normalizers_db or force_load_normalizers_db:
            _load_normalizers_db(force_load_normalizers_db, normalizers_use_existing)

        _harvest_sources(update_cached)
        await _transform_sources()

    # Load neo4j database
    start = timer()
    echo_info("Loading neo4j database...")

    g = Graph(uri=db_url, credentials=(db_username, db_password))
    if load_target_cdm:
        g.load_from_json(load_target_cdm)
    else:
        version = None
        if load_latest_s3_cdms:
            version = _retrieve_s3_cdms()
        g.clear()
        for src in sorted({v.value for v in SourceName.__members__.values()}):
            if version is not None:
                pattern = f"{src}_cdm_{version}.json"
            else:
                pattern = f"{src}_cdm_*.json"
            globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)
            try:
                path = sorted(globbed)[-1]
            except IndexError:
                raise FileNotFoundError(f"No valid transform file found "
                                        f"matching pattern: {pattern}")
            g.load_from_json(path)
    g.close()
    end = timer()
    echo_info(
        f"Successfully loaded neo4j database in {(end-start):.5f} s\n"
    )


s3_cdm_pattern = re.compile(r"cdm/20[23]\d[01]\d[0123]\d/(.*)_cdm_(.*).json.zip")


def _retrieve_s3_cdms() -> str:
    """Retrieve most recent CDM files from VICC S3 bucket. Expects to find
    files in a path like the following:
        s3://vicc-metakb/cdm/20220201/civic_cdm_20220201.json.zip

    :return: date string from retrieved files to use when loading to DB.
    :raise: ResourceLoadException if S3 initialization fails
    :raise: FileNotFoundError if unable to find files matching expected
        pattern in VICC MetaKB bucket.
    """
    echo_info("Attempting to fetch CDM files from S3 bucket")
    s3 = boto3.resource("s3", config=Config(region_name="us-east-2"))
    if not s3:
        raise ResourceLoadException("Unable to initiate AWS S3 Resource")
    bucket = sorted(
        list(
            s3.Bucket("vicc-metakb").objects.filter(Prefix="cdm").all()
        ),
        key=lambda f: f.key,
        reverse=True
    )
    newest_version: Optional[str] = None
    for file in bucket:
        match = re.match(s3_cdm_pattern, file.key)
        if match:
            source = match.group(1)
            if newest_version is None:
                newest_version = match.group(2)
            elif match.group(2) != newest_version:
                continue
        else:
            continue

        tmp_path = Path(tempfile.gettempdir()) / "metakb_dl_tmp"
        with open(tmp_path, "wb") as f:
            file.Object().download_fileobj(f)

        cdm_dir = APP_ROOT / "data" / source / "transform"
        cdm_zip = ZipFile(tmp_path, "r")
        cdm_zip.extract(f"{source}_cdm_{newest_version}.json", cdm_dir)

    if newest_version is None:
        raise FileNotFoundError("Unable to locate files matching expected "
                                "resource pattern in VICC s3 bucket")
    echo_info(f"Retrieved CDM files dated {newest_version}")
    return newest_version


def _harvest_sources(update_cached: bool) -> None:
    """Run harvesting procedure for all sources."""
    echo_info("Harvesting sources...")
    # TODO: Switch to using constant
    harvester_sources = {
        'civic': CivicHarvester,
        'moa': MoaHarvester
    }
    total_start = timer()
    for source_str, source_class in harvester_sources.items():
        echo_info(f"Harvesting {source_str}...")
        start = timer()

        if source_str == "civic" and update_cached:
            echo_info(
                "civicpy cache is being updated. This may take several minutes..."
            )
            source = source_class(update_cached=True, update_from_remote=False)
        else:
            source = source_class()

        source_successful = source.harvest()
        end = timer()

        if not source_successful:
            echo_info(f'{source_str} harvest failed.')
            click.get_current_context().exit()

        echo_info(f"{source_str} harvest finished in {(end - start):.5f} s")

    total_end = timer()
    echo_info(
        f"Successfully harvested all sources in {(total_end - total_start):.5f} s\n"
    )


async def _transform_sources() -> None:
    """Run transformation procedure for all sources."""
    echo_info("Transforming harvested data to CDM...")
    # TODO: Switch to using constant
    transform_sources = {
        'civic': CivicTransform,
        'moa': MoaTransform
    }
    total_start = timer()
    for src_str, src_name in transform_sources.items():
        echo_info(f"Transforming {src_str}...")
        start = timer()
        source = src_name()
        await source.transform()
        end = timer()
        echo_info(f"{src_str} transform finished in {(end - start):.5f} s.")
        source.create_json()
    total_end = timer()
    echo_info(
        f"Successfully transformed all sources to CDM in "
        f"{(total_end-total_start):.5f} s\n"
    )


def _load_normalizers_db(load_normalizer_db: bool, from_local: bool) -> None:
    """Load normalizer database source data.

    :param load_normalizer_db: Load normalizer database for each normalizer
    """
    disease_db = create_disease_db()
    therapy_db = create_therapy_db()
    gene_db = create_gene_db()

    if load_normalizer_db:
        load_disease = load_therapy = load_gene = True
    else:
        load_disease = (
            not disease_db.check_schema_initialized()
            or not disease_db.check_tables_populated()
        )
        load_therapy = (
            not therapy_db.check_schema_initialized()
            or not therapy_db.check_tables_populated()
        )
        load_gene = (
            not gene_db.check_schema_initialized()
            or not gene_db.check_tables_populated()
        )

    if load_disease:
        update_disease_sources(list(DiseaseSourceName), disease_db, True, from_local)

    if load_therapy:
        update_therapy_sources(list(TherapySourceName), therapy_db, True, from_local)

    if load_gene:
        update_gene_sources(list(GeneSourceName), gene_db, True, from_local)

    echo_info("Normalizers database loaded.\n")


def _check_db_param(param: str, name: str) -> str:
    """Check for MetaKB database parameter.

    :param param: value of parameter as received from command line
    :param name: name of parameter
    :return: parameter value, or exit with error message if unavailable
    """
    if not param:
        env_var_name = f'METAKB_DB_{name.upper()}'
        env_var_value = environ.get(env_var_name)
        if env_var_value:
            return env_var_value
        else:
            # Default is local
            if name == 'URL':
                return "bolt://localhost:7687"
            elif name == 'username':
                return 'neo4j'
            else:
                return 'password'
    else:
        return param


def _help_msg(msg: str = "") -> None:
    """Handle invalid user input.

    :param msg: Error message to display to user.
    """
    ctx = click.get_current_context()
    logger.fatal(msg)
    if msg:
        click.echo(msg)
    else:
        click.echo(ctx.get_help())
    ctx.exit()


if __name__ == '__main__':
    update_metakb_db(_anyio_backend="asyncio")
