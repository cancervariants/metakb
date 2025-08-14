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


def prune_transformed_data(data: TransformedData) -> TransformedData:
    """Remove unused entitites from data collection.

    Data transformation tries to collect all entities (e.g. genes, therapies, diseases)
    provided by a source, but we only want to import a statement if our data model supports
    every one of its components, and we don't want to import an entity unless it is
    connected to at least one imported statement.
    """
    raise NotImplementedError


class AbstractRepository(abc.ABC):
    """Abstract definition of a repository class.

    Used to access and store core MetaKB data.
    """

    def get_statement(
        self, statement_id: str
    ) -> (
        Statement
        | VariantDiagnosticStudyStatement
        | VariantPrognosticStudyStatement
        | VariantTherapeuticResponseStudyStatement
    ):
        """Given a single statement ID, get it back.

        :param statement_id: the ID of a statement
        :raise KeyError: if unable to retrieve it
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def add_transformed_data(self, data: TransformedData) -> None:
        """Add a chunk of transformed data to the database.

        :param data: data grouped by GKS entity type
        """
        data = prune_transformed_data(data)
        # TODO prune unused stuff
        # TODO some kind of session/transaction logic
        for catvar in data.categorical_variants:
            self.add_catvar(catvar)
        for document in data.documents:
            self.add_document(document)
        for method in data.methods:
            self.add_method(method)
        for gene in data.genes:
            self.add_gene(gene)
        for condition in data.conditions:
            self.add_condition(condition)
        for therapy in data.therapies:
            self.add_therapy(therapy)
        for evidence in data.statements_evidence:
            self.add_evidence(evidence)
        for assertion in data.statements_assertions:
            self.add_assertion(assertion)

    def add_catvar(self, catvar: CategoricalVariant) -> None:
        raise NotImplementedError

    def add_document(self, document: Document) -> None:
        raise NotImplementedError

    def add_method(self, method: Method) -> None:
        raise NotImplementedError

    def add_gene(
        self,
        gene: MappableConcept,  # TODO double check
    ) -> None:
        raise NotImplementedError

    def add_condition(self, condition: MappableConcept) -> None:
        raise NotImplementedError

    def add_therapy(
        self, therapy: MappableConcept | TherapyGroup
    ) -> None:  # TODO double check
        raise NotImplementedError

    # add statement evidence assertions
    def add_evidence(self, evidence) -> None:
        raise NotImplementedError

    def add_assertion(self, assertion) -> None:
        raise NotImplementedError
