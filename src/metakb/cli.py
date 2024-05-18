"""Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""
import datetime
import logging
import re
import tempfile
from os import environ
from pathlib import Path
from timeit import default_timer as timer
from zipfile import ZipFile

import asyncclick as click
import boto3
from boto3.exceptions import ResourceLoadException
from botocore.config import Config
from disease.database.database import AWS_ENV_VAR_NAME as DISEASE_AWS_ENV_VAR_NAME
from gene.database.database import AWS_ENV_VAR_NAME as GENE_AWS_ENV_VAR_NAME
from therapy.database.database import AWS_ENV_VAR_NAME as THERAPY_AWS_ENV_VAR_NAME

from metakb import APP_ROOT, DATE_FMT
from metakb.database import Graph
from metakb.harvesters.civic import CivicHarvester
from metakb.harvesters.moa import MoaHarvester
from metakb.normalizers import NormalizerName, ViccNormalizers, update_normalizer
from metakb.normalizers import check_normalizers as check_normalizer_health
from metakb.schemas.app import SourceName
from metakb.transform import CivicTransform, MoaTransform

logging.basicConfig(
    filename=f"{__name__}.log",
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    force=True,
)
_logger = logging.getLogger(__name__)


def _echo_info(msg: str) -> None:
    """Log (as INFO) and echo given message.

    :param msg: message to emit
    """
    click.echo(msg)
    _logger.info(msg)


def _help_msg(msg: str = "") -> None:
    """Handle invalid user input.

    :param msg: Error message to display to user.
    """
    ctx = click.get_current_context()
    _logger.fatal(msg)

    click.echo(msg) if msg else click.echo(ctx.get_help())

    ctx.exit()


@click.group()
def cli() -> None:
    """Manage MetaKB data.

    To reset the graph, prepare normalizers if unavailable, invalidate cached data, then
    load MetaKB data:

    \b
        $ metakb clear-graph
        $ metakb check-normalizers || metakb load-normalizers
        $ metakb update --refresh_source_caches

    Other commands are available for more granular control over the update process.
    """  # noqa: D301


_normalizer_db_url_description = "URL endpoint of normalizer database. If not given, the individual normalizers will revert to their own defaults."
_neo4j_db_url_description = "URL endpoint for the application Neo4j database."
_neo4j_creds_description = "Username and password to provide to application Neo4j database. Format as 'username:password'."


@cli.command()
@click.option("--normalizer_db_url", "-u", help=_normalizer_db_url_description)
@click.argument(
    "normalizer",
    type=click.Choice(list(NormalizerName), case_sensitive=False),
    nargs=-1,
)
def check_normalizers(
    db_url: str | None, normalizer: tuple[NormalizerName, ...]
) -> None:
    """Perform basic checks on DB health and table population for normalizers. Exits with
    status code 1 if >= 1 DB schema is uninitialized or critical tables appear empty for one
    or more of the concept normalizer services.

    \b
        $ metakb check-normalizers
        $ echo $?
        1  # indicates failure

    To select specific normalizer services, provide one or more arguments:

        $ metakb check-normalizers therapy disease

    Specific failures and descriptions are logged at level ERROR.
    \f
    :param db_url: URL endpoint for normalizer databases. Overrides defaults or env vars
        for each normalizer service.
    :param normalizer: tuple (possibly empty) of normalizer names to check
    """  # noqa: D301
    if not check_normalizer_health(db_url, normalizer):
        _logger.warning("Normalizer check failed.")
        click.get_current_context().exit(1)
    _logger.info("Normalizer check passed.")


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.argument(
    "normalizer",
    type=click.Choice(list(NormalizerName), case_sensitive=False),
    nargs=-1,
)
def update_normalizers(
    db_url: str | None, normalizer: tuple[NormalizerName, ...]
) -> None:
    """Reload gene, disease, and therapy normalizer data.

    Forces delete of each prior to fetching and loading new data. If errors are
    encountered, attempts to complete updates of other normalizers before exiting.

    Providing no arguments will attempt to update all three:

        $ metakb update-normalizers

    Providing individual normalizer names as arguments will update only those
    normalizers:

        $ metakb update-normalizers disease therapy

    \f
    :param db_url: URL endpoint of normalizers DynamoDB database. If not given, the
        individual normalizers will revert to their own defaults.
    :param normalizer: tuple (possibly empty) of normalizer names to update
    """  # noqa: D301
    success = True
    update_params = [
        (NormalizerName.DISEASE, DISEASE_AWS_ENV_VAR_NAME),
        (NormalizerName.THERAPY, THERAPY_AWS_ENV_VAR_NAME),
        (NormalizerName.GENE, GENE_AWS_ENV_VAR_NAME),
    ]
    if normalizer:
        update_params = [p for p in update_params if p[0] in normalizer]
    for name, aws_env_var_name in update_params:
        if aws_env_var_name in environ:
            msg = (
                f"Updating the {name.value} AWS database from the MetaKB CLI is "
                f"prohibited. Unset the environment variable:`{aws_env_var_name}` to "
                "proceed."
            )
            _logger.error(msg)
            click.echo(msg)
            success = False
            continue

        _echo_info(f"Loading {name.value} normalizer data...")
        try:
            update_normalizer(name, db_url)
        except (Exception, SystemExit) as e:
            _logger.error(
                "Encountered error while updating %s database: %s", name.value, e
            )
            click.echo(f"Failed to update {name.value} normalizer.")
            success = False
            continue
        _echo_info(f"Successfully loaded {name.value} normalizer data.\n")

    if success:
        _echo_info("Normalizer databases updated.\n")
    else:
        click.echo("Not all updates were successful. See logs for more details.")
        click.get_current_context().exit(1)


@cli.command()
@click.option(
    "--refresh_source_caches",
    "-r",
    is_flag=True,
    default=False,
    help=(
        "True if source caches (e.g. CIViCPy) should be updated prior to data regeneration. Note this will take several minutes. False if local cache should be used"
    ),
)
@click.option(
    "--output_directory",
    "-o",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=True,
        writable=True,
        path_type=Path,
    ),
    help="Directory to save output file(s) to.",
)
@click.argument(
    "source",
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
def harvest(
    refresh_source_caches: bool,
    output_directory: Path | None,
    source: tuple[SourceName, ...],
) -> None:
    """Perform harvest.

    If provided source(s), only perform harvest on those sources:

        $ metakb harvest civic

    \f
    :param refresh_source_caches: if true, refresh source caches. Otherwise, harvest
        from existing data if available.
    :param output_directory: directory to save output file(s) to
    :param source: tuple of source names. Harvest all sources if empty.
    """  # noqa: D301
    _harvest_sources(source, refresh_source_caches, output_directory)


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.option(
    "--output_directory",
    "-o",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=True,
        writable=True,
        path_type=Path,
    ),
    help="Directory to save output file(s) to.",
)
@click.argument(
    "source",
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
async def transform(
    normalizer_db_url: str | None,
    output_directory: Path | None,
    source: tuple[SourceName, ...],
) -> None:
    """Transform MetaKB source(s).
    \f
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param output_directory: directory to save output file(s) to
    :param source: tuple of source names. If empty, transform all sources.
    """  # noqa: D301
    await _transform_sources(source, output_directory, normalizer_db_url)


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.option(
    "--output_directory",
    "-o",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=True,
        writable=True,
        path_type=Path,
    ),
)
@click.argument(
    "harvest_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    nargs=1,
)
@click.argument(
    "source_name", type=click.Choice(list(SourceName), case_sensitive=False), nargs=1
)
async def transform_file(
    normalizer_db_url: str | None,
    output_directory: Path | None,
    harvest_file: Path,
    source_name: SourceName,
) -> None:
    """Transform an individual harvested data file. Source name must be specified as well.

        $ metakb transform-file path/to/file.json civic

    \f
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param output_directory: directory to save output file(s) to
    :param harvest_file: path to harvest output file
    :param source_name: name of source that harvested file comes from
    """  # noqa: D301
    normalizer_handler = ViccNormalizers(normalizer_db_url)
    await _transform_source(
        source_name, normalizer_handler, harvest_file, output_directory
    )


def _get_graph(db_url: str, db_creds: str | None) -> Graph:
    """Acquire Neo4j graph.

    :param db_url: URL endpoint for the application Neo4j database.
    :param db_creds: DB username and password, separated by a colon, e.g.
        ``"username:password"``.
    :return: Graph instance
    """
    if not db_creds:
        credentials = ("", "")  # revert to default behavior in graph constructor
    else:
        try:
            split_creds = db_creds.split(":", 1)
            credentials = (split_creds[0], split_creds[1])
        except IndexError:
            _help_msg(
                f"Argument to --db_credentialss appears invalid. Got '{db_creds}'. Should follow pattern 'username:password'."
            )
    return Graph(uri=db_url, credentials=credentials)


@cli.command()
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.option("--db_credentials", "-c", help=_neo4j_creds_description)
def clear_graph(db_url: str, db_credentials: str | None) -> None:
    """Wipe graph DB.

        $ metakb clear-graph

    Note that the Neo4j database URL, username, and password can either be set by CLI
    options, or by environment variables METAKB_DB_URL, METAKB_DB_USERNAME, and
    METAKB_DB_PASSWORD. If both are set, then CLI parameters take precedence. Provide
    credentials as a single string separated by a colon:

        $ metakb clear-graph --db_url=bolt://localhost:7687 --db_credentialss=username:password

    \f
    :param db_url: URL endpoint for the application Neo4j database.
    :param db_credentials: DB username and password, separated by a colon, e.g.
        ``"username:password"``.
    """  # noqa: D301
    graph = _get_graph(db_url, db_credentials)
    graph.clear()
    graph.close()


@cli.command()
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.option("--db_credentials", "-c", help=_neo4j_creds_description)
@click.option(
    "--from_s3",
    "-s",
    is_flag=True,
    help="Retrieves most recent data snapshot from the VICC S3 bucket and loads it. Mutually exclusive with target file arguments.",
)
@click.argument(
    "cdm_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    nargs=-1,
)
def load_cdm(
    db_url: str, db_credentials: str | None, from_s3: bool, cdm_file: tuple[Path, ...]
) -> None:
    """Load CDM files into Neo4j graph.

    If no arguments are provided, load latest available from default transformed data
    location for each MetaKB source:

        $ metakb load-cdm

    Pass path to file(s) to load from a custom location:

        $ metakb load-cdm path/to/file1.json path/to/file2.json

    Use --from_s3 option to instead fetch snapshot files from the MetaKB S3 bucket:

        $ metakb load-cdm --from_s3

    Note that the Neo4j database URL, username, and password can either be set by CLI
    options, or by environment variables METAKB_DB_URL, METAKB_DB_USERNAME, and
    METAKB_DB_PASSWORD. If both are set, then CLI parameters take precedence. Provide
    credentials as a single string separated by a colon:

        $ metakb load-cdm --db_url=bolt://localhost:7687 --db_credentialss=username:password

    \f
    :param db_url: URL endpoint for the application Neo4j database.
    :param db_credentials: DB username and password, separated by a colon, e.g.
        ``"username:password"``.
    :param from_s3: Skip data harvest/transform and load latest existing CDM files from
        VICC S3 bucket. Exclusive with ``cdm_file`` arguments.
    :param cdm_file: tuple of specific file(s) to load from. If empty, just get latest
        available locally for each source.
    """  # noqa: D301
    if from_s3 and cdm_file:
        _help_msg("Error: Cannot use both cdm_file args and --from_s3 option.")

    start = timer()
    _echo_info("Loading Neo4j database...")

    graph = _get_graph(db_url, db_credentials)

    if cdm_file:
        for file in cdm_file:
            graph.load_from_json(file)
    else:
        version = _retrieve_s3_cdms() if from_s3 else "*"

        for src in sorted([s.value for s in SourceName]):
            pattern = f"{src}_cdm_{version}.json"
            globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)

            try:
                path = sorted(globbed)[-1]
            except IndexError as e:
                msg = f"No valid transform file found matching pattern: {pattern}"
                raise FileNotFoundError(msg) from e

            graph.load_from_json(path)

    graph.close()
    end = timer()
    _echo_info(f"Successfully loaded neo4j database in {(end - start):.5f} s")


@cli.command()
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.option("--db_credentails", "-c", help=_neo4j_creds_description)
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.option(
    "--refresh_source_caches",
    "-r",
    is_flag=True,
    default=False,
    help=(
        "`True` if source caches (e.g. CIViCPy) should be updated prior to data regeneration. Note this will take several minutes. `False` if local cache should be used"
    ),
)
@click.argument(
    "source",
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
async def update(
    db_url: str,
    db_credentials: str | None,
    normalizer_db_url: str | None,
    refresh_source_caches: bool,
    source: tuple[SourceName, ...],
) -> None:
    """Execute data harvest and transformation from resources and upload to graph
    datastore.

    To harvest and transform source data into fresh CDM files, and then load them to
    the graph:

        $ metakb update

    Note that the Neo4j database URL, username, and password can either be set by CLI
    options, or by environment variables METAKB_DB_URL, METAKB_DB_USERNAME, and
    METAKB_DB_PASSWORD. If both are set, then CLI parameters take precedence. Provide
    credentials as a single string separated by a colon:

        $ metakb update --db_url=bolt://localhost:7687 --db_credentials=username:password

    \f
    :param db_url: URL endpoint for the application Neo4j database.
    :param db_credentials: DB username and password, separated by a colon, e.g.
        ``"username:password"``.
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param refresh_source_caches: ``True`` if source caches, i.e. CIViCPy, should be
        refreshed before loading data. Note this will take several minutes. Defaults to
        ``False``.
    :param source: source name(s) to update. If empty, update all sources.
    """  # noqa: D301
    _harvest_sources(source, refresh_source_caches)
    await _transform_sources(source, None, normalizer_db_url)

    start = timer()
    _echo_info("Loading Neo4j database...")

    graph = _get_graph(db_url, db_credentials)

    if not source:
        source = tuple(SourceName)
    for src in sorted([s.value for s in source]):
        pattern = f"{src}_cdm_*.json"
        globbed = (APP_ROOT / "data" / src / "transform").glob(pattern)

        try:
            path = sorted(globbed)[-1]
        except IndexError as e:
            msg = f"No valid transform file found matching pattern: {pattern}"
            raise FileNotFoundError(msg) from e

        graph.load_from_json(path)

    graph.close()
    end = timer()
    _echo_info(f"Successfully loaded neo4j database in {(end - start):.5f} s")


def _current_date_string() -> str:
    """Get current date as ISO8601 string

    :return: YYYYMMDD string
    """
    return datetime.datetime.strftime(
        datetime.datetime.now(tz=datetime.timezone.utc), DATE_FMT
    )


def _harvest_sources(
    sources: tuple[SourceName, ...],
    refresh_cache: bool,
    output_directory: Path | None = None,
) -> None:
    """Run harvesting procedure for all sources.

    :param sources: specific names of sources to harvest (harvest all if empty)
    :param refresh_cache: if ``True``, use cached source data if available. Otherwise,
        invalidate cache.
    :param output_directory: directory to save harvester output to
    """
    _echo_info("Harvesting sources...")
    harvester_sources = {
        SourceName.CIVIC: CivicHarvester,
        SourceName.MOA: MoaHarvester,
    }
    if sources:
        harvester_sources = {k: v for k, v in harvester_sources.items() if k in sources}
    total_start = timer()

    for name, source_class in harvester_sources.items():
        _echo_info(f"Harvesting {name.as_print_case()}...")
        start = timer()

        if name == SourceName.CIVIC and refresh_cache:
            # Use latest civic data
            _echo_info("(CIViCPy cache is also being updated)")
            source = source_class(update_cache=True, update_from_remote=False)
        else:
            source = source_class()

        output_file = (
            output_directory / f"{name.value}_harvester_{_current_date_string()}.json"
            if output_directory
            else None
        )
        harvested_data = source.harvest()
        source.save_harvested_data_to_file(harvested_data, output_file)
        end = timer()
        _echo_info(f"{name.as_print_case()} harvest finished in {(end - start):.2f} s")

    total_end = timer()
    _echo_info(
        f"Successfully harvested all sources in {(total_end - total_start):.2f} s"
    )


async def _transform_source(
    source: SourceName,
    normalizer_handler: ViccNormalizers,
    harvest_file: Path | None = None,
    output_directory: Path | None = None,
) -> None:
    """Transform an individual source.

    :param source: name of source
    :param normalizer_handler: container for normalizer access
    :param harvest_file: path to input file (if empty, transformer will use default location)
    :param output_directory: custom directory to store output to -- use source defaults
        if not given
    """
    transform_sources = {
        SourceName.CIVIC: CivicTransform,
        SourceName.MOA: MoaTransform,
    }
    _echo_info(f"Transforming {source.as_print_case()}...")
    start = timer()
    transformer: CivicTransform | MoaTransform = transform_sources[source](
        normalizers=normalizer_handler, harvester_path=harvest_file
    )
    await transformer.transform()
    end = timer()
    _echo_info(f"{source.as_print_case()} transform finished in {(end - start):.2f} s.")
    output_file = (
        output_directory / f"{source.value}_cdm_{_current_date_string()}.json"
        if output_directory
        else None
    )
    transformer.create_json(output_file)


async def _transform_sources(
    sources: tuple[SourceName, ...],
    output_directory: Path | None,
    normalizer_db_url: str | None = None,
) -> None:
    """Run transformation procedure for all sources.

    :param sources: names of source(s) to transform
    :param output_directory: custom directory to store output to -- use source defaults
        if not given
    :param normalizer_db_url: if given, attempt connection for all normalizers to this
        URL. Only works for DynamoDB data backends. Otherwise, fall back to
        specific normalizer env vars/defaults.
    """
    _echo_info("Transforming harvested data to CDM...")
    if not sources:
        sources = tuple(SourceName)
    normalizer_handler = ViccNormalizers(normalizer_db_url)
    total_start = timer()
    for source in sources:
        await _transform_source(
            source, normalizer_handler, output_directory=output_directory
        )
    total_end = timer()
    _echo_info(
        f"Successfully transformed all sources to CDM in "
        f"{(total_end - total_start):.2f} s"
    )


def _retrieve_s3_cdms() -> str:
    """Retrieve most recent CDM files from VICC S3 bucket.

    Expects to find files in a path like the following:
        s3://vicc-metakb/cdm/20220201/civic_cdm_20220201.json.zip

    :return: date string from retrieved files to use when loading to DB.
    :raise ResourceLoadException: if S3 initialization fails
    :raise FileNotFoundError:  if unable to find files matching expected pattern in
        VICC MetaKB bucket.
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
