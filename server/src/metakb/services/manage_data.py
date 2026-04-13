"""Load and manage data for the database."""

import json
import logging
from pathlib import Path

import asyncclick as click
from tqdm import tqdm

from metakb.repository.base import AbstractRepository
from metakb.transformers.base import TransformedData
from metakb.transformers.methodology import merge_assertions

_logger = logging.getLogger(__name__)


def load_from_json(
    src_transformed_cdm: Path, repository: AbstractRepository, silent: bool = True
) -> None:
    """Load assertions and evidence into DB from given CDM JSON file.

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
        loaded_stmt_count = 0
        for assertion in tqdm(data.assertions, disable=silent):
            if existing_assertion := repository.get_statement(assertion.id):
                # MUST pass the existing assertion as the first arg to ensure
                # IDs remain consistent
                assertion = merge_assertions(existing_assertion, assertion)  # noqa: PLW2901
            repository.load_assertion(assertion)
            loaded_stmt_count += 1

    _logger.info("Successfully loaded %s statements.", loaded_stmt_count)
