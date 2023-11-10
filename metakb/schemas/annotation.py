"""Module containing GK pilot annotation definitions"""
from datetime import datetime
from enum import StrEnum
from typing import Dict, List, Literal, Optional, Union

from ga4gh.core import core_models
from pydantic import Field, StrictInt, StrictStr, constr, field_validator


class AgentSubtype(StrEnum):
    """Define constraints for agent subtype"""

    PERSON = "person"
    ORGANIZATION = "organization"
    COMPUTER = "computer"


class Direction(StrEnum):
    """Define constraints for direction"""

    SUPPORTS = "supports"
    REFUTES = "refutes"
    NONE = "none"


class Document(core_models._MappableEntity):
    """a representation of a physical or digital document"""

    type: Literal["Document"] = "Document"
    title: Optional[StrictStr] = Field(None, description="The title of the Document")
    url: Optional[constr(pattern=r"^(https?|s?ftp)://")] = Field(  # noqa: F722
        None, description="A URL at which the document may be retrieved."
    )
    doi: Optional[
        constr(pattern=r"^10.(\d+)(\.\d+)*\/[\w\-\.]+")  # noqa: F722
    ] = Field(
        None,
        description="A `Digital Object Identifier <https://www.doi.org/the-identifier/what-is-a-doi/>_` for the document.",  # noqa: E501
    )
    pmid: Optional[StrictInt] = Field(
        None,
        description="A `PubMed unique identifier <https://en.wikipedia.org/wiki/PubMed#PubMed_identifier>`_.",  # noqa: E501
    )


class Method(core_models._Entity):
    """A set of instructions that specify how to achieve some objective (e.g.
    experimental protocols, curation guidelines, rule sets, etc.)
    """

    type: Literal["Method"] = Field("Method", description="MUST be 'Method'.")
    isReportedIn: Optional[Union[Document, core_models.IRI]] = Field(
        None, description="A document in which the information content is expressed."
    )
    subtype: Optional[core_models.Coding] = Field(
        None,
        description="A more specific type of entity the method represents (e.g. Variant Interpretation Guideline, Experimental Protocol)",  # noqa: E501
    )


class Agent(core_models._Entity):
    """An autonomous actor (person, organization, or computational agent) that bears
    some form of responsibility for an activity taking place, for the existence of an
    entity, or for another agent's activity.
    """

    type: Literal["Agent"] = Field("Agent", description="MUST be 'Agent'.")
    name: Optional[StrictStr] = None
    subtype: Optional[AgentSubtype] = None


class Contribution(core_models._Entity):
    """The sum of all actions taken by a single agent in contributing to the creation,
    modification, assessment, or deprecation of a particular entity (e.g. a Statement,
    EvidenceLine, DataItem, Publication, etc.)
    """

    type: Literal["Contribution"] = "Contribution"
    contributor: Optional[Agent] = None
    date: Optional[StrictStr] = None
    activity: Optional[core_models.Coding] = Field(
        None,
        description="SHOULD describe a concept descending from the Contributor Role Ontology.",  # noqa: E501
    )

    @field_validator("date")
    @classmethod
    def date_format(cls, v: Optional[str]) -> Optional[str]:
        """Check that date is YYYY-MM-DD format"""
        if v:
            valid_format = "%Y-%m-%d"

            try:
                datetime.strptime(v, valid_format).strftime(valid_format)
            except ValueError:
                raise ValueError("`date` must use YYYY-MM-DD format")

        return v


class InformationEntity(core_models._Entity):
    """InformationEntities are abstract (non-physical) entities that are about something
    (i.e. they carry information about things in the real world).
    """

    type: StrictStr
    specifiedBy: Optional[Union[Method, core_models.IRI]] = Field(
        None,
        description="A `Method` that describes all or part of the process through which the information was generated.",  # noqa: E501
    )
    contributions: Optional[List[Contribution]] = None
    isReportedIn: Optional[List[Union[Document, core_models.IRI]]] = Field(
        None, description="A document in which the information content is expressed."
    )
    # recordMetadata (might be added in the future)


class DataItem(InformationEntity):
    """An InformationEntity representing an individual piece of data, generated/acquired
    through methods which reliably produce truthful information about something.
    """

    type: Literal["DataItem"] = Field("DataItem", description="MUST be 'DataItem'.")
    subtype: Optional[core_models.Coding] = Field(
        None,
        description="A specific type of data the DataItem object represents (e.g. a specimen count, a patient weight, an allele frequency, a p-value, a confidence score)",  # noqa: E501
    )
    value: StrictStr
    unit: Optional[core_models.Coding] = None


class _StatementBase(InformationEntity):
    """Base class for Statement model. Excludes fields that get extended with a
    different name in child classes (subject, object, qualifiers)
    """

    predicate: Optional[StrictStr] = Field(
        None, description="The predicate of the Statement"
    )
    direction: Direction = Field(
        ..., description="direction of this Statement with respect to the predicate."
    )
    strength: Optional[Union[core_models.Coding, core_models.IRI]] = Field(
        None,
        description="The overall strength of support for the Statement based on all evidence assessed.",  # noqa: E501
    )


class Statement(_StatementBase):
    """A Statement (aka `Assertion`) represents a claim of purported truth as made by a
    particular agent, on a particular occasion.
    """

    subject: StrictStr = Field(..., description="The subject of the Statement.")
    object: Optional[StrictStr] = Field(None, description="The object of the Statement")
    qualifiers: Optional[Dict] = Field(
        None,
        description="Additional, optional properties that may qualify the Statement.",
    )
