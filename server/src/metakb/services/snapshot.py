"""Provide tools for creating snapshots of stored data."""

import logging
from datetime import UTC, datetime
from pathlib import Path

import click
from ga4gh.va_spec.base import Statement
from pydantic import BaseModel
from tqdm import tqdm

from metakb import __version__ as metakb_version
from metakb.repository.base import AbstractRepository

_logger = logging.getLogger(__name__)


class DbSnapshotMeta(BaseModel):
    """Description of relevant snapshot metadata"""

    name: str = "metakb_snapshot"
    created_at: datetime = datetime.now(tz=UTC)
    metakb_version: str = metakb_version


class DbSnapshot(BaseModel):
    """Data snapshot for backing up and reloading metakb data"""

    assertions: list[Statement]
    meta: DbSnapshotMeta


class SnapshotError(RuntimeError):
    """Raised when a database snapshot cannot be generated due to inconsistent data."""


async def save_db_snapshot(
    repository: AbstractRepository, outfile_path: Path, silent: bool = True
) -> None:
    """Save a snapshot of the database to the specified location

    Retrieves all statement IDs from the repository, fetches each corresponding
    statement, and serializes the collection to ``outfile_path``. The output is
    intended as a portable snapshot of the database that can later be reloaded.

    :param repository: Repository from which to retrieve statements.
    :param outfile_path: Destination path for the JSON snapshot.
    :param silent: If ``False``, emit progress messages to stdout in addition to
        the application logger.

    :raise SnapshotError: If a statement ID returned by the repository cannot be
        retrieved, indicating that the repository is in an inconsistent state.
    :raise OSError: If the output file cannot be written.
    """
    msg = "Creating DB snapshot..."
    _logger.info(msg)
    if not silent:
        click.echo(msg)

    assertion_ids = await repository.get_all_assertion_ids()
    assertions: list[Statement] = []
    for assertion_id in tqdm(assertion_ids, disable=silent):
        assertion = await repository.get_statement(assertion_id)
        if not assertion:
            msg = f"Unable to retrieve assertion for expected ID {assertion_id}"
            raise SnapshotError(msg)
        assertions.append(assertion)
    snapshot = DbSnapshot(assertions=assertions, meta=DbSnapshotMeta())
    with outfile_path.open("w") as f:
        f.write(snapshot.model_dump_json(exclude_none=True, indent=2))
