"""Load and manage data for the database."""

import json
import logging
from pathlib import Path

import asyncclick as click
from ga4gh.va_spec.base import Statement
from tqdm import tqdm

from metakb.repository.base import AbstractRepository

# from metakb.transformers.methodology import merge_assertions

_logger = logging.getLogger(__name__)


SUPPORTED_CATVAR_CONSTRAINTS = {"DefiningAlleleConstraint", "FeatureContextConstraint"}


def is_loadable_assertion(statement: Statement) -> bool:
    """Check whether an assertion can be loaded to DB

    Requirements:

    * Must be a higher-order (MetaKB) assertion
    * Double-check that entity terms are of supported types/structures
       * Categorical variant contains exactly 1 constraint

    :param statement: incoming statement from CDM. All parameters must be fully materialized,
        not simply referenced as IRIs
    :return: whether statement can be loaded given current data support policy
    :raise NotImplementedError: if unsupported proposition type is provided
    :raise ValueError: if unrecognized type used for therapeutic (eg string IRI)
    """
    success = True

    if not statement.id.startswith("metakb.assertion"):
        _logger.debug(
            "%s could not be loaded because it's not a MetaKB assertion", statement.id
        )
        success = False
    proposition = statement.proposition
    constraints = proposition.subjectVariant.constraints
    if not constraints:
        _logger.debug(
            "%s could not be loaded because assertion subject variant lacks constraints: %s",
            statement.id,
            proposition.subjectVariant,
        )
        success = False
    else:
        if len(constraints) != 1:
            _logger.debug(
                "%s could not be loaded because it contains more than 1 constraint: %s",
                statement.id,
                constraints,
            )
            success = False
        if constraints[0].root.type not in SUPPORTED_CATVAR_CONSTRAINTS:
            _logger.debug(
                "%s could not be loaded because it doesn't use a supported constraint type: %s",
                statement.id,
                constraints,
            )
            success = False
    if success:
        _logger.info("Success. %s can be loaded.", statement.id)
    else:
        _logger.info("Failure. %s cannot be loaded.", statement.id)
    return success


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
        statements = [Statement(**i) for i in dumped_data.get("statements", [])]
        loaded_stmt_count = 0
        for statement in tqdm(statements, disable=silent):
            if not is_loadable_assertion(statement):
                continue
            _check_for_assertion_updates(statement, repository)
            add_statement(statement, repository)
            loaded_stmt_count += 1

    _logger.info("Successfully loaded %s statements.", loaded_stmt_count)
