"""Declare base repository interface + associated helper functions."""

import abc

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Document, Method, Statement, TherapyGroup

from metakb.transformers.base import TransformedData


class AbstractRepository(abc.ABC):
    """Abstract definition of a repository class.

    Used to access and store core MetaKB data.
    """

    @abc.abstractmethod
    def get_statements(
        self,
        statement_ids: list[str],
    ) -> list[
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ]:
        """Retrieve statements for the corresponding statement IDs.

        :param statement_ids: the IDs of a statement
        :return: list of statements for which retrieval was successful
        """

    @abc.abstractmethod
    def search_statements(
        self,
        statement_id: str | None = None,
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
        """TODO describe this"""

    @abc.abstractmethod
    def add_transformed_data(self, data: TransformedData) -> None:
        """Add a chunk of transformed data to the database.

        :param data: data grouped by GKS entity type
        """

    @abc.abstractmethod
    def teardown_db(self) -> None:
        """Reset repository storage."""
