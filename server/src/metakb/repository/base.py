"""Declare base repository interface + associated helper functions."""

import abc
import logging

from ga4gh.core.models import Extension, MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    ConditionSet,
    Statement,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)

from metakb.transformers.base import TransformedData

_logger = logging.getLogger(__name__)


class AbstractRepository(abc.ABC):
    """Abstract definition of a repository class.

    Used to access and store core MetaKB data.
    """

    @abc.abstractmethod
    def search_statements(
        self,
        variation_id: str | None = None,
        gene_id: str | None = None,
        therapy_id: str | None = None,
        disease_id: str | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        """Perform entity-based search over all statements.

        Return all statements matching all provided entity parameters.

        Probable future changes
        * Search by list of entities
        * Combo-therapy specific search

        :param variation_id: GA4GH variation ID
        :param gene_id: normalized gene ID
        :param therapy_id: normalized drug ID
        :param disease_id: normalized condition ID
        :param start: page start
        :param limit: length of page
        :return: list of matching statements
        """

    @abc.abstractmethod
    def add_transformed_data(self, data: TransformedData) -> None:
        """Add a chunk of transformed data to the database.

        :param data: data grouped by GKS entity type
        """

    @abc.abstractmethod
    def teardown_db(self) -> None:
        """Reset repository storage."""


def _has_normalize_failure(extensions: list[Extension] | None) -> bool:
    """Check if extensions contain indication of normalization failure

    :param extensions: list of extensions from an entity object
    :return: True if contains normalize failure
    """
    if extensions:
        for extension in extensions:
            if extension.name == "vicc_normalizer_failure" and extension.value:
                return True
    return False


def _is_loadable_condition(
    condition: MappableConcept | ConditionSet, statement_id: str
) -> bool:
    """Check if condition or condition set can be loaded into DB

    :param condition: condition or conditionset to check
    :param statement_id: ID to use in logging failure message
    :return: whether condition is loadable
    :raise ValueError: if unsupported type of condition (eg IRI ref) is provided
    """
    if isinstance(condition, MappableConcept):
        if _has_normalize_failure(condition.extensions):
            _logger.info(
                "%s could not be loaded because condition failed to normalize: %s",
                statement_id,
                condition,
            )
            return False
    elif isinstance(condition, ConditionSet):
        for member_condition in condition.conditions:
            if _has_normalize_failure(member_condition.extensions):
                _logger.info(
                    "%s could not be loaded because condition in ConditionSet failed to normalize: %s",
                    statement_id,
                    condition,
                )
                return False
    else:
        raise ValueError  # noqa: TRY004
    return True


def is_loadable_statement(statement: Statement) -> bool:
    """Check whether statement can be loaded to DB

    * All entity terms need to have normalized
    * For variations, that means the catvar must have a constraint
    * For StudyStatements that are supported by other statements via evidence lines,
        all supporting statements must be loadable for the overarching StudyStatement
        to be loadable

    :param statement: incoming statement from CDM. All parameters must be fully materialized,
        not simply referenced as IRIs
    :return: whether statement can be loaded given current data support policy
    :raise NotImplementedError: if unsupported proposition type is provided
    :raise ValueError: if unsupported type used for therapeutic (eg string IRI)
    """
    success = True
    if evidence_lines := statement.hasEvidenceLines:
        for evidence_line in evidence_lines:
            for evidence_item in evidence_line.hasEvidenceItems:
                if not is_loadable_statement(evidence_item):
                    _logger.info(
                        "%s could not be loaded because %s is not supported",
                        statement.id,
                        evidence_item.id,
                    )
                    success = False
    proposition = statement.proposition
    if not proposition.subjectVariant.constraints:
        _logger.info(
            "%s could not be loaded because subject variant object lacks constraints: %s",
            statement.id,
            proposition.subjectVariant,
        )
        success = False
    if isinstance(proposition, VariantTherapeuticResponseProposition):
        if not _is_loadable_condition(
            proposition.conditionQualifier.root, statement.id
        ):
            success = False
        therapeutic = proposition.objectTherapeutic.root
        if isinstance(therapeutic, MappableConcept):
            if _has_normalize_failure(therapeutic.extensions):
                _logger.info(
                    "%s could not be loaded because drug failed to normalize: %s",
                    statement.id,
                    therapeutic,
                )
                success = False
        elif isinstance(therapeutic, TherapyGroup):
            for drug in therapeutic.therapies:
                if _has_normalize_failure(drug.extensions):
                    _logger.info(
                        "%s could not be loaded because drug in therapygroup failed to normalize: %s",
                        statement.id,
                        drug,
                    )
                    success = False
        else:
            raise ValueError  # noqa: TRY004
    elif isinstance(
        proposition, VariantDiagnosticProposition | VariantPrognosticProposition
    ):
        if not _is_loadable_condition(proposition.objectCondition.root, statement.id):
            success = False
    else:
        msg = f"Unsupported proposition type: {proposition.type}"
        raise NotImplementedError(msg)
    if proposition.geneContextQualifier and _has_normalize_failure(
        proposition.geneContextQualifier.extensions
    ):
        _logger.info(
            "%s could not be loaded because gene failed to normalize: %s",
            statement.id,
            proposition.geneContextQualifier,
        )
        success = False
    if success:
        _logger.info("Success. %s can be loaded.", statement.id)
    else:
        _logger.info("Failure. %s cannot be loaded.", statement.id)
    return success
