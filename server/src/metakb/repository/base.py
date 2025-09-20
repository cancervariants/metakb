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
        variation_id: str | None = None,
        gene_id: str | None = None,
        therapy_id: str | None = None,
        disease_id: str | None = None,
        statement_id: str | None = None,
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
    def load_statement(self, statement: Statement) -> None:
        """Load individual statement, and contained entities, into DB

        :param statement: statement to load
        """

    @abc.abstractmethod
    def teardown_db(self) -> None:
        """Reset repository storage."""
