"""Module containing variant statement definitions"""
from enum import StrEnum
from typing import Literal, Optional, Union, List

from ga4gh.core import core_models
from ga4gh.vrs import models
from pydantic import BaseModel, Field

from metakb.schemas.annotation import Document, _StatementBase
from metakb.schemas.categorical_variation import CategoricalVariation


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


class VariantOncogenicityStudyPredicate(StrEnum):
    """Define constraints for Variant Oncogenicity Study predicate"""

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


class VariantStatement(_StatementBase):
    """A `Statement` describing the impact of a variant."""

    # extends subject
    variant: Optional[
        Union[models.Variation, CategoricalVariation, core_models.IRI]
    ] = Field(
        None, description="A variation object that is the subject of the Statement."
    )


class VariantClassification(VariantStatement):
    """A `VariantStatement` classifying the impact of a variant."""

    classification: Union[core_models.Coding, core_models.IRI] = Field(
        ...,
        description="A methodological, summary classification about the impact of a variant.",  # noqa: E501
    )


class VariantPathogenicityQualifier(BaseModel):
    """VariantPathogenicity Qualifier"""

    penetrance: Optional[Penetrance] = Field(
        None,
        description="The extent to which the variant impact is expressed by individuals carrying it as a measure of the proportion of carriers exhibiting the condition.",  # noqa: E501
    )
    modeOfInheritance: Optional[ModeOfInheritance] = Field(
        None,
        description="The pattern of inheritance expected for the pathogenic effect of this variant.",  # noqa: E501
    )
    geneContext: Optional[core_models.Gene] = Field(
        None, description="A gene context that qualifies the Statement."
    )


class VariantPathogenicity(VariantClassification):
    """A `VariantClassification` describing the role of a variant in causing an
    inherited disorder.
    """

    type: Literal["VariantPathogenicity"] = Field(
        "VariantPathogenicity", description="MUST be 'VariantPathogenicity'."
    )
    # extends predicate
    predicate: Optional[Literal["isCausalFor"]] = None
    # extends object
    condition: Union[core_models.Condition, core_models.IRI] = Field(
        ..., description="The `Condition` for which the variant impact is stated."
    )
    # extends qualifiers
    qualifiers: Optional[VariantPathogenicityQualifier] = None


class VariantStudySummary(VariantStatement):
    """A `Statement` summarizing evidence about the impact of a variant from one or more
    studies.
    """

    # extends isReportedIn
    isReportedIn: List[Union[Document, core_models.IRI]] = Field(
        ...,
        description="A document in which the information content is expressed.",
        min_items=1,
    )


class VariantOncogenicityStudyQualifier(BaseModel):
    """Qualifier for Variant Oncogenicity Study"""

    alleleOrigin: Optional[AlleleOrigin] = Field(
        None,
        description="Whether the statement should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or both (combined).",  # noqa: E501
    )
    allelePrevalence: Optional[AllelePrevalence] = Field(
        None,
        description="Whether the statement should be interpreted in the context of the variant being rare or common.",  # noqa: E501
    )
    geneContext: Optional[core_models.Gene] = Field(
        None, description="A gene context that qualifies the Statement."
    )


class VariantOncogenicityStudy(VariantStudySummary):
    """A study summarization supporting or refuting the effect of variation on
    oncogenesis of a tumor type.
    """

    type: Literal["VariantOncogenicity"] = "VariantOncogenicity"
    # extends predicate
    predicate: VariantOncogenicityStudyPredicate
    # extends object
    tumorType: Union[core_models.Condition, core_models.IRI] = Field(
        ..., description="The tumor type for which the variant impact is evaluated."
    )
    # extends qualifiers
    qualifiers: Optional[VariantOncogenicityStudyQualifier] = None


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
    # extends predicate
    predicate: VariantTherapeuticResponseStudyPredicate
    # extends object
    therapeutic: Union[core_models.TherapeuticProcedure, core_models.IRI] = Field(
        ...,
        description="A drug administration or other therapeutic procedure that the neoplasm is intended to respond to.",  # noqa: E501
    )
    tumorType: Union[core_models.Condition, core_models.IRI] = Field(
        ...,
        description="The tumor type context in which the variant impact is evaluated.",
    )
    # extends qualifiers
    qualifiers: Optional[VariantOncogenicityStudyQualifier] = None
