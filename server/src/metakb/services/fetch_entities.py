"""Retrieve data for specific biomedical entities."""

from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.base import EvidenceLine, Statement


def _collect_unique_genes(statements: list[Statement]) -> list[MappableConcept]:
    """Collect unique genes from nested evidence only (exclude root-level genes)."""
    genes_by_id: dict[str, MappableConcept] = {}

    def visit_statement(stmt: Statement, include_self: bool = True) -> None:
        if include_self:
            gene = getattr(
                getattr(stmt, "proposition", None), "geneContextQualifier", None
            )
            if gene is not None and getattr(gene, "id", None):
                genes_by_id[gene.id] = gene

        for evidence_line in getattr(stmt, "hasEvidenceLines", None) or []:
            visit_evidence_line(evidence_line)

    def visit_evidence_line(line: EvidenceLine) -> None:
        for item in line.hasEvidenceItems or []:
            if isinstance(item, Statement):
                visit_statement(item, include_self=True)
            elif isinstance(item, EvidenceLine):
                visit_evidence_line(item)
            else:
                msg = f"Unexpected evidence item type: {type(item)}"
                raise TypeError(msg)

    # root statements: do NOT include their own gene
    for statement in statements:
        visit_statement(statement, include_self=False)

    return list(genes_by_id.values())


def _update_gene_from_civic_gid(
    gene: MappableConcept, civic_gene: MappableConcept
) -> MappableConcept:
    gene.mappings.append(
        ConceptMapping(
            relation=Relation.EXACT_MATCH,
            coding=Coding(
                id=civic_gene.id,
                system="https://civicdb.org/features/",
                code=code(civic_gene.id.split(":")[1]),
            ),
        )
    )
    if not gene.get_extensions_by_name("gene_description"):  # noqa: SIM102
        if civic_description := civic_gene.get_extensions_by_name("description"):
            gene.extensions.append(
                Extension(
                    name="gene_description",
                    value={
                        "source": civic_gene.id,
                        "description": civic_description.value,
                    },
                )
            )

    return gene


def extract_gene_from_assertions(assertions: list[Statement]) -> MappableConcept:
    """Given MetaKB assertions, gather the gene and source-provided gene concepts."""
    gene = assertions[0].proposition.geneContextQualifier
    child_genes = _collect_unique_genes(assertions)
    for child_gene in child_genes:
        _update_gene_from_civic_gid(gene, child_gene)
    return gene
