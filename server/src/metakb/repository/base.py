"""Declare base repository interface + associated helper functions."""

import abc

from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Statement,
)


class AbstractRepository(abc.ABC):
    """Abstract definition of a repository class.

    Used to access and store core MetaKB data.
    """

    @abc.abstractmethod
    def get_statement(
        self, statement_id: str
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
        | None
    ):
        """Retrieve a statement

        :param statement_id: ID of the statement minted by the source
        :return: complete statement if available
        """

    @abc.abstractmethod
    def search_statements(
        self,
        variation_ids: list[str] | None = None,
        gene_ids: list[str] | None = None,
        therapy_ids: list[str] | None = None,
        disease_ids: list[str] | None = None,
        statement_ids: list[str] | None = None,
        start: int = 0,
        limit: int | None = None,
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        """Perform entity-based search over all statements.

        Return all statements matching any item within a given list of entity IDs.

        IE: Given a list for [DrugA, DrugB] and [GeneA, GeneB], return all statements
        that involve both one of the two given drugs AND one of the two given genes.

        Probable future changes
        * Combo-therapy specific search
        * Specific logic for searching diseases/conditionsets
        * Search on source values rather than normalized values

        todo update description
        """

    @abc.abstractmethod
    def load_statement(self, statement: Statement) -> None:
        """Load individual statement, and contained entities, into DB

        :param statement: statement to load
        """

    @abc.abstractmethod
    def teardown_db(self) -> None:
        """Reset repository storage."""
