"""Construct Categorical Variants from constituent parts for evidence aggregation.

Provide constructor functions and also define rules/methods for minting IDs.

Todo:
* Figure out name and ID conventions for "normalized" objects

"""

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    CopyChangeConstraint,
    DefiningAlleleConstraint,
    DefiningLocationConstraint,
    FeatureContextConstraint,
    Relation,
)
from ga4gh.cat_vrs.recipes import CategoricalCnv, ProteinSequenceConsequence, SystemUri
from ga4gh.core.models import Coding, MappableConcept, code
from ga4gh.vrs.models import Allele, CopyNumberChange

LIFTOVER_TO_RELATION = MappableConcept(
    primaryCoding=Coding(
        system=SystemUri.GKS_ALLELE_RELATION, code=code(Relation.LIFTOVER_TO)
    )
)
TRANSLATION_OF_RELATION = MappableConcept(
    primaryCoding=Coding(
        system=SystemUri.SEQUENCE_ONTOLOGY,
        code=code(Relation.TRANSLATION_OF),
    ),
)


def build_copynumberchange_catvar(variant: CopyNumberChange) -> CategoricalCnv:
    """Build a CopyNumberChange catvar

    :param variant: VRS copynumberchange variant
    :return: CategoricalCNV using the input variant, with MetaKB name and ID
    """
    cv_id = f"metakb.cv:CNC_{variant.copyChange}_{variant.id.split(':')[1]}"
    cv_name = "TODO FIXME"
    return CategoricalCnv(
        id=cv_id,
        name=cv_name,
        constraints=[
            Constraint(root=CopyChangeConstraint(copyChange=variant.copyChange)),
            Constraint(
                root=DefiningLocationConstraint(
                    location=variant.location,
                    matchCharacteristic=MappableConcept(
                        primaryCoding=Coding(
                            code=code("is_within"),
                            system="ga4gh-gks-term:location-match",
                        )
                    ),
                    relations=[LIFTOVER_TO_RELATION],
                )
            ),
        ],
    )


def build_proteinsequenceconsequence_catvar(
    allele: Allele,
) -> ProteinSequenceConsequence:
    """Construct a ProteinSequenceConsequence categorical variant.

    :param allele: VRS allele
    :return: ProteinSequenceConsequence-based catvar with MetaKB name and ID
    """
    cv_id = f"metakb.cv:PSQ_{allele.id.split(':')[1]}"
    cv_name = "TODO FIXME"  # figure out how to autogenerate name
    return ProteinSequenceConsequence(
        id=cv_id,
        name=cv_name,
        constraints=[
            Constraint(
                root=DefiningAlleleConstraint(
                    allele=allele,
                    relations=[
                        LIFTOVER_TO_RELATION,
                        TRANSLATION_OF_RELATION,
                    ],
                )
            )
        ],
    )


def build_featurecontext_catvar(feature: MappableConcept) -> CategoricalVariant:
    """Build a simple FeatureContextConstraint-based catvar

    :param feature: feature to use as basis of constraint
    :return: CatVar with a FeatureContextConstraint, and a MetaKB name and ID
    """
    if feature.conceptType != "Gene":
        raise ValueError
    cv_id = f"metakb.cv:FC_{feature.id.replace(':', '_')}"
    cv_name = "TODO METAKB FIXME"
    return CategoricalVariant(
        id=cv_id,
        name=cv_name,
        constraints=[Constraint(root=FeatureContextConstraint(featureContext=feature))],
    )
