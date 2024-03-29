"""Module containing GA4GH categorical variation definitions"""
from enum import StrEnum
from typing import List, Literal, Optional, Union

from ga4gh.core import core_models
from ga4gh.vrs import models
from pydantic import Field, RootModel, StrictStr


class LocationMatchCharacteristic(StrEnum):
    """The characteristics of a valid match between a contextual CNV location (the
    query) and the Categorical CNV location (the domain), when both query and domain are
    represented on the same  reference sequence. An `exact` match requires the location
    of the query and domain to be identical. A `subinterval` match requires the query to
    be a subinterval of the domain. A `superinterval` match requires the query to be a
    superinterval of the domain. A `partial` match requires at least 1 residue of
    between the query and domain.
    """

    EXACT = "exact"
    PARTIAL = "partial"
    SUBINTERVAL = "subinterval"
    SUPERINTERVAL = "superinterval"


class _CategoricalVariationBase(core_models._DomainEntity):
    """Base class for Categorical Variation"""

    members: Optional[List[Union[models.Variation, core_models.IRI]]] = Field(
        None,
        description="A non-exhaustive list of VRS variation contexts that satisfy the constraints of this categorical variant.",  # noqa: E501
    )


class ProteinSequenceConsequence(_CategoricalVariationBase):
    """A change that occurs in a protein sequence as a result of genomic changes. Due to
    the degenerate nature of the genetic code, there are often several genomic changes
    that can cause a protein sequence consequence. The protein sequence consequence,
    like a `CanonicalAllele`, is defined by an
    `Allele <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#variation>` that is
    representative of a collection of congruent Protein Alleles that share the same
    altered codon(s).
    """

    type: Literal["ProteinSequenceConsequence"] = Field(
        "ProteinSequenceConsequence",
        description="MUST be 'ProteinSequenceConsequence'.",
    )
    definingContext: Union[models.Allele, core_models.IRI] = Field(
        ...,
        description="The `VRS Allele <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#allele>`_  object that is congruent with (projects to the same codons) as alleles on other protein reference sequences.",  # noqa: E501
    )


class CanonicalAllele(_CategoricalVariationBase):
    """A canonical allele is defined by an
    `Allele <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#variation>` that is
    representative of a collection of congruent Alleles, each of which depict the same
    nucleic acid change on different underlying reference sequences. Congruent
    representations of an Allele often exist across different genome assemblies and
    associated cDNA transcript representations.
    """

    type: Literal["CanonicalAllele"] = Field(
        "CanonicalAllele", description="MUST be 'CanonicalAllele'."
    )
    definingContext: Union[models.Allele, core_models.IRI] = Field(
        ...,
        description="The `VRS Allele <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#allele>`_ object that is congruent with variants on alternate reference sequences.",  # noqa: E501
    )


class CategoricalCnv(_CategoricalVariationBase):
    """A categorical variation domain is defined first by a sequence derived from a
    canonical `Location <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#Location>`_ ,
    which is representative of a collection of congruent Locations. The change or count
    of this sequence is also described, either by a numeric value (e.g. "3 or more
    copies") or categorical representation (e.g. "high-level gain"). Categorical CNVs
    may optionally be defined by rules specifying the location match characteristics for
    member CNVs.
    """

    type: Literal["CategoricalCnv"] = Field(
        "CategoricalCnv", description="MUST be 'CategoricalCnv'."
    )
    location: models.Location = Field(
        ...,
        description="A `VRS Location <https://vrs.ga4gh.org/en/2.0/terms_and_model.html#location>`_ object that represents a sequence derived from that location, and is congruent with locations on alternate reference sequences.",  # noqa: E501
    )
    locationMatchCharacteristic: Optional[LocationMatchCharacteristic] = Field(
        None,
        description="The characteristics of a valid match between a contextual CNV location (the query) and the Categorical CNV location (the domain), when both query and domain are represented on the same reference sequence. An `exact` match requires the location of the query and domain to be identical. A `subinterval` match requires the query to be a subinterval of the domain. A `superinterval` match requires the query to be a superinterval of the domain. A `partial` match requires at least 1 residue of overlap between the query and domain.",  # noqa: E501
    )
    copyChange: Optional[models.CopyChange] = Field(
        None,
        description="A representation of the change in copies of a sequence in a system. MUST be one of 'efo:0030069' (complete genomic loss), 'efo:0020073' (high-level loss), 'efo:0030068' (low-level loss), 'efo:0030067' (loss), 'efo:0030064' (regional base ploidy), 'efo:0030070' (gain), 'efo:0030071' (low-level gain), 'efo:0030072' (high-level gain).",  # noqa: E501
    )
    copies: Optional[Union[int, models.Range]] = Field(
        None, description="The integral number of copies of the subject in a system."
    )


class DescribedVariation(_CategoricalVariationBase):
    """Some categorical variation concepts are supported by custom nomenclatures or
    text-descriptive representations for which a categorical variation model does not
    exist. DescribedVariation is a class that adds requirements and contextual semantics
    to the `label` and `description` fields to indicate how a categorical variation
    concept should be evaluated for matching variants.
    """

    type: Literal["DescribedVariation"] = Field(
        "DescribedVariation", description="MUST be 'DescribedVariation'."
    )
    label: StrictStr = Field(
        ...,
        description="A primary label for the categorical variation. This required property should provide a short and descriptive textual representation of the concept.",  # noqa: E501
    )
    description: Optional[StrictStr] = Field(
        None,
        description="A textual description of the domain of variation that should match the categorical variation entity.",  # noqa: E501
    )


class CategoricalVariation(RootModel):
    """A representation of a categorically-defined domain for variation, in which
    individual contextual variation instances may be members of the domain.
    """

    root: Union[
        CanonicalAllele, CategoricalCnv, DescribedVariation, ProteinSequenceConsequence
    ] = Field(
        ...,
        json_schema_extra={
            "description": "A representation of a categorically-defined domain for variation, in which individual contextual variation instances may be members of the domain.",  # noqa: E501
        },
        discriminator="type",
    )
