"""Load and manage data for the database."""

import json
import logging
from pathlib import Path

import asyncclick as click
from ga4gh.va_spec.base import EvidenceLine, Statement
from tqdm import tqdm

from metakb.repository.base import AbstractRepository
from metakb.transformers.base import TransformedData
from metakb.transformers.methodology import (
    add_evidence_to_assertion,
    initialize_assertion,
)

_logger = logging.getLogger(__name__)


def _add_evidence_line(ev_line: EvidenceLine, repository: AbstractRepository) -> None:
    if ev_line.hasEvidenceItems is None:
        msg = f"Encountered evidence line with no evidence: {ev_line}"
        _logger.error(msg)
        raise ValueError(msg)
    for item in ev_line.hasEvidenceItems:
        if isinstance(item, EvidenceLine):
            _add_evidence_line(item, repository)
        elif isinstance(item, Statement):
            _add_statement(item, repository)
        else:
            msg = f"Encountered unexpected type of ev item: {item} in {ev_line.id=}"
            _logger.error(msg)
            raise TypeError(msg)
    repository.load_evidence_line(ev_line, repository)


def _add_statement(statement: Statement, repository: AbstractRepository) -> None:
    """Load a GKS statement to the repository

    If it's a higher-order claim -- ie it's supported by additional evidence -- load those
    items first.

    :param statement: incoming statement. Assumed valid -- check for supportedness beforehand.
    :param repository: data repository instance
    """
    if statement.hasEvidenceLines:
        for line in statement.hasEvidenceLines:
            _add_evidence_line(line)
            # for item in line.hasEvidenceItems:
            #     add_statement(item, repository)
            # repository.load_evidence_line(line)
    repository.load_statement(statement)


def _update_existing_assertion(
    assertion: Statement, repository: AbstractRepository
) -> Statement | None:
    db_assertion = repository.get_statement(assertion.id)
    if not db_assertion:
        return None

    existing_ev_items = get_ev_from_assertion(db_assertion)
    new_ev_items = get_ev_from_assertion(assertion)
    all_ev = combine_ev(existing_ev_items, new_ev_items)

    new_assertion = initialize_assertion(
        db_assertion.id, db_assertion.proposition, all_ev[0]
    )
    for ev_item in all_ev[1:]:
        add_evidence_to_assertion(new_assertion, ev_item)


#     # update assertion in place with newly-aggregated evidence and derived fields
#     db_assertion = add
#     merge_assertions(assertion, db_assertion)
#     repository.update_assertion_strength(assertion.id, assertion.strength)
#     repository.update_assertion_properties(
#         assertion.id,
#         assertion.direction,
#         assertion.extensions,
#     )
#     return assertion


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
            """
            * get previous copy of assertion
            *
            """
            if _update_existing_assertion(assertion, repository):
                repository
                # wipe
                pass  # do update existing stuff
            # _check_for_assertion_updates(assertion, repository)
            # add_statement(statement, repository)
            # loaded_stmt_count += 1

    _logger.info("Successfully loaded %s statements.", loaded_stmt_count)
