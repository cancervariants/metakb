"""Common data model"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class StatementType(Enum):
    """Constraints for Statement types."""

    THERAPEUTIC = 'GksTherapeuticResponse'


class VariantOrigin(Enum):
    """Constraints for Variant Origins."""

    SOMATIC = 'somatic'


class ClinicalSignificance(Enum):
    """Constraints for Clinical Significance."""

    SENSITIVITY = 'predicts_sensitivity'


class EvidenceLevel(Enum):
    """Define constraints for Evidence Level."""

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class Evidence(BaseModel):
    """A class for evidence."""

    id: str
    type: StatementType
    molecular_profile: str
    therapeutic_intervention: str
    disease: str
    variant_origin: VariantOrigin
    clinical_significance: ClinicalSignificance
    evidence_level: EvidenceLevel
    provenance: List  # TODO: Not defined yet


class GKSDescriptorType(Enum):
    """Define constraints for GKS Descriptors."""

    THERAPEUTIC_INTERVENTION = 'GksTherapeuticIntervention'
    MOLECULAR_PROFILE = 'GksMolecularProfile'
    ALLELE_DESCRIPTOR = 'AlleleDescriptor'
    VARIANT_SET_DESCRIPTOR = 'VariationSetDescriptor'
    GENE_DESCRIPTOR = 'GeneDescriptor'


class Component(BaseModel):
    """A class for Components."""

    id: str
    label: str


class DrugInteractionType(Enum):
    """Define constraints for Drug Interaction Types."""

    COMBINATION = 'combination'
    SEQUENTIAL = 'sequential'
    SUBSTITUTES = 'substitutes'


class GKSDescriptors(BaseModel):
    """A class for GKS Descriptors."""

    id: str
    type: GKSDescriptorType
    components: List[Component]
    drug_interaction_type: Optional[DrugInteractionType]


class ValueObjects:
    """A class for Value Objects."""


class TherapeuticResponse:
    """A class for a Therapeutic Response."""

    evidence: Evidence
    gks_descriptors: List[GKSDescriptors]
    value_objects: List[ValueObjects]


class XrefSystem(Enum):
    """Define constraints for System in xrefs."""

    CLINVAR = 'ClinVar'
    CLINGEN = 'ClinGenAlleleRegistry'
    DB_SNP = 'dbSNP'
    NCBI = 'ncbigene'


class NamespacePrefix(Enum):
    """Define constraints for Namespace prefixes."""

    CIVIC = 'civic'
    NCIT = 'ncit'
