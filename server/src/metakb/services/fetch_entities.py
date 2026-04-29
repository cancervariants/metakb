"""Retrieve data for specific biomedical entities.

For now, this mostly involves post-processing data from user searches, but could
involve separate fetching operations in the future.
"""

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.base import EvidenceLine, Statement


def _collect_unique_entities(statements: list[Statement], entity_attr: str) -> list:
    """Collect unique entities from nested evidence, stopping recursion at Statements.

    :param statements: list of assertions provided in a response
    :param entity_attr: name of property on proposition (e.g. "geneContextQualifier")
    :return: list of unique child entities within statements
    """
    entities_by_id: dict[str, MappableConcept] = {}

    def extract_entity(stmt: Statement) -> None:
        entity = getattr(getattr(stmt, "proposition", None), entity_attr, None)
        if entity is not None and getattr(entity, "id", None):
            entities_by_id[entity.id] = entity

    def visit_evidence_line(line: EvidenceLine) -> None:
        for item in line.hasEvidenceItems or []:
            if isinstance(item, Statement):
                # collect, but DO NOT recurse into this statement
                extract_entity(item)
            elif isinstance(item, EvidenceLine):
                visit_evidence_line(item)
            else:
                msg = f"Unexpected evidence item type: {type(item)}"
                raise TypeError(msg)

    # start from root statements, but do NOT include their own entities
    for statement in statements:
        for evidence_line in getattr(statement, "hasEvidenceLines", None) or []:
            visit_evidence_line(evidence_line)

    return list(entities_by_id.values())


def _update_gene_from_civic_gid(
    gene: MappableConcept, civic_gene: MappableConcept
) -> MappableConcept:
    """Add source-provided data (e.g. mappings) onto original normalized entity object"""
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
    child_genes = _collect_unique_entities(assertions, "geneContextQualifier")
    for child_gene in child_genes:
        if child_gene.id.startswith("civic.gid:"):
            _update_gene_from_civic_gid(gene, child_gene)
    return gene


def _update_variation_from_moa_variation(
    variation: CategoricalVariant, moa_variation: CategoricalVariant
) -> CategoricalVariant:
    """Add source-provided data onto original normalized entity object"""
    if moa_variation.mappings:
        variation.mappings.extend(moa_variation.mappings)
    return variation


def _update_variation_from_civic_variation(
    variation: CategoricalVariant, civic_variation: CategoricalVariant
) -> CategoricalVariant:
    """Add source-provided data onto original normalized entity object"""
    variation.mappings.append(
        ConceptMapping(
            relation=Relation.EXACT_MATCH,
            coding=Coding(
                id=civic_variation.id,
                system="https://www.civicdb.org/molecular-profiles",
                code=code(civic_variation.id.split(":")[-1]),
            ),
        )
    )
    existing_description = next(
        (i for i in variation.extensions if i.name == "variation_description"), None
    )
    if not existing_description and civic_variation.description:
        variation.extensions.append(
            Extension(
                name="variation_description",
                value={
                    "source": civic_variation.id,
                    "description": civic_variation.description,
                },
            )
        )

    variation.mappings.extend(
        [
            m
            for m in civic_variation.mappings
            if m.coding.id.startswith(
                ("clingen.allele:", "clinvar.variation", "dbsnp:")
            )
        ]
    )
    return variation


def extract_variation_from_assertions(
    assertions: list[Statement],
) -> CategoricalVariant:
    """Given MetaKB assertions, gather the subject catvar with source-provided data added where needed"""
    catvar = assertions[0].proposition.subjectVariant
    child_catvars = _collect_unique_entities(assertions, "subjectVariant")
    for child_catvar in child_catvars:
        if child_catvar.id.startswith("moa.variant:"):
            catvar = _update_variation_from_moa_variation(catvar, child_catvar)
        elif child_catvar.id.startswith("civic.mpid:"):
            catvar = _update_variation_from_civic_variation(catvar, child_catvar)
    # dedup mappings just in case
    catvar.mappings = list(
        {m.coding.id: m for m in catvar.mappings if m.coding.id}.values()
    )
    return catvar
