"""Load and manage data for the database."""

import json
import logging
from pathlib import Path

import asyncclick as click
from ga4gh.va_spec.base import Statement
from tqdm import tqdm

from metakb.repository.base import AbstractRepository
from metakb.transformers.base import TransformedData

# from metakb.transformers.methodology import merge_assertions

_logger = logging.getLogger(__name__)


def add_statement(statement: Statement, repository: AbstractRepository) -> None:
    """Load a GKS statement to the repository

    If it's a higher-order claim -- ie it's supported by additional evidence -- load those
    items first.

    :param statement: incoming statement. Assumed valid -- check for supportedness beforehand.
    :param repository: data repository instance
    """
    if statement.hasEvidenceLines:
        for line in statement.hasEvidenceLines:
            for item in line.hasEvidenceItems:
                add_statement(item, repository)
    repository.load_statement(statement)


def _check_for_assertion_updates(
    assertion: Statement, repository: AbstractRepository
) -> None:
    db_assertion = repository.get_statement(assertion.id)
    if not db_assertion:
        return
    # update assertion in place with newly-aggregated evidence and derived fields
    merge_assertions(assertion, db_assertion)
    repository.update_assertion_strength(assertion.id, assertion.strength)
    repository.update_assertion_properties(
        assertion.id,
        assertion.direction,
        assertion.extensions,
    )


def load_from_json(
    src_transformed_cdm: Path, repository: AbstractRepository, silent: bool = True
) -> None:
    """Load evidence into DB from given CDM JSON file.

    Iterate through the provided statements. If a statement looks like a MetaKB assertion,
    then try to load

    1. all constituent evidence items, recursively
    2. the assertion itself

    :param src_transformed_cdm: path to file for a source's transformed data to
        common data model containing statements, variation, therapies, conditions,
        genes, methods, documents, etc.
    :param repository: data repository instance
    :param silent: whether to suppress printing to console
    """
    _logger.info("Loading data from %s", src_transformed_cdm)
    if not silent:
        click.echo(f"Loading {src_transformed_cdm}")
    with src_transformed_cdm.open() as f:
        dumped_data = json.load(f)
        data = TransformedData(**dumped_data)
        for assertion in tqdm(data.assertions, disable=silent):
            _check_for_assertion_updates(assertion, repository)
            add_statement(statement, repository)
            loaded_stmt_count += 1

    _logger.info("Successfully loaded %s statements.", loaded_stmt_count)
