"""Common data model"""
from enum import Enum
from typing import List, Literal, Optional, Set, Union

from ga4gh.vrsatile.pydantic.core_models import CURIE, ExtensibleEntity, ValueEntity, \
    Coding, RecordMetadata, Condition, Disease, Phenotype, Therapeutic, \
    CombinationTherapeuticCollection, SubstituteTherapeuticCollection
from ga4gh.vrsatile.pydantic.vrs_models import Variation
from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, \
    CategoricalVariation, CategoricalVariationDescriptor, PhenotypeDescriptor, \
    DiseaseDescriptor, ConditionDescriptor, TherapeuticDescriptor, \
    TherapeuticCollectionDescriptor
from pydantic import BaseModel
from pydantic.types import StrictStr


class CivicEvidenceLevel(str, Enum):
    """Define constraints for CIViC evidence levels"""

    A = "civic.evidence_level:A"
    B = "civic.evidence_level:B"
    C = "civic.evidence_level:C"
    D = "civic.evidence_level:D"
    E = "civic.evidence_level:E"


class MoaEvidenceLevel(str, Enum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "moa.evidence_level:fda_approved"
    GUIDELINE = "moa.evidence_level:guideline"
    CLINICAL_TRIAL = "moa.evidence_level:clinical_trial"
    CLINICAL_EVIDENCE = "moa.evidence_level:clinical_evidence"
    PRECLINICAL_EVIDENCE = "moa.evidence_level:preclinical_evidence"
    INFERENTIAL_EVIDENCE = "moa.evidence_level:inferential_evidence"


class EcoLevel(str, Enum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: List[StrictStr]
    exact_mappings: Set[Union[CivicEvidenceLevel, MoaEvidenceLevel, EcoLevel]]
    definition: StrictStr


class SourceName(str, Enum):
    """Resources we import directly."""

    CIVIC = "civic"
    MOA = "moa"


class XrefSystem(str, Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = "clinvar"
    CLINGEN = "caid"
    DB_SNP = "dbsnp"
    NCBI = "ncbigene"
    DISEASE_ONTOLOGY = "do"


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = "pmid"
    ASCO = "asco"


class NormalizerPrefix(str, Enum):
    """Define constraints for normalizer prefixes."""

    GENE = "gene"


class TargetPropositionType(str, Enum):
    """Define constraints for target proposition type."""

    VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE = "VariationNeoplasmTherapeuticResponseProposition"  # noqa: E501
    PREDICTIVE = "VariationTherapeuticResponseProposition"
    DIAGNOSTIC = "VariationDiagnosticProposition"
    PROGNOSTIC = "VariationPrognosticProposition"
    PREDISPOSING = "VariationPredispositionProposition"
    FUNCTIONAL = "VariationFunctionalConsequenceProposition"
    ONCOGENIC = "VariationOncogenicityProposition"
    PATHOGENIC = "VariationPathogenicityProposition"


class PredictivePredicate(str, Enum):
    """Define constraints for predictive predicate."""

    SENSITIVITY = "predicts_sensitivity_to"
    RESISTANCE = "predicts_resistance_to"


class DiagnosticPredicate(str, Enum):
    """Define constraints for diagnostic predicate."""

    POSITIVE = "is_diagnostic_inclusion_criterion_for"
    NEGATIVE = "is_diagnostic_exclusion_criterion_for"


class PrognosticPredicate(str, Enum):
    """Define constraints for prognostic predicate."""

    BETTER_OUTCOME = "is_prognostic_of_better_outcome_for"
    POOR_OUTCOME = "is_prognostic_of_worse_outcome_for"


class PathogenicPredicate(str, Enum):
    """Define constraints for the pathogenicity predicate."""

    UNCERTAIN_SIGNIFICANCE = "is_of_uncertain_significance_for"
    PATHOGENIC = "is_pathogenic_for"
    BENIGN = "is_benign_for"


class FunctionalPredicate(str, Enum):
    """Define constraints for functional predicate."""

    GAIN_OF_FUNCTION = "causes_gain_of_function_of"
    LOSS_OF_FUNCTION = "causes_loss_of_function_of"
    UNALTERED_FUNCTION = "does_not_change_function_of"
    NEOMORPHIC = "causes_neomorphic_function_of"
    DOMINATE_NEGATIVE = "causes_dominant_negative_function_of"


Predicate = Union[PredictivePredicate, DiagnosticPredicate, PrognosticPredicate,
                  PathogenicPredicate, FunctionalPredicate]


class MethodId(str, Enum):
    """Create method id constants"""

    CIVIC_EID_SOP = "metakb.method:1"
    CIVIC_AID_AMP_ASCO_CAP = "metakb.method:2"
    CIVIC_AID_ACMG = "metakb.method:3"
    MOA_ASSERTION_BIORXIV = "metakb.method:4"


class Document(ExtensibleEntity):
    """A representation of a physical or digital document"""

    type: Literal["Document"] = "Document"
    xrefs: Optional[List[CURIE]]
    title: Optional[StrictStr]


class Method(ExtensibleEntity):
    """A set of instructions that specify how to achieve some objective (e.g.
    experimental protocols, curation guidelines, rule sets, etc.)
    """

    type: Literal["Method"] = "Method"
    is_reported_in: Optional[Union[CURIE, Document]]
    method_type: Optional[StrictStr]


# class DataItem():
#     pass


class Agent(ExtensibleEntity):
    """An autonomous actor (person, organization, or computational agent) that bears
    some form of responsibility for an activity taking place, for the existence of an
    entity, or for another agent"s activity.
    """

    type: Literal["Agent"] = "Agent"
    name: Optional[StrictStr]


class Contribution(ExtensibleEntity):
    """The sum of all actions taken by a single agent in contributing to the creation,
    modification, assessment, or deprecation of a particular entity (e.g. a Statement,
    EvidenceLine, DataItem, Publication, etc.)
    """

    type: Literal["Contribution"] = "Contribution"
    agent: Optional[Agent]
    date: Optional[StrictStr]  # TODO: format date
    role: Optional[StrictStr]


class InformationEntity(ExtensibleEntity):
    """InformationEntities are abstract (non-physical) entities that are about
    something (i.e. they carry information about things in the real world).
    """

    description: Optional[StrictStr]
    confidence_level: Optional[Coding]
    # confidence_score: DataItem
    method: Optional[Union[Method, CURIE]]
    contributions: Optional[List[Contribution]]
    is_reported_in: Optional[List[Union[Document, CURIE]]]
    record_metadata: Optional[RecordMetadata]


class Direction(str, Enum):
    """The direction of this statement with respect to the target proposition."""

    SUPPORTS = "supports"
    UNCERTAIN = "uncertain"
    OPPOSES = "opposes"


class Proposition(ValueEntity):
    """An abstract :ref:`ValueEntity` representing the shareable meaning that can be
    put forth as true or false by a Statement.
    """

    subject: ValueEntity
    predicate: Predicate
    object: ValueEntity


class VariationProposition(Proposition):
    """A proposition describing the role of a variation subject."""

    subject: Union[CURIE, Variation, CategoricalVariation]


class VariationGermlinePathogenicityPropositionPredicate(str, Enum):
    """The relationship asserted to hold between the variation (subject) and the
    condition (object) of the Proposition.
    """

    CAUSES_MENDELIAN_CONDITION = "causes_mendelian_condition"
    INCREASES_RISK_FOR_CONDITION = "increases_risk_for_condition"
    DECREASES_RISK_FOR_CONDITION = "decreases_risk_for_condition"


class VariationGermlinePathogenicityProposition(VariationProposition):
    """A proposition describing the role of a variation in causing or preventing a
    germline disease condition.
    """

    type: Literal["VariationGermlinePathogenicityProposition"] = "VariationGermlinePathogenicityProposition"  # noqa: E501
    predicate: VariationGermlinePathogenicityPropositionPredicate
    object: Union[Condition, Disease, Phenotype]


class VariationNeoplasmProposition(VariationProposition):
    """A proposition regarding the effect of variation within a neoplasm."""

    type: Literal["VariationNeoplasmProposition"] = "VariationNeoplasmProposition"
    neoplasm_type_qualifier: Union[Condition, Disease, Phenotype]


class VariationNeoplasmTherapeuticResponseProposition(VariationNeoplasmProposition):
    """A :ref:`Proposition` describing the role of a variation in modulating the
    response of a neoplasm to one or more therapeutics.
    """

    type: Literal["VariationNeoplasmTherapeuticResponseProposition"] = "VariationNeoplasmTherapeuticResponseProposition"  # noqa: E501
    object: Union[Therapeutic, CombinationTherapeuticCollection,
                  SubstituteTherapeuticCollection]


class Statement(InformationEntity):
    """A Statement (aka "Assertion") represents a claim of purported truth as made by
    a particular agent, on a particular occasion.
    """

    evidence_level: Optional[Coding]
    # evidence_score: DataItem
    target_proposition: Optional[Union[Proposition, CURIE]]
    conclusion: Optional[Coding]
    direction: Optional[Direction]


class VariationOrigin(str, Enum):
    """A representation of whether the subject variation is inherited (germline) or
    acquired (somatic).
    """

    GERMLINE = "germline"
    SOMATIC = "somatic"


class VariationStatement(Statement):
    """A :ref:`Statement` describing the impact of a variation."""

    subject_descriptor: Optional[Union[VariationDescriptor,
                                       CategoricalVariationDescriptor, CURIE]]
    variation_origin: Optional[VariationOrigin]


class VariationConditionStatement(VariationStatement):
    """A :ref:`Statement` describing the impact of a variation on a condition."""

    object_descriptor: Union[PhenotypeDescriptor, DiseaseDescriptor,
                             ConditionDescriptor, CURIE]


class VariationGermlinePathogenicityStatement(VariationConditionStatement):
    """A :ref:`Statement` describing the role of a variation in causing or protecting
    against a germline Condition.
    """

    type: Literal["VariationGermlinePathogenicityStatement"] = \
        "VariationGermlinePathogenicityStatement"
    classification: Optional[Coding]
    target_proposition: Optional[VariationGermlinePathogenicityProposition]


class VariationNeoplasmStatement(VariationStatement):
    """A statement regarding the effect of variation within a neoplasm."""

    type: Literal["VariationNeoplasmStatement"] = "VariationNeoplasmStatement"
    neoplasm_type_descriptor: Optional[Union[PhenotypeDescriptor, DiseaseDescriptor,
                                             ConditionDescriptor, CURIE]]


class VariationNeoplasmTherapeuticResponseStatement(VariationNeoplasmStatement):
    """A :ref:`Statement` describing the role of a variation in modulating the response
    of a neoplasm to one or more therapeutics.
    """

    type: Literal["VariationNeoplasmTherapeuticResponseStatement"] = \
        "VariationNeoplasmTherapeuticResponseStatement"
    object_descriptor: Optional[Union[TherapeuticDescriptor,
                                      TherapeuticCollectionDescriptor, CURIE]]
