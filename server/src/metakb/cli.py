"""Provide CLI utility for performing data collection, transformation, and upload
to graph datastore.
"""

import asyncio
import importlib.metadata as importlib_metadata
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from timeit import default_timer as timer
from urllib.parse import urlparse

import click
from botocore.exceptions import ClientError, EndpointConnectionError

from metakb import __version__
from metakb.config import get_config
from metakb.harvesters import (
    CBioPortalHarvester,
    CivicHarvester,
    FdaPodaHarvester,
    MoaHarvester,
)
from metakb.harvesters.base import FetchMode, Harvester
from metakb.harvesters.mci import MciHarvester
from metakb.log_config import configure_logs
from metakb.normalizers import (
    NORMALIZER_AWS_ENV_VARS,
    IllegalUpdateError,
    NormalizerName,
    ViccNormalizers,
    probe_variation_normalizer_runtime,
    update_normalizer,
)
from metakb.normalizers import check_normalizers as check_normalizer_health
from metakb.repository.base import AbstractRepository
from metakb.repository.neo4j_repository import Neo4jRepository, get_driver
from metakb.schemas.app import SourceName
from metakb.services import load_from_json, save_db_snapshot
from metakb.source_data import SourceDataStore
from metakb.transformers import (
    CivicTransformer,
    FdaPodaTransformer,
    MciTransformer,
    MoaTransformer,
)

_logger = logging.getLogger(__name__)


def _echo_info(msg: str, quiet: bool = False) -> None:
    """Log (as INFO) and echo given message.

    :param msg: message to emit
    :param quiet: if true, suppress console output
    """
    if not quiet:
        click.echo(msg)
    _logger.info(msg)


def _get_transform_env_diagnostics(normalizer_db_url: str | None) -> list[str]:
    """Collect baseline environment diagnostics for transform preflight.
    This is a helper function for ensuring environment variables are properly set prior to running transform.

    :param normalizer_db_url: optional explicit normalizer database URL
    :return: list of issues found
    """
    diagnostics: list[str] = []

    if not normalizer_db_url:
        normalizer_env = {
            "GENE_NORM_DB_URL": os.environ.get("GENE_NORM_DB_URL"),
            "DISEASE_NORM_DB_URL": os.environ.get("DISEASE_NORM_DB_URL"),
            "THERAPY_NORM_DB_URL": os.environ.get("THERAPY_NORM_DB_URL"),
        }
        for env_name, value in normalizer_env.items():
            if not value:
                diagnostics.append(
                    f"{env_name} is not set (required when running CLI from host)."
                )

    seqrepo_root = os.environ.get("SEQREPO_ROOT_DIR")
    if not seqrepo_root:
        diagnostics.append("SEQREPO_ROOT_DIR is not set.")
    elif not Path(seqrepo_root).exists():
        diagnostics.append(
            f"SEQREPO_ROOT_DIR points to a path that does not exist: {seqrepo_root}"
        )

    if not os.environ.get("UTA_DB_URL"):
        diagnostics.append("UTA_DB_URL is not set.")

    return diagnostics


async def _get_preflighted_normalizers(
    normalizer_db_url: str | None,
) -> ViccNormalizers:
    """Initialize normalizer dependencies for transform workflows and verify that they are online.

    :param normalizer_db_url: optional explicit normalizer database URL
    :raises click.ClickException: If required dependencies are unavailable
    :return: initialized normalizer container
    """
    diagnostics = _get_transform_env_diagnostics(normalizer_db_url)
    if diagnostics:
        msg = "\n".join(
            [
                "Transform preflight failed due to missing local configuration:",
                *[f"- {d}" for d in diagnostics],
                "Tip: when running from host with compose-dev services, set "
                "GENE_NORM_DB_URL=http://localhost:8011, "
                "DISEASE_NORM_DB_URL=http://localhost:8012, "
                "THERAPY_NORM_DB_URL=http://localhost:8013, plus UTA_DB_URL and "
                "SEQREPO_ROOT_DIR.",
            ]
        )
        raise click.ClickException(msg)

    try:
        normalizer_handler = ViccNormalizers(normalizer_db_url)
    except EndpointConnectionError as e:
        msg = (
            "Unable to connect to one or more normalizer databases. "
            "Check GENE_NORM_DB_URL/DISEASE_NORM_DB_URL/THERAPY_NORM_DB_URL.\n"
            f"Original error: {e}"
        )
        raise click.ClickException(msg) from e
    except ClientError as e:
        msg = (
            "Normalizer endpoint responded with an unexpected API error. "
            "This often means the URL points at a non-normalizer service "
            "(for example, MetaKB API on :8000 instead of DynamoDB local).\n"
            f"Original error: {e}"
        )
        raise click.ClickException(msg) from e
    except Exception as e:
        msg = (
            "Failed to initialize normalizers. Verify normalizer endpoints, UTA DB "
            "connectivity, and SeqRepo configuration.\n"
            f"Original error: {e}"
        )
        raise click.ClickException(msg) from e

    # Probe concept normalizers to fail fast if services are misconfigured.
    concept_probes = (
        ("gene", lambda: normalizer_handler.normalize_gene("BRAF")),
        (
            "disease",
            lambda: normalizer_handler.normalize_disease("melanoma"),
        ),
        ("therapy", lambda: normalizer_handler.normalize_therapy("aspirin")),
    )
    for concept_name, probe in concept_probes:
        try:
            probe()
        except Exception as e:
            msg = (
                f"{concept_name.capitalize()} normalizer probe failed. "
                "Confirm endpoint accessibility and loaded tables.\n"
                f"Original error: {e}"
            )
            raise click.ClickException(msg) from e

    # Probe variation normalizer for UTA/SeqRepo readiness.
    probe_result = await probe_variation_normalizer_runtime(normalizer_handler)
    if probe_result.error:
        e = probe_result.error
        if (
            isinstance(e, AttributeError)
            and "ValidationInfo" in str(e)
            and "warnings" in str(e)
        ):
            pydantic_version = importlib_metadata.version("pydantic")
            variation_norm_version = importlib_metadata.version("variation-normalizer")
            msg = (
                "Variation normalizer failed due to a dependency compatibility issue.\n"
                f"Detected pydantic=={pydantic_version}, variation-normalizer=={variation_norm_version}.\n"
                "Known symptom: AttributeError involving `ValidationInfo` and "
                "`warnings`.\n"
                "Try pinning pydantic below 2.12 in this environment, e.g.:\n"
                '  pip install "pydantic<2.12"'
            )
            raise click.ClickException(msg) from e
        msg = (
            "Variation normalizer probe failed. This typically indicates UTA or "
            "SeqRepo is unavailable/misconfigured (check UTA_DB_URL and "
            "SEQREPO_ROOT_DIR).\n"
            f"Original error: {e}"
        )
        raise click.ClickException(msg) from e
    if not probe_result.variation_found:
        msg = (
            "Variation normalizer probe returned no result for 'BRAF V600E'. "
            "This indicates variation normalization is not operational in this "
            "environment (commonly UTA/SeqRepo misconfiguration or inaccessible "
            "normalizer dependencies).\n"
            f"Variation normalizer warnings: {probe_result.warnings}"
        )
        raise click.ClickException(msg)

    return normalizer_handler


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """Manage MetaKB data.

    To reset the graph, prepare normalizers if unavailable, invalidate cached data, then
    load MetaKB data:

    \b
        $ metakb clear-db
        $ metakb check-normalizers || metakb load-normalizers
        $ metakb update --refresh_source_caches

    Other commands are available for more granular control over the update process.
    """  # noqa: D301
    configure_logs(logging.DEBUG) if get_config().debug else configure_logs()


_normalizer_db_url_description = "URL endpoint of normalizer database. If not given, the individual normalizers will revert to their own defaults."
_neo4j_db_url_description = "Connection string for the application Neo4j database."


def _print_enum_metavar(enum: type[Enum]) -> str:
    """Format enum for Click metavar printout in help message.

    :param enum: enum class
    :return: formatted string, eg "[[civic|moa]]..."
    """
    return f"[[{'|'.join(list(enum))}]]..."


@cli.command()
@click.option("--normalizer_db_url", "-u", help=_normalizer_db_url_description)
@click.argument(
    "normalizers",
    metavar=_print_enum_metavar(NormalizerName),
    type=click.Choice(list(NormalizerName), case_sensitive=False),
    nargs=-1,
)
def check_normalizers(
    normalizer_db_url: str | None, normalizers: tuple[NormalizerName, ...]
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
    :param normalizer_db_url: URL endpoint for normalizer databases. Overrides defaults or env
        vars for each normalizer service.
    :param normalizers: tuple (possibly empty) of normalizer names to check
    """  # noqa: D301
    if not check_normalizer_health(normalizer_db_url, normalizers):
        _logger.warning("Normalizer check failed.")
        click.get_current_context().exit(1)
    _logger.info("Normalizer check passed.")


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.argument(
    "normalizers",
    metavar=_print_enum_metavar(NormalizerName),
    type=click.Choice(list(NormalizerName), case_sensitive=False),
    nargs=-1,
)
def update_normalizers(
    normalizer_db_url: str | None, normalizers: tuple[NormalizerName, ...]
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
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, the individual normalizers will revert to their own defaults.
    :param normalizers: tuple (possibly empty) of normalizer names to update
    """  # noqa: D301
    success = True
    if not normalizers:
        normalizers = tuple(NormalizerName)
    for name in normalizers:
        _echo_info(f"Loading {name.value} normalizer data...")
        try:
            update_normalizer(name, normalizer_db_url)
        except IllegalUpdateError:
            msg = (
                f"Updating the {name.value} AWS database from the MetaKB CLI is "
                f"prohibited. Unset the environment variable "
                f"{NORMALIZER_AWS_ENV_VARS[name]} to proceed."
            )
            _logger.exception(msg)
            click.echo(msg)
            success = False
            continue
        except (Exception, SystemExit):
            _logger.exception(
                "Encountered error while updating %s database", name.value
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
@click.argument(
    "sources",
    metavar=_print_enum_metavar(SourceName),
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
def harvest(
    refresh_source_caches: bool,
    sources: tuple[SourceName, ...],
) -> None:
    """Perform harvest.

    If provided SOURCE(s), only perform harvest on those sources:

        $ metakb harvest civic

    Otherwise, harvest all known sources.

    \f
    :param refresh_source_caches: if true, refresh source caches. Otherwise, harvest
        from existing data if available.
    :param sources: tuple of source names. Harvest all sources if empty.
    """  # noqa: D301
    _harvest_sources(sources, refresh_source_caches)


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
@click.argument(
    "sources",
    metavar=_print_enum_metavar(SourceName),
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
def transform(
    normalizer_db_url: str | None,
    sources: tuple[SourceName, ...],
) -> None:
    """Transform MetaKB SOURCE(s).

    If provided names of SOURCEs, perform transform on those sources only:

        $ metakb transform civic

    Otherwise, transform all available sources.

    \f
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param sources: tuple of source names. If empty, transform all sources.
    """  # noqa: D301
    asyncio.run(_transform_sources(sources, normalizer_db_url))


async def _transform_file(
    normalizer_db_url: str | None,
    harvest_file: Path,
    source_name: SourceName,
) -> None:
    """Perform transformation on a specific source harvest file"""
    normalizer_handler = await _get_preflighted_normalizers(normalizer_db_url)
    await _transform_source(source_name, normalizer_handler, harvest_file)


@cli.command()
@click.option("--normalizer_db_url", "-n", help=_normalizer_db_url_description)
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
    harvest_file: Path,
    source_name: SourceName,
) -> None:
    """Transform an individual harvested data file. Source name must be specified as well.

        $ metakb transform-file path/to/file.json civic

    \f
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param harvest_file: path to harvest output file
    :param source_name: name of source that harvested file comes from
    """  # noqa: D301
    asyncio.run(_transform_file(normalizer_db_url, harvest_file, source_name))


@asynccontextmanager
async def _get_repository(db_url: str | None) -> AsyncGenerator[AbstractRepository]:
    """Acquire repository session instance for CLI functions.

    This function wraps the driver factory function in a context manager to ensure proper
    lifespan management (i.e. close it when the session concludes)

    :param db_url: URL endpoint for the application Neo4j database.
    :return: Graph driver instance
    """
    driver = get_driver(db_url)
    session = driver.session()
    repo = Neo4jRepository(session)
    try:
        await repo.initialize()
        yield repo
    finally:
        await session.close()
        await driver.close()


async def _clear_db(db_url: str) -> None:
    """Perform async teardown of DB

    Dispatch with asyncio.run() from a `click` function
    """
    click.echo("Clearing MetaKB DB...")
    async with _get_repository(db_url) as repo:
        await repo.teardown_db()
    click.echo("Finishing clearing MetaKB DB.")


@cli.command()
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
def clear_db(db_url: str) -> None:
    """Clear graph DB.

        $ metakb clear-db

    Note that the Neo4j database URL, username, and password can either be set by a CLI
    options, or by the environment variable METAKB_DB_URL. For example:

        $ metakb clear-db --db_url=bolt://username:password@localhost:7687

    \f
    :param db_url: connection string for the application Neo4j database.
    """  # noqa: D301
    asyncio.run(_clear_db(db_url))


def _confirm_remote(uri: str, assume_yes: bool) -> None:
    if not uri:
        uri = os.environ.get("METAKB_DB_URL", "")
    host = urlparse(uri).hostname
    if assume_yes or host in {"localhost", "127.0.0.1", "::1", None}:
        return

    click.confirm(
        f"You are about to load data into a remote Neo4j instance:\n\n"
        f"    {host}\n\n"
        "Continue?",
        abort=True,
    )


@cli.group()
def load() -> None:
    """Load transformed source data into the MetaKB database."""


async def _load_sources(
    db_url: str, sources: tuple[SourceName, ...], quiet: bool
) -> None:
    async with _get_repository(db_url) as repository:
        for source in sources:
            if source == SourceName.CBIOPORTAL:
                continue  # not yet supported
            src_data = SourceDataStore(src_name=source)
            cdm_file = src_data.get_latest_transformed_file()
            await load_from_json(cdm_file, repository, silent=quiet)


@load.command("all")
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output.")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts.")
def load_all(db_url: str, quiet: bool, yes: bool) -> None:
    """Load the latest transformed data artifacts for each source into the MetaKB database.

        $ metakb load all

    Note that the Neo4j database URL, username, and password can either be set by a CLI
    options, or by the environment variable METAKB_DB_URL. For example:

        $ metakb load all --db_url=bolt://username:password@localhost:7687
    """
    _confirm_remote(db_url, yes)
    asyncio.run(_load_sources(db_url, tuple(SourceName), quiet))


@load.command("sources")
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.argument(
    "sources",
    metavar=_print_enum_metavar(SourceName),
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output.")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts.")
def load_sources(
    db_url: str, sources: tuple[SourceName, ...], quiet: bool, yes: bool
) -> None:
    """Load latest transformed artifacts for the named source(s) into the MetaKB database.

        $ metakb load sources moa civic

    Note that the Neo4j database URL, username, and password can either be set by a CLI
    options, or by the environment variable METAKB_DB_URL. For example:

        $ metakb load sources --db_url=bolt://username:password@localhost:7687 civic
    """
    _confirm_remote(db_url, yes)
    asyncio.run(_load_sources(db_url, sources, quiet))


async def _load_files(db_url: str, files: tuple[Path, ...], quiet: bool) -> None:
    async with _get_repository(db_url) as repository:
        for file in files:
            await load_from_json(file, repository, silent=quiet)


@load.command("files")
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.argument(
    "files",
    metavar="[CDM_FILE]...",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    nargs=-1,
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output.")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts.")
def load_files(db_url: str, files: tuple[Path, ...], quiet: bool, yes: bool) -> None:
    """Load specific transformed data artifacts into the MetaKB database.

        $ metakb load files path/to/file1.json path/to/file2.json

    Note that the Neo4j database URL, username, and password can either be set by a CLI
    options, or by the environment variable METAKB_DB_URL. For example:

        $ metakb load files --db_url=bolt://username:password@localhost:7687 myfile.json
    """
    _confirm_remote(db_url, yes)
    start = timer()
    if not quiet:
        click.echo("Loading files into MetaKB database...")
    asyncio.run(_load_files(db_url, files, quiet))
    end = timer()
    _echo_info(
        f"Successfully loaded files into MetaKB database in {(end - start):.5f} s",
        quiet,
    )


async def _update(
    db_url: str,
    normalizer_db_url: str | None,
    refresh_source_caches: bool,
    sources: tuple[SourceName, ...],
    quiet: bool,
) -> None:
    """Update a source or sources from a sync click function"""
    _harvest_sources(sources, refresh_source_caches)
    await _transform_sources(sources, normalizer_db_url)

    start = timer()
    _echo_info("Loading Neo4j database...", quiet)

    if not sources:
        sources = tuple(SourceName)
    async with _get_repository(db_url) as repository:
        for src in sorted([s.value for s in sources]):
            pattern = f"{src}_cdm_*.json"
            globbed = (get_config().data_dir / src / "transformers").glob(pattern)

            try:
                path = sorted(globbed)[-1]
            except IndexError as e:
                msg = f"No valid transformation files found matching pattern: {pattern}"
                raise FileNotFoundError(msg) from e

            await load_from_json(path, repository, silent=quiet)

        end = timer()
        _echo_info(
            f"Successfully loaded neo4j database in {(end - start):.5f} s", quiet
        )


@cli.command()
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
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
    "sources",
    metavar=_print_enum_metavar(SourceName),
    type=click.Choice(list(SourceName), case_sensitive=False),
    nargs=-1,
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output.")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts.")
async def update(
    db_url: str,
    normalizer_db_url: str | None,
    refresh_source_caches: bool,
    sources: tuple[SourceName, ...],
    quiet: bool,
    yes: bool,
) -> None:
    """Execute data harvest and transformation from resources and upload to graph
    datastore.

    To harvest and transform source data into fresh CDM files, and then load them to
    the graph:

        $ metakb update

    Note that the Neo4j database URL, username, and password can either be set by a CLI
    options, or by the environment variable METAKB_DB_URL. For example:

        $ metakb update --db_url=bolt://username:password@localhost:7687

    Provide one or more SOURCE arguments to limit data harvest and transformation to
    just those source(s):

        $ metakb update moa

    \f
    :param db_url: connection string for the application Neo4j database.
    :param normalizer_db_url: URL endpoint of normalizers DynamoDB database. If not
        given, defaults to the configuration rules of the individual normalizers.
    :param refresh_source_caches: ``True`` if source caches, i.e. CIViCPy, should be
        refreshed before loading data. Note this will take several minutes. Defaults to
        ``False``.
    :param sources: source name(s) to update. If empty, update all sources.
    """  # noqa: D301
    _confirm_remote(db_url, yes)
    asyncio.run(
        _update(db_url, normalizer_db_url, refresh_source_caches, sources, quiet=quiet)
    )


def _harvest_sources(
    sources: tuple[SourceName, ...],
    refresh_cache: bool,
) -> None:
    """Run harvesting procedure for all sources.

    :param sources: specific names of sources to harvest (harvest all if empty)
    :param refresh_cache: if ``False``, use cached source data if available. Otherwise,
        invalidate cache.
    """
    _echo_info("Harvesting sources...")
    harvester_sources = {
        SourceName.CIVIC: CivicHarvester,
        SourceName.MOA: MoaHarvester,
        SourceName.FDA_PODA: FdaPodaHarvester,
        SourceName.CBIOPORTAL: CBioPortalHarvester,
        SourceName.MCI: MciHarvester,
    }
    if sources:
        harvester_sources = {k: v for k, v in harvester_sources.items() if k in sources}
    total_start = timer()
    fetch_mode = FetchMode.FORCE_REFRESH if refresh_cache else FetchMode.CHECK_STALE

    for name, source_class in harvester_sources.items():
        _echo_info(f"Harvesting {name.as_print_case()}...")
        start = timer()
        data_dir = SourceDataStore(src_name=name)
        source: Harvester = source_class(data_dir)
        source.harvest(fetch_mode)
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
) -> None:
    """Transform an individual source.

    :param source: name of source
    :param normalizer_handler: container for normalizer access
    :param harvest_file: path to input file (if empty, transformer will use default location)
    """
    transformer_sources = {
        SourceName.CIVIC: CivicTransformer,
        SourceName.MOA: MoaTransformer,
        SourceName.FDA_PODA: FdaPodaTransformer,
        SourceName.MCI: MciTransformer,
    }
    _echo_info(f"Transforming {source.as_print_case()}...")
    start = timer()
    src_data_store = SourceDataStore(src_name=source)
    transformer: CivicTransformer | MoaTransformer | FdaPodaTransformer = (
        transformer_sources[source](
            src_data_store=src_data_store, normalizers=normalizer_handler
        )
    )
    if not harvest_file:
        harvest_file = src_data_store.get_latest_harvested_file()
    transformed_data = await transformer.transform(harvest_file)
    end = timer()
    _echo_info(
        f"{source.as_print_case()} transformation finished in {(end - start):.2f} s."
    )
    src_data_store.save_cdm(transformed_data)


async def _transform_sources(
    sources: tuple[SourceName, ...],
    normalizer_db_url: str | None = None,
) -> None:
    """Run transformation procedure for all sources.

    :param sources: names of source(s) to transform
    :param normalizer_db_url: if given, attempt connection for all normalizers to this
        URL. Only works for DynamoDB data backends. Otherwise, fall back to
        specific normalizer env vars/defaults.
    """
    _echo_info("Transforming harvested data to CDM...")
    if not sources:
        sources = tuple(SourceName)
    normalizer_handler = await _get_preflighted_normalizers(normalizer_db_url)
    total_start = timer()
    for source in sources:
        await _transform_source(source, normalizer_handler)
    total_end = timer()
    _echo_info(
        f"Successfully transformed all sources to CDM in "
        f"{(total_end - total_start):.2f} s"
    )


@cli.group()
def snapshot() -> None:
    """Create and manage snapshots of MetaKB data."""


def _get_snapshot_dir() -> Path:
    snapshot_dir = get_config().data_dir / "snapshots"
    snapshot_dir.mkdir(exist_ok=True, parents=True)
    return snapshot_dir


async def _create_snapshot(db_url: str, file: Path | None, quiet: bool) -> None:
    if not file:
        snapshot_dir = _get_snapshot_dir()
        timestamp = datetime.now(UTC).strftime(SourceDataStore.TIMESTAMP_FMT)
        file = snapshot_dir / f"metakb_snapshot_{timestamp}.json"

    async with _get_repository(db_url) as repo:
        await save_db_snapshot(repo, file, quiet)


@snapshot.command("create")
@click.option("--db_url", "-u", default="", help=_neo4j_db_url_description)
@click.option(
    "--file",
    "-f",
    help="Destination path for the snapshot JSON file.",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output.")
def create_snapshot(db_url: str, quiet: bool, file: Path | None = None) -> None:
    """Create a MetaKB snapshot"""
    asyncio.run(_create_snapshot(db_url, file, quiet))


if __name__ == "__main__":
    cli()
