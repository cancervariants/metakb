"""Module containing variant statement definitions"""
from enum import StrEnum
from typing import Literal, Optional, Union, List

from ga4gh.core import core_models
from ga4gh.vrs import models
from pydantic import BaseModel, Field

from metakb.schemas.annotation import Document, Statement
from metakb.schemas.categorical_variation import CategoricalVariation

# TODO:
# - [ ] extends: (for fields)


class Penetrance(StrEnum):
    """The extent to which the variant impact is expressed by individuals carrying it as
    a measure of the proportion of carriers exhibiting the condition.
    """

    HIGH = "high"
    LOW = "low"
    RISK_ALLELE = "risk allele"


class ModeOfInheritance(StrEnum):
    """The pattern of inheritance expected for the pathogenic effect of this variant."""

    AUTOSOMAL_DOMINANT = "autosomal dominant"
    AUTOSOMAL_RECESSIVE = "autosomal recessive"
    X_LINKED_DOMINANT = "X-linked dominant"
    X_LINKED_RECESSIVE = "X-linked recessive"
    MITOCHONDRIAL = "mitochondrial"


class Predicate(StrEnum):
    """Define constraints for predicate"""

    IS_ONCOGENIC_FOR = "isOncogenicFor"
    IS_PROTECTIVE_FOR = "isProtectiveFor"
    IS_PREDISPOSING_FOR = "isPredisposingFor"


class AlleleOrigin(StrEnum):
    """Whether the statement should be interpreted in the context of an inherited
    (germline) variant, an acquired (somatic) mutation, or both (combined).
    """

    GERMLINE = "germline"
    SOMATIC = "somatic"
    COMBINED = "combined"


class AllelePrevalence(StrEnum):
    """Whether the statement should be interpreted in the context of the variant being
    rare or common.
    """

    RARE = "rare"
    COMMON = "common"


class VariantStatement(Statement):
    """A `Statement` describing the impact of a variant."""

    subject: None = None
    variant: Optional[
        Union[models.Variation, CategoricalVariation, core_models.IRI]
    ] = Field(
        None, description="A variation object that is the subject of the Statement."
    )


class VariantClassification(VariantStatement):
    """A `VariantStatement` classifying the impact of a variant."""

    classification: Union[core_models.Coding, core_models.IRI] = Field(
        ...,
        description="A methodological, summary classification about the impact of a variant.",
    )


class Qualifier(BaseModel):
    """Qualifier"""

    penetrance: Penetrance = Field(
        ...,
        description="The extent to which the variant impact is expressed by individuals carrying it as a measure of the proportion of carriers exhibiting the condition.",
    )
    modeOfInheritance: ModeOfInheritance = Field(
        ...,
        description="The pattern of inheritance expected for the pathogenic effect of this variant.",
    )
    geneContext: core_models.Gene = Field(
        ..., description="A gene context that qualifies the Statement."
    )


class VariantPathogenicity(VariantClassification):
    """A `VariantClassification` describing the role of a variant in causing an
    inherited disorder.
    """

    type: Literal["VariantPathogenicity"] = Field(
        "VariantPathogenicity", description="MUST be 'VariantPathogenicity'."
    )
    predicate: Literal["isCausalFor"] = "isCausalFor"
    object: None = None
    condition: Union[core_models.Condition, core_models.IRI] = Field(
        ..., description="The `Condition` for which the variant impact is stated."
    )
    qualifiers: Optional[Qualifier] = None


class VariantStudySummary(VariantStatement):
    """A `Statement` summarizing evidence about the impact of a variant from one or more
    studies.
    """

    isReportedIn: List[Union[Document, core_models.IRI]] = Field(
        None,
        description="A document in which the information content is expressed.",
        min_items=1,
    )


class VariantOncogenicityStudyQualifier(BaseModel):
    """Qualifier for Variant Oncogenicity Study"""

    alleleOrigin: Optional[AlleleOrigin] = Field(
        None,
        description="Whether the statement should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or both (combined).",
    )
    allelePrevalence: Optional[AllelePrevalence] = Field(
        None,
        description="Whether the statement should be interpreted in the context of the variant being rare or common.",
    )
    geneContext: Optional[core_models.Gene] = Field(
        None,
        description="A gene context that qualifies the Statement."
    )


class VariantOncogenicityStudy(VariantStudySummary):
    """A study summarization supporting or refuting the effect of variation on
    oncogenesis of a tumor type.
    """

    type: Literal["VariantOncogenicity"] = "VariantOncogenicity"
    predicate: Predicate
    object: None = None
    tumorType: Union[core_models.Condition, core_models.IRI] = Field(
        ..., description="The tumor type for which the variant impact is evaluated."
    )


# FIXME:
class VariantTherapeuticResponseStudyPredicate(StrEnum):
    """Predicate for Variant Therapeutic Response Study"""

    PREDICTS_SENSITIVITY_TO = "predictsSensitivityTo"
    PREDICTS_RESISTANCE_TO = "predictsResistanceTo"


class VariantTherapeuticResponseStudy(VariantStudySummary):
    """A study summarization describing the role of a variation in modulating the
    response of a neoplasm to drug administration or other therapeutic procedure.
    """

    type: Literal["VariantTherapeuticResponseStudy"] = Field(
        "VariantTherapeuticResponseStudy",
        description="MUST be 'VariantTherapeuticResponseStudy'.",
    )
    predicate: VariantTherapeuticResponseStudyPredicate
    object: None = None
    therapeutic: Union[core_models.TherapeuticProcedure, core_models.IRI] = Field(
        ...,
        description="A drug administration or other therapeutic procedure that the neoplasm is intended to respond to.",
    )
    tumorType: Union[core_models.Condition, core_models.IRI] = Field(
        ...,
        description="The tumor type context in which the variant impact is evaluated.",
    )
    qualifiers: Optional[VariantOncogenicityStudyQualifier] = None
