"""Declare base repository interface + associated helper functions."""

import abc
import logging

from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
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
    """
    success = True
    if evidence_lines := statement.hasEvidenceLines:
        for evidence_line in evidence_lines:
            for evidence_item in evidence_line.hasEvidenceItems:
                if not is_loadable_statement(evidence_item):
                    _logger.debug(
                        "%s could not be loaded because %s is not supported",
                        statement.id,
                        evidence_item.id,
                    )
                    success = False
    proposition = statement.proposition
    if not proposition.subjectVariant.constraints:
        _logger.debug(
            "%s could not be loaded because subject variant object lacks constraints: %s",
            statement.id,
            proposition.subjectVariant,
        )
        success = False
    match proposition:
        case VariantTherapeuticResponseProposition():
            if extensions := proposition.conditionQualifier.root.extensions:
                for extension in extensions:
                    if extension.name == "vicc_normalizer_failure" and extension.value:
                        _logger.debug(
                            "%s could not be loaded because condition failed to normalize: %s",
                            statement.id,
                            proposition.conditionQualifier.root,
                        )
                        success = False
            if therapeutic := proposition.objectTherapeutic:
                if isinstance(therapeutic.root, MappableConcept):
                    if extensions := therapeutic.root.extensions:
                        for extension in extensions:
                            if (
                                extension.name == "vicc_normalizer_failure"
                                and extension.value
                            ):
                                _logger.debug(
                                    "%s could not be loaded because drug failed to normalize: %s",
                                    statement.id,
                                    therapeutic.root,
                                )
                                success = False
                elif isinstance(therapeutic.root, TherapyGroup):
                    for drug in therapeutic.root.therapies:
                        if extensions := drug.extensions:
                            for extension in extensions:
                                if (
                                    extension.name == "vicc_normalizer_failure"
                                    and extension.value
                                ):
                                    _logger.debug(
                                        "%s could not be loaded because drug in therapygroup failed to normalize: %s",
                                        statement.id,
                                        drug,
                                    )
                                    success = False
                else:
                    raise TypeError
        case VariantDiagnosticProposition() | VariantPrognosticProposition():
            if extensions := proposition.objectCondition.root.extensions:
                for extension in extensions:
                    if extension.name == "vicc_normalizer_failure" and extension.value:
                        _logger.debug(
                            "%s could not be loaded because condition failed to normalize: %s",
                            statement.id,
                            proposition.objectCondition.root,
                        )
                        success = False
        case _:
            msg = f"Unsupported proposition type: {proposition.type}"
            raise NotImplementedError(msg)
    if proposition.geneContextQualifier:  # noqa: SIM102
        if gene_extensions := proposition.geneContextQualifier.extensions:
            for extension in gene_extensions:
                if extension.name == "vicc_normalizer_failure" and extension.value:
                    _logger.debug(
                        "%s could not be loaded because gene failed to normalize: %s",
                        statement.id,
                        proposition.geneContextQualifier,
                    )
                    success = False
    if success:
        _logger.debug("Success. %s can be loaded.", statement.id)
    else:
        _logger.debug("Failure. %s cannot be loaded.", statement.id)
    return success
