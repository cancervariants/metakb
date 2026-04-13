"""Unit tests for Transformer base helpers."""

import pytest
from cool_seq_tool.handlers import SeqRepoAccess
from cool_seq_tool.sources import TranscriptMappings
from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    Constraint,
    DefiningAlleleConstraint,
)
from ga4gh.vrs.models import Allele

from metakb.repository.neo4j_models import CategoricalVariantNode
from metakb.transformers.catvars import get_normalized_protein_consequence_name


class _DummySeqRepoAccess(SeqRepoAccess):
    def __init__(self, aliases: list[str]) -> None:
        self._aliases = aliases

    def translate_alias(self, _: str) -> tuple[list[str], None]:
        return self._aliases, None

    def translate_identifier(self, _: str) -> tuple[list[str], None]:
        return self._aliases, None

    @staticmethod
    def extract_sequence_type(alias: str) -> str | None:
        if "refseq:NP_" in alias or "refseq:XP_" in alias:
            return "p"
        return "g"


def _get_test_allele(
    ref: str = "V",
    alt: str = "E",
    include_location_sequence: bool = True,
) -> Allele:
    location = {
        "id": "ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
        "type": "SequenceLocation",
        "sequenceReference": {
            "type": "SequenceReference",
            "refgetAccession": "SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
        },
        "start": 599,
        "end": 600,
    }
    if include_location_sequence:
        location["sequence"] = ref
    return Allele(
        id="ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
        location=location,
        state={"type": "LiteralSequenceExpression", "sequence": alt},
    )


class _DummyTxMappings(TranscriptMappings):
    def __init__(self, gene_name: str | None = "BRAF") -> None:
        self.get_gene_symbol_from_refseq_protein = lambda _: gene_name
        self.get_gene_symbol_from_ensembl_protein = lambda _: gene_name


def test_get_normalized_protein_consequence_name() -> None:
    allele = _get_test_allele(ref="V", alt="E")
    normalized_name = get_normalized_protein_consequence_name(
        _DummySeqRepoAccess(["refseq:NP_004324.2"]), _DummyTxMappings(), allele
    )
    assert normalized_name == "BRAF V600E"


def test_get_normalized_protein_consequence_name_unsupported_edit() -> None:
    allele = _get_test_allele(ref="V", alt="EE")
    with pytest.raises(NotImplementedError):
        get_normalized_protein_consequence_name(
            _DummySeqRepoAccess(["refseq:NP_004324.2"]), _DummyTxMappings(), allele
        )


def test_get_normalized_protein_consequence_name_missing_location_sequence() -> None:
    allele = _get_test_allele(include_location_sequence=False)
    with pytest.raises(NotImplementedError):
        get_normalized_protein_consequence_name(
            _DummySeqRepoAccess(["refseq:NP_004324.2"]), _DummyTxMappings(), allele
        )


def test_get_normalized_protein_consequence_name_non_protein_sequence(tmp_path) -> None:
    allele = _get_test_allele(ref="V", alt="E")
    with pytest.raises(ValueError, match="is not a protein sequence"):
        get_normalized_protein_consequence_name(
            _DummySeqRepoAccess(["refseq:NC_000007.14"]), _DummyTxMappings(), allele
        )


def test_categorical_variant_node_uses_normalized_name_for_name() -> None:
    allele = _get_test_allele()
    cv = CategoricalVariant(
        id="civic.mpid:1",
        name="BRAF V600E",
        constraints=[Constraint(root=DefiningAlleleConstraint(allele=allele))],
    )
    cv_node = CategoricalVariantNode.from_gks(cv)
    assert cv_node.name == "BRAF V600E"
