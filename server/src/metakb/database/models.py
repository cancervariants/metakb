"""Define data access objects."""

from neomodel import (
    ArrayProperty,
    IntegerProperty,
    One,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    UniqueIdProperty,
)


class SequenceLocation(StructuredNode):
    id_ = StringProperty(unique_index=True, required=True)
    refget_accession = StringProperty(required=True)
    sequence = StringProperty()
    start = IntegerProperty()
    end = IntegerProperty()

    allele_set = RelationshipFrom("Allele", "HAS_LOCATION")


class SequenceExpression(StructuredNode):
    uid = UniqueIdProperty()
    sequence = StringProperty(required=True)

    allele_set = RelationshipFrom("Allele", "HAS_STATE")


class LiteralSequenceExpression(SequenceExpression):
    pass


class ReferenceLengthExpression(SequenceExpression):
    length = IntegerProperty(required=True)
    repeat_subunit_length = IntegerProperty(required=True)


class Variation(StructuredNode):
    name = StringProperty()
    description = StringProperty()
    extensions = StringProperty()
    mappings = StringProperty()


class Allele(Variation):
    id_ = StringProperty(unique_index=True, required=True)
    expression_hgvs_g = ArrayProperty(base_property=StringProperty())
    expression_hgvs_c = ArrayProperty(base_property=StringProperty())
    expression_hgvs_p = ArrayProperty(base_property=StringProperty())

    location = RelationshipTo(SequenceLocation, "HAS_LOCATION", cardinality=One)
    state = RelationshipTo(
        SequenceExpression,
        "HAS_STATE",
        cardinality=One,
    )

    categorical_variant_set = RelationshipFrom("CategoricalVariant", "HAS_MEMBER")


class DefiningAlleleConstraint(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty()
    relations = ArrayProperty(base_property=StringProperty())

    defining_allele = RelationshipTo(Allele, "HAS_DEFINING_ALLELE", cardinality=One)


class CategoricalVariant(Variation):
    id_ = StringProperty(unique_index=True, required=True)

    constraint = RelationshipTo(
        DefiningAlleleConstraint, "HAS_CONSTRAINT", cardinality=One
    )
    members = RelationshipTo(Allele, "HAS_MEMBER")
