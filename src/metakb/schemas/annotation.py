"""Module containing GK pilot annotation definitions"""

import datetime
from enum import Enum
from typing import Literal

from ga4gh.core import core_models
from pydantic import Field, StrictInt, StrictStr, constr, field_validator


class AgentSubtype(str, Enum):
    """Define constraints for agent subtype"""

    PERSON = "person"
    ORGANIZATION = "organization"
    COMPUTER = "computer"


class Direction(str, Enum):
    """Define constraints for direction"""

    SUPPORTS = "supports"
    REFUTES = "refutes"
    NONE = "none"


class Document(core_models._MappableEntity):  # noqa: SLF001
    """a representation of a physical or digital document"""

    type: Literal["Document"] = "Document"
    title: StrictStr | None = Field(None, description="The title of the Document")
    url: constr(pattern="^(https?|s?ftp)://") | None = Field(
        None, description="A URL at which the document may be retrieved."
    )
    doi: constr(pattern="^10.(\\d+)(\\.\\d+)*\\/[\\w\\-\\.]+") | None = Field(
        None,
        description="A `Digital Object Identifier <https://www.doi.org/the-identifier/what-is-a-doi/>_` for the document.",
    )
    pmid: StrictInt | None = Field(
        None,
        description="A `PubMed unique identifier <https://en.wikipedia.org/wiki/PubMed#PubMed_identifier>`_.",
    )


class Method(core_models._Entity):  # noqa: SLF001
    """A set of instructions that specify how to achieve some objective (e.g.
    experimental protocols, curation guidelines, rule sets, etc.)
    """

    type: Literal["Method"] = Field("Method", description="MUST be 'Method'.")
    isReportedIn: Document | core_models.IRI | None = Field(
        None, description="A document in which the information content is expressed."
    )
    subtype: core_models.Coding | None = Field(
        None,
        description="A more specific type of entity the method represents (e.g. Variant Interpretation Guideline, Experimental Protocol)",
    )


class Agent(core_models._Entity):  # noqa: SLF001
    """An autonomous actor (person, organization, or computational agent) that bears
    some form of responsibility for an activity taking place, for the existence of an
    entity, or for another agent's activity.
    """

    type: Literal["Agent"] = Field("Agent", description="MUST be 'Agent'.")
    name: StrictStr | None = None
    subtype: AgentSubtype | None = None


class Contribution(core_models._Entity):  # noqa: SLF001
    """The sum of all actions taken by a single agent in contributing to the creation,
    modification, assessment, or deprecation of a particular entity (e.g. a Statement,
    EvidenceLine, DataItem, Publication, etc.)
    """

    type: Literal["Contribution"] = "Contribution"
    contributor: Agent | None = None
    date: StrictStr | None = None
    activity: core_models.Coding | None = Field(
        None,
        description="SHOULD describe a concept descending from the Contributor Role Ontology.",
    )

    @field_validator("date")
    @classmethod
    def date_format(cls, v: str | None) -> str | None:
        """Check that date is YYYY-MM-DD format"""
        if v:
            valid_format = "%Y-%m-%d"

            try:
                datetime.datetime.strptime(v, valid_format).replace(
                    tzinfo=datetime.timezone.utc
                ).strftime(valid_format)
            except ValueError as e:
                msg = "`date` must use YYYY-MM-DD format"
                raise ValueError(msg) from e
        return v


class _InformationEntity(core_models._Entity):  # noqa: SLF001
    """InformationEntities are abstract (non-physical) entities that are about something
    (i.e. they carry information about things in the real world).
    """

    id: StrictStr
    type: StrictStr
    specifiedBy: Method | core_models.IRI | None = Field(
        None,
        description="A `Method` that describes all or part of the process through which the information was generated.",
    )
    contributions: list[Contribution] | None = None
    isReportedIn: list[Document | core_models.IRI] | None = Field(
        None, description="A document in which the information content is expressed."
    )
    # recordMetadata (might be added in the future)


class DataItem(_InformationEntity):
    """An InformationEntity representing an individual piece of data, generated/acquired
    through methods which reliably produce truthful information about something.
    """

    type: Literal["DataItem"] = Field("DataItem", description="MUST be 'DataItem'.")
    subtype: core_models.Coding | None = Field(
        None,
        description="A specific type of data the DataItem object represents (e.g. a specimen count, a patient weight, an allele frequency, a p-value, a confidence score)",
    )
    value: StrictStr
    unit: core_models.Coding | None = None


class _StatementBase(_InformationEntity):
    """Base class for Statement model. Excludes fields that get extended with a
    different name in child classes (subject, object, qualifiers)
    """

    predicate: StrictStr | None = Field(
        None, description="The predicate of the Statement"
    )
    direction: Direction = Field(
        ..., description="direction of this Statement with respect to the predicate."
    )
    strength: core_models.Coding | core_models.IRI | None = Field(
        None,
        description="The overall strength of support for the Statement based on all evidence assessed.",
    )


class _Statement(_StatementBase):
    """A Statement (aka `Assertion`) represents a claim of purported truth as made by a
    particular agent, on a particular occasion.
    """

    subject: StrictStr = Field(..., description="The subject of the Statement.")
    object: StrictStr | None = Field(None, description="The object of the Statement")
    qualifiers: dict | None = Field(
        None,
        description="Additional, optional properties that may qualify the Statement.",
    )
