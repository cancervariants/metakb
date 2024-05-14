"""Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import logging
import re
import tempfile
from enum import StrEnum
from os import environ
from pathlib import Path
from timeit import default_timer as timer
from zipfile import ZipFile

import asyncclick as click
import boto3
from boto3.exceptions import ResourceLoadException
from botocore.config import Config
from disease.cli import update_db as update_normalizer_disease_db
from disease.database.database import AWS_ENV_VAR_NAME as DISEASE_AWS_ENV_VAR_NAME
from gene.cli import update_normalizer_db as update_normalizer_gene_db
from gene.database.database import AWS_ENV_VAR_NAME as GENE_AWS_ENV_VAR_NAME
from therapy.cli import update_normalizer_db as update_normalizer_therapy_db
from therapy.database.database import AWS_ENV_VAR_NAME as THERAPY_AWS_ENV_VAR_NAME

from metakb import APP_ROOT
from metakb.database import Graph
from metakb.harvesters.civic import CivicHarvester
from metakb.harvesters.moa import MoaHarvester
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.normalizers import (
    check_normalizers as check_normalizer_health,
)
from metakb.schemas.app import SourceName
from metakb.transform import CivicTransform, MoaTransform

logging.basicConfig(
    filename=f"{__name__}.log",
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    force=True,
)
_logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Manage MetaKB data."""


def _echo_info(msg: str) -> None:
    """Log (as INFO) and echo given message.

    :param msg: message to emit
    """
    click.echo(msg)
    _logger.info(msg)


@cli.command()
@click.option(
    "--db_url",
    "-u",
    help="URL endpoint of normalizer database. If not given, the individual normalizers will use their own default, which is a DynamoDB connection to 'http://localhost:8000'.",
)
def check_normalizers(db_url: str | None) -> None:
    """Perform basic checks on DB health and population for all normalizers. Exits with
    status code 1 if DB schema is uninitialized or critical tables appear empty for one
    or more of the concept normalizer services.

    \b
        $ metakb check-normalizers
        $ echo $?
        1  # indicates failure

    \f
    :param db_url: URL endpoint for normalizer databases. Overrides defaults or env vars
        for each normalizer service.
    """  # noqa: D301
    if not check_normalizer_health(db_url):
        _logger.warning("Normalizer check failed.")
        click.get_current_context().exit(1)
    _logger.info("Normalizer check passed.")


@cli.command()
@click.option(
    "--db_url",
    help=(
        "URL endpoint of normalizers DynamoDB database. If not given, defaults to URL environment variables or `http://localhost:8000` per the configuration rules of the individual normalizers."
    ),
)
def load_normalizers(db_url: str | None) -> None:
    """Reload gene, disease, and therapy normalizer data.

    Forces delete of each prior to fetching and loading new data. If errors are
    encountered, attempts to complete updates of other normalizers before exiting.

    \f
    :param db_url: URL endpoint of normalizers DynamoDB database. If not given,
        defaults to ``http://localhost:8000`` per the configuration rules of the
        individual normalizers.
    """  # noqa: D301
    success = True
    updater_args = ["--update_all", "--update_merged"]
    if db_url:
        updater_args += ["--db_url", db_url]
    for name, update_normalizer_db_fn, aws_env_var_name in [
        ("Disease", update_normalizer_disease_db, DISEASE_AWS_ENV_VAR_NAME),
        ("Therapy", update_normalizer_therapy_db, THERAPY_AWS_ENV_VAR_NAME),
        ("Gene", update_normalizer_gene_db, GENE_AWS_ENV_VAR_NAME),
    ]:
        if aws_env_var_name in environ:
            _logger.warning(
                "Updating the %s AWS database via the MetaKB CLI is prohibited -- unset env var %s",
                name,
                aws_env_var_name,
            )
            click.echo(
                f"You cannot update the {name} AWS database. You must unset the "
                f"environment variable:`{aws_env_var_name}`"
            )
            success = False
            continue

        _echo_info(f"\nLoading {name} Normalizer data...")
        try:
            update_normalizer_db_fn(["--update_all", "--update_merged"])
        except SystemExit as e:
            _logger.error("Encountered error while updating %s database: %s", name, e)
            click.echo(f"Failed to update {name} normalizer.")
            success = False
            continue
        _echo_info(f"Successfully Loaded {name} Normalizer data.\n")

    if success:
        _echo_info("Normalizers database loaded.\n")
    else:
        click.get_current_context().exit(1)


class _LoadCdmOption(StrEnum):
    LOCAL = "local"
    S3 = "s3"


@cli.command()
@click.option(
    "--db_url",
    default="",
    help="URL endpoint for the application Neo4j database.",
)
@click.option(
    "--db_creds",
    help="Username and password to provide to application Neo4j database. Format as 'username:password'.",
)
@click.option(
    "--normalizer_db_url",
    help=(
        "URL endpoint of normalizers DynamoDB database. If not given, defaults to `http://localhost:8000` or DB URL environment variables per the configuration rules of the individual normalizers."
    ),
)
@click.option(
    "--load_cdm",
    "-l",
    type=click.Choice(list(_LoadCdmOption), case_sensitive=False),
    help=(
        "Load the most recent data. 'local': Clears the database and loads the most recent data from local source files. 's3': Clears the database, retrieves the most recent data from the VICC S3 bucket, and loads it. Exclusive with --load-target-cdm."
    ),
)
@click.option(
    "--load_target_cdm",
    "-t",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help=(
        "Load transformed CDM file at specified path. Exclusive with --load_latest_cdms and --load_latest_s3_cdms."
    ),
)
@click.option(
    "--update_source_caches",
    "-u",
    is_flag=True,
    default=False,
    help=(
        "`True` if source caches (e.g. CivicPy) should be updated prior to data regeneration. Note this will take several minutes. `False` if local cache should be used"
    ),
)
async def update(
    db_url: str,
    db_creds: str | None,
    normalizer_db_url: str | None,
    load_cdm: _LoadCdmOption | None,
    load_target_cdm: Path | None,
    update_source_caches: bool,
) -> None:
    """Execute data harvest and transformation from resources and upload to graph
    datastore.

    To wipe all data, perform a complete refresh of biomedical concept normalizer data,
    and fetch latest data from sources:

        $ metakb update --force_load_normalizers_db --load_latest_cdms --update_cached

    To load the latest published source data from the VICC storage repository:

        $ metakb update --load_latest_s3_cdms

    Note that the Neo4j database URL, username, and password can either be set by CLI
    options, or by environment variables METAKB_DB_URL, METAKB_DB_USERNAME, and
    METAKB_DB_PASSWORD. If both are set, then CLI parameters take precedence.

    \f
    :param db_url: URL endpoint for the application Neo4j database. Can also be provided
        via environment variable ``METAKB_DB_URL``, which takes priority.
    :param db_creds: DB username and password, separated by a colon, e.g.
        ``"username:password"``.
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to ``http://localhost:8000`` per the configuration rules of the
        individual normalizers.
    :param load_cdm:
    :param load_target_cdm: Load transformed CDM file at specified path. Exclusive with
        ``--load_cdm``.
    :param update_source_caches: ``True`` if source caches, i.e. civicpy, should be
        refreshed before loading data. Note this will take several minutes. Defaults to
        ``False``.
    """  # noqa: D301
    if load_cdm and load_target_cdm:
        _help_msg("Error: Can only use one of `--load_cdm` and `--load_target_cdm`.")

    if (not load_cdm) and (not load_target_cdm):
        _harvest_sources(update_source_caches)
        await _transform_sources(normalizer_db_url)

    start = timer()
    _echo_info("Loading Neo4j database...")

    if not db_creds:
        credentials = ("", "")  # revert to default behavior in graph constructor
    else:
        try:
            split_creds = db_creds.split(":", 1)
            credentials = (split_creds[0], split_creds[1])
        except IndexError:
            _help_msg(
                f"Argument to --db_creds appears invalid. Got '{db_creds}'. Should follow pattern 'username:password'."
            )
    g = Graph(uri=db_url, credentials=credentials)

    if load_target_cdm:
        g.load_from_json(load_target_cdm)
    else:
        version = _retrieve_s3_cdms() if load_cdm == _LoadCdmOption.S3 else "*"
        g.clear()

        for src in sorted([s.value for s in SourceName]):
            pattern = f"{src}_cdm_{version}.json"
            globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)

            try:
                path = sorted(globbed)[-1]
            except IndexError as e:
                msg = f"No valid transform file found matching pattern: {pattern}"
                raise FileNotFoundError(msg) from e

            g.load_from_json(path)

    g.close()
    end = timer()
    _echo_info(f"Successfully loaded neo4j database in {(end - start):.5f} s\n")


def _help_msg(msg: str = "") -> None:
    """Handle invalid user input.

    :param msg: Error message to display to user.
    """
    ctx = click.get_current_context()
    _logger.fatal(msg)

    if msg:
        click.echo(msg)
    else:
        click.echo(ctx.get_help())

    ctx.exit()


def _harvest_sources(update_cached: bool) -> None:
    """Run harvesting procedure for all sources.

    :param update_cached: `True` if civicpy cache should be updated. Note this will take
        several minutes. `False` if local cache should be used
    """
    _echo_info("Harvesting sources...")
    harvester_sources = {
        SourceName.CIVIC.value: CivicHarvester,
        SourceName.MOA.value: MoaHarvester,
    }
    total_start = timer()

    for source_str, source_class in harvester_sources.items():
        _echo_info(f"Harvesting {source_str}...")
        start = timer()

        if source_str == SourceName.CIVIC.value and update_cached:
            # Use latest civic data
            _echo_info("(civicpy cache is also being updated)")
            source = source_class(update_cache=True, update_from_remote=False)
        else:
            source = source_class()

        harvested_data = source.harvest()
        source.save_harvested_data_to_file(harvested_data)
        end = timer()
        _echo_info(f"{source_str} harvest finished in {(end - start):.5f} s")

    total_end = timer()
    _echo_info(
        f"Successfully harvested all sources in {(total_end - total_start):.5f} s\n"
    )


async def _transform_sources(normalizer_db_url: str | None = None) -> None:
    """Run transformation procedure for all sources.

    :param normalizer_db_url: if given, attempt connection for all normalizers to this
        URL. Only works for DynamoDB data backends. Otherwise, fall back to
        specific normalizer env vars/defaults.
    """
    _echo_info("Transforming harvested data to CDM...")
    transform_sources: dict[str, type[CivicTransform] | type[MoaTransform]] = {
        SourceName.CIVIC.value: CivicTransform,
        SourceName.MOA.value: MoaTransform,
    }
    total_start = timer()

    normalizer_handler = ViccNormalizers(normalizer_db_url)

    for src_str, transformer in transform_sources.items():
        _echo_info(f"Transforming {src_str}...")
        start = timer()
        source = transformer(normalizers=normalizer_handler)
        await source.transform()
        end = timer()
        _echo_info(f"{src_str} transform finished in {(end - start):.5f} s.")
        source.create_json()

    total_end = timer()
    _echo_info(
        f"Successfully transformed all sources to CDM in "
        f"{(total_end - total_start):.5f} s\n"
    )


def _retrieve_s3_cdms() -> str:
    """Retrieve most recent CDM files from VICC S3 bucket.

    Expects to find files in a path like the following:
        s3://vicc-metakb/cdm/20220201/civic_cdm_20220201.json.zip

    :return: date string from retrieved files to use when loading to DB.
    :raise ResourceLoadException: if S3 initialization fails
    :raise FileNotFoundError:  if unable to find files matching expected
        pattern in VICC MetaKB bucket.
    """
    _echo_info("Attempting to fetch CDM files from S3 bucket")
    s3 = boto3.resource("s3", config=Config(region_name="us-east-2"))

    if not s3:
        msg = "Unable to initiate AWS S3 Resource"
        raise ResourceLoadException(msg)

    bucket = sorted(  # noqa: C414
        list(s3.Bucket("vicc-metakb").objects.filter(Prefix="cdm").all()),
        key=lambda f: f.key,
        reverse=True,
    )
    newest_version: str | None = None

    for file in bucket:
        match = re.match(
            re.compile(r"cdm/20[23]\d[01]\d[0123]\d/(.*)_cdm_(.*).json.zip"), file.key
        )

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

    _echo_info(f"Retrieved CDM files dated {newest_version}")
    return newest_version


if __name__ == "__main__":
    cli()
