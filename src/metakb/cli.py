"""Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import logging
import re
import tempfile
from os import environ
from pathlib import Path
from timeit import default_timer as timer
from typing import Optional
from zipfile import ZipFile

import asyncclick as click
import boto3
from boto3.exceptions import ResourceLoadException
from botocore.config import Config
from disease.cli import update_db as update_normalizer_disease_db
from gene.cli import update_normalizer_db as update_normalizer_gene_db
from therapy.cli import update_normalizer_db as update_normalizer_therapy_db

from metakb import APP_ROOT
from metakb.database import Graph
from metakb.harvesters.civic import CivicHarvester
from metakb.harvesters.moa import MoaHarvester
from metakb.schemas.app import SourceName
from metakb.transform import CivicTransform, MoaTransform

logger = logging.getLogger(__name__)


S3_CDM_PATTERN = re.compile(r"cdm/20[23]\d[01]\d[0123]\d/(.*)_cdm_(.*).json.zip")


def echo_info(msg: str) -> None:
    """Log (as INFO) and echo given message.

    :param msg: message to emit
    """
    click.echo(msg)
    logger.info(msg)


@click.command()
@click.option(
    "--db_url",
    default="bolt://localhost:7687",
    help=(
        "URL endpoint for the application Neo4j database. Can also be provided via environment variable METAKB_DB_URL, which takes priority."
    ),
)
@click.option(
    "--db_username",
    default="neo4j",
    help=(
        "Username to provide to application Neo4j database. Can also be provided via environment variable METAKB_DB_USERNAME, which takes priority."
    ),
)
@click.option(
    "--db_password",
    default="password",
    help=(
        "Password to provide to application Neo4j database. Can also be provided via environment variable METAKB_DB_PASSWORD, which takes priority."
    ),
)
@click.option(
    "--force_load_normalizers_db",
    "-f",
    is_flag=True,
    default=False,
    help=("Load all normalizers data into DynamoDB database."),
)
@click.option(
    "--normalizers_db_url",
    default="http://localhost:8000",
    help=(
        "URL endpoint of normalizers DynamoDB database. Set to `http://localhost:8000` by default."
    ),
)
@click.option(
    "--load_latest_cdms",
    "-l",
    is_flag=True,
    default=False,
    help=(
        "Clear MetaKB Neo4j database and load most recent available source CDM files. Does not run harvest and transform methods to generate new CDM files. Exclusive with --load_target_cdm and --load_latest_s3_cdms."
    ),
)
@click.option(
    "--load_target_cdm",
    "-t",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    required=False,
    help=(
        "Load transformed CDM file at specified path. Exclusive with --load_latest_cdms and --load_latest_s3_cdms."
    ),
)
@click.option(
    "--load_latest_s3_cdms",
    "-s",
    is_flag=True,
    default=False,
    required=False,
    help=(
        "Clear MetaKB database, retrieve most recent data available from public VICC S3 bucket, and load the database with retrieved data. Exclusive with --load_latest_cdms and load_target_cdm."
    ),
)
@click.option(
    "--update_cached",
    "-u",
    is_flag=True,
    default=False,
    required=False,
    help=(
        "`True` if civicpy cache should be updated. Note this will take several minutes. `False` if local cache should be used"
    ),
)
async def update_metakb_db(
    db_url: str,
    db_username: str,
    db_password: str,
    force_load_normalizers_db: bool,
    normalizers_db_url: str,
    load_latest_cdms: bool,
    load_target_cdm: Optional[Path],
    load_latest_s3_cdms: bool,
    update_cached: bool,
) -> None:
    """Execute data harvest and transformation from resources and upload to graph
    datastore.

    :param db_url: URL endpoint for the application Neo4j database. Can also be provided
        via environment variable ``METAKB_DB_URL``, which takes priority.
    :param db_username: Username to provide to application Neo4j database. Can also be
        provided via environment variable ``METAKB_DB_USERNAME``, which takes priority.
    :param db_password: Password to provide to application Neo4j database. Can also be
        provided via environment variable ``METAKB_DB_PASSWORD``, which takes priority.
    :param force_load_normalizers_db: Load all normalizers data into DynamoDB database.
    :param normalizers_db_url: URL endpoint of normalizers DynamoDB database. Set to
        ``http://localhost:8000`` by default.
    :param load_latest_cdms: Clear MetaKB Neo4j database and load most recent available
        source CDM files. Does not run harvest and transform methods to generate new CDM
        files. Exclusive with --load_target_cdm and --load_latest_s3_cdms.
    :param load_target_cdm: Load transformed CDM file at specified path. Exclusive with
        --load_latest_cdms and --load_latest_s3_cdms.
    :param load_latest_s3_cdms: Clear MetaKB database, retrieve most recent data
        available from public VICC S3 bucket, and load the database with retrieved data.
        Exclusive with --load_latest_cdms and load_target_cdm.
    :param update_cached: `True` if civicpy cache should be updated. Note this will take
        several minutes. `False` if local cache should be used
    """
    if sum([load_latest_cdms, bool(load_target_cdm), load_latest_s3_cdms]) > 1:
        _help_msg(
            "Error: Can only use one of `--load_latest_cdms`, `--load_target_cdm`, `--load_latest_s3_cdms`."
        )

    if not any([load_latest_cdms, load_target_cdm, load_latest_s3_cdms]):
        if force_load_normalizers_db:
            if normalizers_db_url:
                for env_var_name in [
                    "GENE_NORM_DB_URL",
                    "THERAPY_NORM_DB_URL",
                    "DISEASE_NORM_DB_URL",
                ]:
                    environ[env_var_name] = normalizers_db_url

            _load_normalizers_db()

        _harvest_sources(update_cached)
        await _transform_sources()

    # Load neo4j database
    start = timer()
    echo_info("Loading neo4j database...")

    g = Graph(uri=db_url, credentials=(db_username, db_password))

    if load_target_cdm:
        g.load_from_json(load_target_cdm)
    else:
        version = _retrieve_s3_cdms() if load_latest_s3_cdms else None
        g.clear()

        for src in sorted({v.value for v in SourceName.__members__.values()}):
            pattern = (
                f"{src}_cdm_{version}.json"
                if version is not None
                else f"{src}_cdm_*.json"
            )
            globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)

            try:
                path = sorted(globbed)[-1]
            except IndexError as e:
                msg = f"No valid transform file found matching pattern: {pattern}"
                raise FileNotFoundError(msg) from e

            g.load_from_json(path)

    g.close()
    end = timer()
    echo_info(f"Successfully loaded neo4j database in {(end - start):.5f} s\n")


def _retrieve_s3_cdms() -> str:
    """Retrieve most recent CDM files from VICC S3 bucket.
    Expects to find files in a path like the following:
        s3://vicc-metakb/cdm/20220201/civic_cdm_20220201.json.zip

    :raise ResourceLoadException: if S3 initialization fails
    :raise FileNotFoundError:  if unable to find files matching expected
        pattern in VICC MetaKB bucket.
    :return: date string from retrieved files to use when loading to DB.
    """
    echo_info("Attempting to fetch CDM files from S3 bucket")
    s3 = boto3.resource("s3", config=Config(region_name="us-east-2"))

    if not s3:
        msg = "Unable to initiate AWS S3 Resource"
        raise ResourceLoadException(msg)

    bucket = sorted(  # noqa: C414
        list(s3.Bucket("vicc-metakb").objects.filter(Prefix="cdm").all()),
        key=lambda f: f.key,
        reverse=True,
    )
    newest_version: Optional[str] = None

    for file in bucket:
        match = re.match(S3_CDM_PATTERN, file.key)

        if match:
            source = match.group(1)
            if newest_version is None:
                newest_version = match.group(2)
            elif match.group(2) != newest_version:
                continue
        else:
            continue

        tmp_path = Path(tempfile.gettempdir()) / "metakb_dl_tmp"
        with tmp_path.open("wb") as f:
            file.Object().download_fileobj(f)

        cdm_dir = APP_ROOT / "data" / source / "transform"
        cdm_zip = ZipFile(tmp_path, "r")
        cdm_zip.extract(f"{source}_cdm_{newest_version}.json", cdm_dir)

    if newest_version is None:
        msg = "Unable to locate files matching expected resource pattern in VICC s3 bucket"
        raise FileNotFoundError(msg)

    echo_info(f"Retrieved CDM files dated {newest_version}")
    return newest_version


def _harvest_sources(update_cached: bool) -> None:
    """Run harvesting procedure for all sources.

    :param update_cached: `True` if civicpy cache should be updated. Note this will take
        several minutes. `False` if local cache should be used
    """
    echo_info("Harvesting sources...")
    harvester_sources = {
        SourceName.CIVIC.value: CivicHarvester,
        SourceName.MOA.value: MoaHarvester,
    }
    total_start = timer()

    for source_str, source_class in harvester_sources.items():
        echo_info(f"Harvesting {source_str}...")
        start = timer()

        if source_str == SourceName.CIVIC.value and update_cached:
            # Use latest civic data
            echo_info("(civicpy cache is also being updated)")
            source = source_class(update_cache=True, update_from_remote=False)
        else:
            source = source_class()

        source_successful = source.harvest()

        end = timer()

        if not source_successful:
            echo_info(f"{source_str} harvest failed.")
            click.get_current_context().exit()

        echo_info(f"{source_str} harvest finished in {(end - start):.5f} s")

    total_end = timer()
    echo_info(
        f"Successfully harvested all sources in {(total_end - total_start):.5f} s\n"
    )


@staticmethod
async def _transform_sources() -> None:
    """Run transformation procedure for all sources."""
    echo_info("Transforming harvested data to CDM...")
    transform_sources = {
        SourceName.CIVIC.value: CivicTransform,
        SourceName.MOA.value: MoaTransform,
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
        f"{(total_end - total_start):.5f} s\n"
    )


def _load_normalizers_db() -> None:
    """Load normalizer DynamoDB database source data."""
    for name, update_normalizer_db_fn in [
        ("Disease", update_normalizer_disease_db),
        ("Therapy", update_normalizer_therapy_db),
        ("Gene", update_normalizer_gene_db),
    ]:
        _update_normalizer_db(name, update_normalizer_db_fn)

    echo_info("Normalizers database loaded.\n")


def _update_normalizer_db(
    name: str,
    update_normalizer_db_fn: callable,
) -> None:
    """Update Normalizer DynamoDB database.

    :param name: Name of the normalizer
    :param update_normalizer_db_fn: Function to update the normalizer DynamoDB database
    """
    try:
        echo_info(f"\nLoading {name} Normalizer data...")
        update_normalizer_db_fn(["--update_all", "--update_merged"])
        echo_info(f"Successfully Loaded {name} Normalizer data.\n")
    except SystemExit as e:
        if e.code != 0:
            raise e


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


if __name__ == "__main__":
    update_metakb_db(_anyio_backend="asyncio")
