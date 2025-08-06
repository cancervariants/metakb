"""Load MetaKB data into Neo4j database."""

import json

from neomodel import StructuredNode

from metakb.database.models import (
    Allele,
    CategoricalVariant,
    DefiningAlleleConstraint,
    LiteralSequenceExpression,
    ReferenceLengthExpression,
    SequenceLocation,
)


def _add_allele(allele: dict) -> StructuredNode:
    allele_node = Allele(
        id_=allele["id"],
        name=allele["name"],
        expression_hgvs_g=["sdflkjsdf"],
        expression_hgvs_c=["sdflkjsdf"],
        expression_hgvs_p=["sdflkjsdf"],
    ).save()
    sl = allele["location"]

    sl_node = SequenceLocation(
        id_=sl["id"],
        start=sl.get("start"),
        end=sl.get("end"),
        refget_accession=sl["sequenceReference"]["refgetAccession"],
        sequence=sl.get("sequence"),
    ).save()
    allele_node.location.connect(sl_node)

    if allele["state"]["type"] == "LiteralSequenceExpression":
        state_node = LiteralSequenceExpression(
            sequence=allele["state"]["sequence"]
        ).save()
    else:
        state_node = ReferenceLengthExpression(
            length=allele["state"]["length"],
            repeat_subunit_length=allele["state"]["repeatSubunitLength"],
            sequence=allele["state"]["sequence"],
        ).save()
    allele_node.state.connect(state_node)
    return allele_node


def _add_dac_cv(
    catvar: dict,
) -> None:
    constraint = catvar["constraints"][0]
    allele = constraint["allele"]

    catvar_node = CategoricalVariant(
        id_=catvar["id"],
        description=catvar.get("description"),
        aliases=catvar.get("aliases"),
        extensions=json.dumps(catvar["extensions"]) if "extensions" in catvar else None,
        mappings=json.dumps(catvar["mappings"]) if "mappings" in catvar else None,
    ).save()

    constraint_node = DefiningAlleleConstraint().save()
    catvar_node.constraint.connect(constraint_node)

    allele_node = _add_allele(allele)
    constraint_node.defining_allele.connect(allele_node)

    for member_allele in catvar.get("members", []):
        member_allele_node = _add_allele(member_allele)
        catvar_node.members.connect(member_allele_node)
