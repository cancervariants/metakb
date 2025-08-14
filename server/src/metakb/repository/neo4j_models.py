"""Define data structures for loading objects into DB."""

from pydantic import BaseModel, Json


class CategoricalVariantNode(BaseModel):
    id: str
    name: str = ""
    description: str = ""
    aliases: list[str] = []
    extensions: Json[
        list
    ]  # TODO double check how this works -- what's returned by neo4j?
    mappings: Json[list]


class ConstraintNode(BaseModel):
    id: str
    relations: list[str]


class AlleleNode(BaseModel):
    id: str
    name: str = ""
    expression_hgvs_g: str = ""
    expression_hgvs_c: str = ""
    expression_hgvs_p: str = ""


class SequenceLocationNode(BaseModel):
    id: str
    # I recognize that these are technically optional
    # for now I'm making them required because the alternative (working out nullability) is worse
    start: int
    end: int
    refget_accession: str
    sequence: str = ""


class LiteralSequenceExpressionNode(BaseModel):
    sequence: str


class ReferenceLengthExpressionNode(BaseModel):
    sequence: str
    length: int
    repeat_subunit_length: int
