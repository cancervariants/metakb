"""Define data structures for loading objects into DB."""

import json
import logging
from typing import Literal, Self

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    DefiningAlleleConstraint,
)
from ga4gh.core.models import ConceptMapping, Extension, MappableConcept
from ga4gh.va_spec.base import Document, MembershipOperator, Method, TherapyGroup
from ga4gh.vrs.models import (
    Allele,
    LiteralSequenceExpression,
    ReferenceLengthExpression,
    SequenceLocation,
    VrsType,
)
from pydantic import BaseModel, RootModel

from metakb.transformers.base import NormalizerExtensionName

_logger = logging.getLogger(__name__)


class SequenceLocationNode(BaseModel):
    id: str
    # I recognize that these are technically optional --
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
        if expressions := allele.expressions:
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
        """Create new node instance from a Cat-VRS DefiningAlleleConstraint.

        :param constraint: original constraint object
        :param constraint_id: database identifier. Our working convention is to
            incorporate the container categorical variant's ID as part of this, which means
            we need to get this arg separately
        :return: node instance
        """
        return cls(
            id=constraint_id,
            relations=[],  # TODO more to think about how to convert to strings
            allele=AlleleNode.from_vrs(constraint.allele),
        )


# Helper models to enable quick serialization of array properties
_Extensions = RootModel[list[Extension]]
_Mappings = RootModel[list[ConceptMapping]]


class CategoricalVariantNode(BaseModel):
    """Node model for Categorical Variant."""

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


class DocumentNode(BaseModel):
    """Node model for Document."""

    id: str
    source_type: str
    title: str
    name: str
    pmid: str
    doi: str
    urls: list[str]

    @classmethod
    def from_vrs(cls, document: Document) -> Self:
        """We need to work out a policy for handling ID-less documents -- ie the documents
        used to back methods used by sources.


        """
        if not document.id:
            if pmid := document.pmid:
                doc_id = f"pmid:{pmid}"
            else:
                if doi := document.doi:
                    doc_id = f"doi:{doi}"
                else:
                    msg = f"Unable to create internal ID for document {document}"
                    raise ValueError(msg)
            _logger.warning("Designating %s as ID for document %s", doc_id, document)
        else:
            doc_id = document.id

        for extension in getattr(document, "extensions", []):
            if extension.name == ["source_type"]:
                src_type = extension.value
        else:
            src_type = ""

        return cls(
            id=doc_id,
            title=document.title if document.title else "",
            urls=document.urls if document.urls else [],
            pmid=str(document.pmid) if document.pmid else "",
            name=document.name if document.name else "",
            doi=document.doi if document.doi else "",
            source_type=src_type,
        )


class GeneNode(BaseModel):
    """Node model for Gene."""

    id: str
    normalized_id: str
    description: str
    name: str
    aliases: list[str]
    mappings: str
    extensions: str

    @classmethod
    def from_vrs(cls, gene: MappableConcept) -> Self:
        normalized_id = None
        for mapping in gene.mappings:
            for ext in gene.extensions:
                if ext.name == NormalizerExtensionName.PRIORITY and ext.value:
                    normalized_id = mapping.coding.id
                    break
            if normalized_id:
                break
        else:
            msg = f"Unable to locate normalized ID in gene {gene}"
            raise ValueError(msg)
        description = ""
        aliases = []
        for extension in gene.extensions:
            if extension.name == "description":
                description = extension.value
            elif extension.name == "aliases":
                aliases = extension.value
        return cls(
            id=gene.id,
            normalized_id=normalized_id,
            description=description,
            name=gene.name,
            aliases=aliases,
            mappings=_Mappings(gene.mappings).model_dump_json(),
            extensions=_Extensions(gene.extensions).model_dump_json(),
        )


class DiseaseNode(BaseModel):
    """Node model for Disease."""

    id: str
    normalized_id: str
    name: str
    mappings: str

    @classmethod
    def from_vrs(cls, disease: MappableConcept) -> Self:
        normalized_id = None
        for mapping in disease.mappings:
            for ext in disease.extensions:
                if ext.name == NormalizerExtensionName.PRIORITY and ext.value:
                    normalized_id = mapping.coding.id
                    break
            if normalized_id:
                break
        if not normalized_id:
            msg = f"Unable to locate normalized ID in disease {disease}"
            raise ValueError(msg)
        return cls(
            id=disease.id,
            normalized_id=normalized_id,
            name=disease.name,
            mappings=_Mappings(disease.mappings).model_dump_json(),
        )


class DrugNode(BaseModel):
    """Node model for Drug."""

    id: str
    normalized_id: str
    name: str
    aliases: list[str]
    extensions: str
    mappings: str

    @classmethod
    def from_vrs(cls, therapy: MappableConcept) -> Self:
        normalized_id = None
        for mapping in therapy.mappings:
            for ext in therapy.extensions:
                if ext.name == NormalizerExtensionName.PRIORITY and ext.value:
                    normalized_id = mapping.coding.id
                    break
            if normalized_id:
                break
        else:
            msg = f"Unable to locate normalized ID in therapy {therapy}"
            raise ValueError(msg)
        aliases = []
        for extension in therapy.extensions:
            if extension.name == "aliases":
                aliases = extension.value
        return cls(
            id=therapy.id,
            normalized_id=normalized_id,
            name=therapy.name,
            aliases=aliases,
            mappings=_Mappings(therapy.mappings).model_dump_json(),
            extensions=_Extensions(therapy.extensions).model_dump_json(),
        )


class TherapyGroupNode(BaseModel):
    """Node model for TherapyGroup."""

    id: str
    membership_operator: MembershipOperator
    therapies: list[DrugNode]
    extensions: str

    @classmethod
    def from_vrs(cls, therapy_group: TherapyGroup) -> Self:
        return cls(
            id=therapy_group.id,
            extensions=_Extensions(therapy_group.extensions).model_dump_json(),
            membership_operator=MembershipOperator(therapy_group.membershipOperator),
            therapies=[
                DrugNode.from_vrs(therapy) for therapy in therapy_group.therapies
            ],
        )


class MethodNode(BaseModel):
    """Node model for Method."""

    id: str
    name: str

    @classmethod
    def from_vrs(cls, method: Method) -> Self:
        return cls(id=method.id, name=method.name)


class StrengthNode(BaseModel):
    """Node model of a Strength object."""

    id: str
    name: str
    mappings: str
    primary_coding: str

    @classmethod
    def from_vrs(cls, strength: MappableConcept) -> Self:
        if (
            strength.primaryCoding.system
            == "https://civic.readthedocs.io/en/latest/model/evidence/level.html"
        ):
            node_id = f"civic.strength:{strength.primaryCoding.code}"
        elif strength.primaryCoding.system == "AMP/ASCO/CAP (AAC) Guidelines, 2017":
            node_id = f"amp-asco-cap.strength:{strength.primaryCoding.code}"
        else:
            msg = f"Unrecognized strength concept: {strength}"
            raise ValueError(msg)
        return cls(
            id=node_id,
            name=strength.name,
            mappings=_Mappings(strenght.mappings).model_dump_json(),
            primary_coding=json.dumps(strength.primaryCoding),
        )


class EvidenceNode(BaseModel):
    """Node model for a Statement object serving as evidence."""

    id: str
    description: str
    method_id: str
    document_ids: list[str]
    has_strength: StrengthNode

    # TODO think about proposition types
    # Maybe make separate node classes for each kind?
    # TODO also need to think about assertion vs evidence
