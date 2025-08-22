"""Define data structures for loading objects into DB."""

from __future__ import annotations

import json
import logging
from typing import Literal, Self

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    DefiningAlleleConstraint,
)
from ga4gh.core.models import Coding, ConceptMapping, Extension, MappableConcept
from ga4gh.va_spec.base import (
    DiagnosticPredicate,
    Direction,
    Document,
    EvidenceLine,
    MembershipOperator,
    Method,
    PrognosticPredicate,
    Statement,
    TherapeuticResponsePredicate,
    TherapyGroup,
    VariantDiagnosticProposition,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import (
    Allele,
    Expression,
    LiteralSequenceExpression,
    ReferenceLengthExpression,
    SequenceLocation,
    SequenceReference,
    VrsType,
)
from pydantic import BaseModel, Field, RootModel

from metakb.transformers.base import NormalizerExtensionName

_logger = logging.getLogger(__name__)

# Helper models to enable quick serialization of array properties
_Extensions = RootModel[list[Extension]]
_Mappings = RootModel[list[ConceptMapping]]
_Expressions = RootModel[list[Expression]]


class SequenceLocationNode(BaseModel):
    """Node model for SequenceLocation"""

    id: str
    # I recognize that these are technically optional --
    # for now I'm making them required because the alternative (working out nullability) is worse
    # so we can figure it out later
    start: int
    end: int
    refget_accession: str
    sequence: str = ""

    @classmethod
    def from_gks(cls, sequence_location: SequenceLocation) -> Self:
        """Create Node instance from GKS class."""
        return cls(
            id=sequence_location.id,
            start=sequence_location.start,
            end=sequence_location.end,
            refget_accession=sequence_location.sequenceReference.refgetAccession,
            sequence=str(sequence_location.sequence),
        )

    def to_gks(self) -> SequenceLocation:
        """Return VRS-Python SequenceLocation"""
        return SequenceLocation(
            id=self.id,
            start=self.start,
            end=self.end,
            sequenceReference=SequenceReference(refgetAccession=self.refget_accession),
            sequence=self.sequence if self.sequence else None,
        )


class LiteralSequenceExpressionNode(BaseModel):
    """Node model for LiteralSequenceExpression"""

    sequence: str
    type: Literal["LiteralSequenceExpression"] = "LiteralSequenceExpression"

    @classmethod
    def from_gks(cls, lse: LiteralSequenceExpression) -> Self:
        """Create Node instance from GKS class."""
        return cls(sequence=str(lse.sequence))

    def to_gks(self) -> LiteralSequenceExpression:
        """Return VRS-Python LiteralSequenceExpression"""
        return LiteralSequenceExpression(sequence=self.sequence)


class ReferenceLengthExpressionNode(BaseModel):
    """Node model for ReferenceLengthExpression"""

    sequence: str
    length: int
    repeat_subunit_length: int
    type: Literal["ReferenceLengthExpression"] = "ReferenceLengthExpression"

    @classmethod
    def from_gks(cls, rle: ReferenceLengthExpression) -> Self:
        """Create Node instance from GKS class."""
        return cls(
            sequence=rle.sequence.root,
            length=rle.length,
            repeat_subunit_length=rle.repeatSubunitLength,
        )

    def to_gks(self) -> ReferenceLengthExpression:
        """Return VRS-Python ReferenceLengthExpression"""
        return ReferenceLengthExpression(
            sequence=self.sequence,
            length=self.length,
            repeatSubunitLength=self.repeat_subunit_length,
        )


class AlleleNode(BaseModel):
    """Node model for VRS allele"""

    id: str
    name: str
    expressions: str  # just a jsonblob for now. we should update the harvest/transform to only grab relevant hgvs expr
    location: SequenceLocationNode
    state: LiteralSequenceExpressionNode | ReferenceLengthExpressionNode

    @classmethod
    def from_gks(cls, allele: Allele) -> Self:
        """Create Node instance from GKS class."""
        if allele.state.type == VrsType.LIT_SEQ_EXPR:
            state = LiteralSequenceExpressionNode.from_gks(allele.state)
        elif allele.state.type == VrsType.REF_LEN_EXPR:
            state = ReferenceLengthExpressionNode.from_gks(allele.state)
        else:
            msg = f"Unrecognized state type: {allele.state} for {allele.id}"
            raise ValueError(msg)

        return cls(
            id=allele.id,
            name=allele.name if allele.name else "",
            expressions=_Expressions(allele.expressions or []).model_dump_json(),
            location=SequenceLocationNode.from_gks(allele.location),
            state=state,
        )

    def to_gks(self) -> Allele:
        """Return VRS-Python Allele instance"""
        return Allele(
            id=self.id,
            name=self.name if self.name else None,
            expressions=_Expressions(json.loads(self.expressions)).root,
            location=self.location.to_gks(),
            state=self.state.to_gks(),
        )


class DefiningAlleleConstraintNode(BaseModel):
    """Node model for Cat-VRS DefiningAlleleConstraint"""

    id: str
    relations: list[str]
    allele: AlleleNode

    @classmethod
    def from_gks(cls, constraint: DefiningAlleleConstraint, constraint_id: str) -> Self:
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
            allele=AlleleNode.from_gks(constraint.allele),
        )

    def to_gks(self) -> DefiningAlleleConstraint:
        return DefiningAlleleConstraint(
            relations=self.relations, allele=self.allele.to_gks()
        )


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
    def from_gks(cls, catvar: CategoricalVariant) -> Self:
        """Create Node instance from GKS class."""
        if len(catvar.constraints) != 1:
            msg = "Only single-constraint catvars are currently supported"
            raise ValueError(msg)
        constraint = catvar.constraints[0]
        if constraint.root.type == "DefiningAlleleConstraint":
            constraint_id = (
                f"{catvar.id}:{constraint.root.type}:{constraint.root.allele.id}"
            )
            constraint_node = DefiningAlleleConstraintNode.from_gks(
                constraint.root, constraint_id
            )
        else:
            msg = f"Unrecognized constraint type: {constraint}"
            raise ValueError(msg)

        members = (
            [AlleleNode.from_gks(m.root) for m in catvar.members]
            if catvar.members
            else []
        )

        return cls(
            id=catvar.id,
            name=catvar.name or "",
            description=catvar.description or "",
            aliases=catvar.aliases or [],
            extensions=_Extensions(catvar.extensions or []).model_dump_json(),
            mappings=_Mappings(catvar.mappings or []).model_dump_json(),
            constraint=constraint_node,
            members=members,
        )

    def to_gks(self) -> CategoricalVariant:
        """Construct cat-vrs-python CategoricalVariant instance"""
        return CategoricalVariant(
            id=self.id,
            name=self.name if self.name else "",
            aliases=self.aliases if self.aliases else None,
            description=self.description if self.description else "",
            extensions=_Extensions(json.loads(self.extensions)).root,
            mappings=_Mappings(json.loads(self.mappings)).root,
            constraints=[self.constraint.to_gks()],
            members=[m.to_gks() for m in self.members],
        )


class GeneNode(BaseModel):
    """Node model for Gene."""

    id: str
    normalized_id: str
    name: str
    mappings: str
    extensions: str

    @classmethod
    def from_gks(cls, gene: MappableConcept) -> Self:
        """Create Node instance from GKS class."""
        normalized_id = None
        for mapping in gene.mappings:
            for ext in mapping.extensions:
                if ext.name == NormalizerExtensionName.PRIORITY and ext.value:
                    normalized_id = mapping.coding.id
                    break
            if normalized_id:
                break
        else:
            msg = f"Unable to locate normalized ID in gene {gene}"
            raise ValueError(msg)
        description = ""
        if extensions := gene.extensions:
            for extension in extensions:
                if extension.name == "description":
                    description = extension.value
        return cls(
            id=gene.id,
            normalized_id=normalized_id,
            description=description,
            name=gene.name,
            mappings=_Mappings(gene.mappings or []).model_dump_json(),
            extensions=_Extensions(gene.extensions or []).model_dump_json(),
        )

    def to_gks(self) -> MappableConcept:
        """Create GKS class for Gene from node."""
        return MappableConcept(
            id=self.id,
            conceptType="gene",
            name=self.name if self.name else None,
            mappings=_Mappings(json.loads(self.mappings)).root,
            extensions=_Extensions(json.loads(self.extensions)).root,
        )


class DiseaseNode(BaseModel):
    """Node model for Disease."""

    id: str
    normalized_id: str
    name: str
    mappings: str

    @classmethod
    def from_gks(cls, disease: MappableConcept) -> Self:
        """Create Node instance from GKS class."""
        normalized_id = None
        for mapping in disease.mappings:
            if extensions := mapping.extensions:
                for extension in extensions:
                    if (
                        extension.name == NormalizerExtensionName.PRIORITY
                        and extension.value
                    ):
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
            name=disease.name or "",
            mappings=_Mappings(disease.mappings or []).model_dump_json(),
        )

    def to_gks(self) -> MappableConcept:
        """Create GKS class for Disease from node."""
        return MappableConcept(
            id=self.id,
            conceptType="Disease",
            name=self.name if self.name else None,
            mappings=_Mappings(json.loads(self.mappings)).root,
        )


class DrugNode(BaseModel):
    """Node model for Drug."""

    id: str
    normalized_id: str
    name: str
    extensions: str
    mappings: str

    @classmethod
    def from_gks(cls, therapy: MappableConcept) -> Self:
        """Create Node instance from GKS class."""
        normalized_id = None
        for mapping in therapy.mappings:
            for ext in mapping.extensions:
                if ext.name == NormalizerExtensionName.PRIORITY and ext.value:
                    normalized_id = mapping.coding.id
                    break
            if normalized_id:
                break
        else:
            msg = f"Unable to locate normalized ID in therapy {therapy}"
            raise ValueError(msg)
        return cls(
            id=therapy.id,
            normalized_id=normalized_id,
            name=therapy.name or "",
            mappings=_Mappings(therapy.mappings or []).model_dump_json(),
            extensions=_Extensions(therapy.extensions or []).model_dump_json(),
        )

    def to_gks(self) -> MappableConcept:
        """Create GKS MappableConcept (drug) from node."""
        return MappableConcept(
            id=self.id,
            conceptType="Drug",
            name=self.name if self.name else None,
            mappings=_Mappings(json.loads(self.mappings)).root,
            extensions=_Extensions(json.loads(self.mappings)).root,
        )


class TherapyGroupNode(BaseModel):
    """Node model for TherapyGroup."""

    id: str
    membership_operator: MembershipOperator
    therapies: list[DrugNode]
    extensions: str

    @classmethod
    def from_gks(cls, therapy_group: TherapyGroup) -> Self:
        """Create Node instance from GKS class."""
        return cls(
            id=therapy_group.id,
            extensions=_Extensions(therapy_group.extensions or []).model_dump_json(),
            membership_operator=MembershipOperator(therapy_group.membershipOperator),
            therapies=[
                DrugNode.from_gks(therapy) for therapy in therapy_group.therapies
            ],
        )

    def to_gks(self) -> TherapyGroup:
        """Create TherapyGroup GKS class from Node instance."""
        return TherapyGroup(
            id=self.id,
            membershipOperator=self.membership_operator,
            therapies=[d.to_gks() for d in self.therapies],
            extensions=_Extensions(json.loads(self.extensions)).root,
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
    def from_gks(cls, document: Document) -> Self:
        """Create Node instance from GKS class.

        **We need to work out a policy for handling ID-less documents -- ie the documents
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
            _logger.info("Designating %s as ID for document %s", doc_id, document)
        else:
            doc_id = document.id

        if extensions := document.extensions:
            for extension in extensions:
                if extension.name == ["source_type"]:
                    src_type = extension.value
                    break
            else:
                src_type = ""
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

    def to_gks(self) -> Document:
        """Create va-spec-python Document instance"""
        doc_id = None if self.id.startswith(("civic", "moa")) else self.id
        # TODO source type?
        return Document(
            id=doc_id,
            title=self.title if self.title else None,
            name=self.name if self.name else None,
            pmid=self.pmid if self.pmid else None,
            doi=self.doi if self.doi else None,
            urls=self.urls if self.urls else None,
        )


class MethodNode(BaseModel):
    """Node model for Method."""

    id: str
    name: str
    reported_in: DocumentNode

    @classmethod
    def from_gks(cls, method: Method) -> Self:
        """Create Node instance from GKS class."""
        document_node = DocumentNode.from_gks(method.reportedIn)
        return cls(id=method.id, name=method.name, reported_in=document_node)

    def to_gks(self) -> Method:
        """Create VA-Spec Method instance."""
        return Method(
            id=method.id,
            name=method.name if method.name else None,
            reportedIn=self.reported_in.to_gks(),
        )


class StrengthNode(BaseModel):
    """Node model of a Strength object."""

    id: str
    name: str
    mappings: str
    primary_coding: str

    @classmethod
    def from_gks(cls, strength: MappableConcept) -> Self:
        """Create Node instance from GKS class."""
        match strength.primaryCoding.system:
            case "https://civic.readthedocs.io/en/latest/model/evidence/level.html":
                node_id = f"civic.strength:{strength.primaryCoding.code.root}"
            case "AMP/ASCO/CAP (AAC) Guidelines, 2017":
                node_id = f"amp-asco-cap.strength:{strength.primaryCoding.code.root}"
            case "https://moalmanac.org/about":
                node_id = f"moalmanac.strength:{strength.primaryCoding.code.root}"
            case _:
                msg = f"Unrecognized strength concept: {strength}"
                raise ValueError(msg)
        return cls(
            id=node_id,
            name=strength.name or "",
            mappings=_Mappings(strength.mappings or []).model_dump_json(),
            primary_coding=strength.primaryCoding.model_dump_json(),
        )

    def to_gks(self) -> MappableConcept:
        """Create VA-Spec Strength instance"""
        return MappableConcept(
            name=self.name if self.name else None,
            mappings=_Mappings(json.loads(self.mappings)).root,
            primaryCoding=Coding(**json.loads(self.primary_coding))
            if self.primary_coding
            else None,
        )


class EvidenceLineNode(BaseModel):
    """Node model for an Evidence Line object."""

    id: str
    direction: Direction
    evidence_items: list[
        TherapeuticReponseStatementNode
        | DiagnosticStatementNode
        | PrognosticStatementNode
    ] = Field(min_length=1)

    @classmethod
    def from_gks(cls, evidence_line: EvidenceLine) -> Self:
        """Construct node representation of Evidence Line object"""
        evidence_line_id = f"evidence_line:{','.join(sorted(item.id for item in evidence_line.hasEvidenceItems))}"
        evidence_items = []
        for item in evidence_line.hasEvidenceItems:
            proposition_type = item.proposition.type
            match proposition_type:
                case "VariantTherapeuticResponseProposition":
                    evidence_items.append(
                        TherapeuticReponseStatementNode.from_gks(item)
                    )
                case "VariantDiagnosticProposition":
                    evidence_items.append(DiagnosticStatementNode.from_gks(item))
                case "VariantPrognosticProposition":
                    evidence_items.append(PrognosticStatementNode.from_gks(item))
                case _:
                    raise NotImplementedError
        return cls(
            id=evidence_line_id,
            direction=evidence_line.directionOfEvidenceProvided,
            evidence_items=evidence_items,
        )

    def to_gks(self) -> EvidenceLine:
        """Create EvidenceLine instance.

        To figure out: the node object just tracks IDs... maybe it should embed whole nodes
        """
        return EvidenceLine(
            directionOfEvidenceProvided=self.direction,
            hasEvidenceItems=[],  # TODO: figure out how best to populate this
        )


class StatementEvidenceBase(BaseModel):
    """Base properties for a Statement evidence node.

    Use as a mixin for a flattened statement/proposition node.
    """

    id: str
    description: str
    method: MethodNode
    documents: list[DocumentNode]
    has_strength: StrengthNode
    allele_origin_qualifier: str
    proposition_type: (
        Literal["VariantTherapeuticResponseProposition"]
        | Literal["VariantDiagnosticProposition"]
        | Literal["VariantPrognosticProposition"]
    )
    evidence_lines: list[EvidenceLineNode]


class TherapeuticReponseStatementNode(StatementEvidenceBase):
    """Node model for an evidence statement about a therapeutic response proposition"""

    predicate: TherapeuticResponsePredicate
    has_tumor_type: DiseaseNode
    has_gene_context: GeneNode
    has_subject_variant: CategoricalVariantNode
    has_therapeutic: TherapyGroupNode | DrugNode

    @classmethod
    def from_gks(
        cls,
        statement: Statement,
    ) -> Self:
        """Create Node instance from GKS class."""
        if not isinstance(statement.proposition, VariantTherapeuticResponseProposition):
            raise TypeError
        method_node = MethodNode.from_gks(statement.specifiedBy)
        strength_node = StrengthNode.from_gks(statement.strength)
        tr_proposition = statement.proposition
        evidence_line_nodes = (
            [
                EvidenceLineNode.from_gks(evidence_line)
                for evidence_line in statement.hasEvidenceLines
            ]
            if statement.hasEvidenceLines
            else []
        )
        document_nodes = (
            [DocumentNode.from_gks(d) for d in statement.reportedIn]
            if statement.reportedIn
            else []
        )
        match tr_proposition.objectTherapeutic.root:
            case TherapyGroup():
                therapeutic_node = TherapyGroupNode.from_gks(
                    tr_proposition.objectTherapeutic.root
                )
            case MappableConcept():
                therapeutic_node = DrugNode.from_gks(
                    tr_proposition.objectTherapeutic.root
                )
            case _:
                raise ValueError

        return cls(
            id=statement.id,
            description=tr_proposition.description or "",
            method=method_node,
            documents=document_nodes,
            has_strength=strength_node,
            predicate=tr_proposition.predicate,
            has_tumor_type=DiseaseNode.from_gks(tr_proposition.conditionQualifier.root),
            has_gene_context=GeneNode.from_gks(tr_proposition.geneContextQualifier),
            has_subject_variant=CategoricalVariantNode.from_gks(
                tr_proposition.subjectVariant
            ),
            has_therapeutic=therapeutic_node,
            allele_origin_qualifier=tr_proposition.alleleOriginQualifier.name,
            proposition_type="VariantTherapeuticResponseProposition",
            evidence_lines=evidence_line_nodes,
        )

    def to_gks(self) -> Statement:
        """Create a Statement containing a TR proposition"""
        return Statement(
            id=self.id,
            description=self.description if self.description else None,
            reportedIn=self.method_id,
            proposition=VariantDiagnosticProposition(),
        )  # TODO figure out more


class DiagnosticStatementNode(StatementEvidenceBase):
    """Node model for an evidence statement about a diagnostic proposition"""

    predicate: DiagnosticPredicate
    has_tumor_type: DiseaseNode
    has_gene_context: GeneNode
    has_subject_variant: CategoricalVariantNode

    @classmethod
    def from_gks(cls, statement: Statement) -> Self:
        """Create Node instance from GKS class."""
        diagnostic_proposition = statement.proposition
        if not isinstance(diagnostic_proposition, VariantDiagnosticProposition):
            raise TypeError
        method = MethodNode.from_gks(statement.specifiedBy)
        strength_node = StrengthNode.from_gks(statement.strength)
        evidence_lines = (
            [
                EvidenceLineNode.from_gks(evidence_line)
                for evidence_line in statement.hasEvidenceLines
            ]
            if statement.hasEvidenceLines
            else []
        )
        document_nodes = (
            [DocumentNode.from_gks(d) for d in statement.reportedIn]
            if statement.reportedIn
            else []
        )

        return cls(
            id=statement.id,
            description=diagnostic_proposition.description or "",
            method=method,
            documents=document_nodes,
            has_strength=strength_node,
            predicate=diagnostic_proposition.predicate,
            has_tumor_type=DiseaseNode.from_gks(
                diagnostic_proposition.objectCondition.root
            ),
            has_gene_context=GeneNode.from_gks(
                diagnostic_proposition.geneContextQualifier
            ),
            has_subject_variant=CategoricalVariantNode.from_gks(
                diagnostic_proposition.subjectVariant
            ),
            allele_origin_qualifier=diagnostic_proposition.alleleOriginQualifier.name,
            proposition_type="VariantDiagnosticProposition",
            evidence_lines=evidence_lines,
        )


class PrognosticStatementNode(StatementEvidenceBase):
    """Node model for an evidence statement about a prognostic proposition"""

    predicate: PrognosticPredicate
    has_tumor_type: DiseaseNode
    has_gene_context: GeneNode
    has_subject_variant: CategoricalVariantNode

    @classmethod
    def from_gks(cls, statement: Statement) -> Self:
        """Create Node instance from GKS class."""
        prognostic_proposition = statement.proposition
        if not isinstance(prognostic_proposition, VariantPrognosticProposition):
            raise TypeError
        method = MethodNode.from_gks(statement.specifiedBy)
        strength_node = StrengthNode.from_gks(statement.strength)
        evidence_lines = (
            [
                EvidenceLineNode.from_gks(evidence_line)
                for evidence_line in statement.hasEvidenceLines
            ]
            if statement.hasEvidenceLines
            else []
        )
        document_nodes = (
            [DocumentNode.from_gks(d) for d in statement.reportedIn]
            if statement.reportedIn
            else []
        )

        return cls(
            id=statement.id,
            description=prognostic_proposition.description or "",
            method=method,
            documents=document_nodes,
            has_strength=strength_node,
            predicate=prognostic_proposition.predicate,
            has_tumor_type=DiseaseNode.from_gks(
                prognostic_proposition.objectCondition.root
            ),
            has_gene_context=GeneNode.from_gks(
                prognostic_proposition.geneContextQualifier
            ),
            has_subject_variant=CategoricalVariantNode.from_gks(
                prognostic_proposition.subjectVariant
            ),
            allele_origin_qualifier=prognostic_proposition.alleleOriginQualifier.name,
            proposition_type="VariantPrognosticProposition",
            evidence_lines=evidence_lines,
        )
