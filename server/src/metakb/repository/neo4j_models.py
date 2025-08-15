"""Define data structures for loading objects into DB."""

import json
from typing import Literal, Self

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    DefiningAlleleConstraint,
)
from ga4gh.core.models import ConceptMapping, Extension
from ga4gh.vrs.models import (
    Allele,
    LiteralSequenceExpression,
    ReferenceLengthExpression,
    SequenceLocation,
    VrsType,
)
from pydantic import BaseModel, Json, RootModel


class SequenceLocationNode(BaseModel):
    id: str
    # I recognize that these are technically optional
    # for now I'm making them required because the alternative (working out nullability) is worse
    # so we can figure it out later
    start: int
    end: int
    refget_accession: str
    sequence: str = ""

    @classmethod
    def from_vrs(cls, sequence_location: SequenceLocation) -> Self:
        return cls(
            id=sequence_location.id,
            start=sequence_location.start,
            end=sequence_location.end,
            refget_accession=sequence_location.sequenceReference.refgetAccession,
            sequence=str(sequence_location.sequence),
        )


class LiteralSequenceExpressionNode(BaseModel):
    sequence: str
    type: Literal["LiteralSequenceExpression"] = "LiteralSequenceExpression"

    @classmethod
    def from_vrs(cls, lse: LiteralSequenceExpression) -> Self:
        return cls(sequence=str(lse.sequence))


class ReferenceLengthExpressionNode(BaseModel):
    sequence: str
    length: int
    repeat_subunit_length: int
    type: Literal["ReferenceLengthExpression"] = "ReferenceLengthExpression"

    @classmethod
    def from_vrs(cls, rle: ReferenceLengthExpression) -> Self:
        return cls(
            sequence=rle.sequence,
            length=rle.length,
            repeat_subunit_length=rle.repeatSubunitLength,
        )


class AlleleNode(BaseModel):
    id: str
    name: str
    expression_hgvs_g: list[str]
    expression_hgvs_c: list[str]
    expression_hgvs_p: list[str]
    location: SequenceLocationNode
    state: LiteralSequenceExpressionNode | ReferenceLengthExpressionNode

    @classmethod
    def from_vrs(cls, allele: Allele) -> Self:
        grouped_expressions = {}
        if expressions := getattr(allele, "expressions"):
            for expr in expressions:
                key = f"expression_{expr.syntax.replace('.', '_')}"
                grouped_expressions.setdefault(key, []).append(expr.value)
        if allele.state.type == VrsType.LIT_SEQ_EXPR:
            state = LiteralSequenceExpressionNode.from_vrs(allele.state)
        elif allele.state.type == VrsType.REF_LEN_EXPR:
            state = ReferenceLengthExpressionNode.from_vrs(allele.state)
        else:
            msg = f"Unrecognized state type: {allele.state} for {allele.id}"
            raise ValueError(msg)

        return cls(
            id=allele.id,
            name=allele.name if allele.name else "",
            expression_hgvs_g=grouped_expressions.get("expression_hgvs_g", []),
            expression_hgvs_c=grouped_expressions.get("expression_hgvs_c", []),
            expression_hgvs_p=grouped_expressions.get("expression_hgvs_p", []),
            location=SequenceLocationNode.from_vrs(allele.location),
            state=state,
        )


class DefiningAlleleConstraintNode(BaseModel):
    id: str
    relations: list[str]
    allele: AlleleNode

    @classmethod
    def from_vrs(cls, constraint: DefiningAlleleConstraint, constraint_id: str) -> Self:
        return cls(
            id=constraint_id,
            relations=[],  # TODO more to think about how to convert to strings
            allele=AlleleNode.from_vrs(constraint.allele),
        )


# Helper models to enable quick serialization of array properties
_Extensions = RootModel[list[Extension]]
_Mappings = RootModel[list[ConceptMapping]]


class CategoricalVariantNode(BaseModel):
    id: str
    name: str
    description: str
    aliases: list[str] = []
    extensions: str
    mappings: str
    constraint: DefiningAlleleConstraintNode  # only currently-supported node
    members: list[AlleleNode]

    @classmethod
    def from_vrs(cls, catvar: CategoricalVariant) -> Self:
        if len(catvar.constraints) != 1:
            msg = "Only single-constraint catvars are currently supported"
            raise ValueError(msg)
        constraint = catvar.constraints[0]
        if constraint.root.type == "DefiningAlleleConstraint":
            constraint_id = (
                f"{catvar.id}:{constraint.root.type}:{constraint.root.allele.id}"
            )
            constraint_node = DefiningAlleleConstraintNode.from_vrs(
                constraint.root, constraint_id
            )
        else:
            msg = f"Unrecognized constraint type: {constraint}"
            raise ValueError(msg)

        return cls(
            id=catvar.id,
            name=catvar.name,
            description=catvar.description,
            aliases=catvar.aliases,
            extensions=_Extensions(catvar.extensions).model_dump_json(),
            mappings=_Mappings(catvar.mappings).model_dump_json(),
            constraint=constraint_node,
            members=[AlleleNode.from_vrs(m.root) for m in catvar.members],
        )
