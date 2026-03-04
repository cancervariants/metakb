"""Unit tests for Transformer base helpers."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.vrs.models import Allele

from metakb.repository.neo4j_models import CategoricalVariantNode
from metakb.transformers.base import (
    Transformer,
    _TransformedRecordsCache,
)


class _DummyCache(_TransformedRecordsCache):
    pass


class _DummySeqRepoAccess:
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


class _DummyVariationNormalizer:
    def __init__(self, aliases: list[str], gene_name: str | None = "BRAF") -> None:
        self.seqrepo_access = _DummySeqRepoAccess(aliases)
        self.gnomad_vcf_to_protein_handler = SimpleNamespace(
            mane_transcript=SimpleNamespace(
                transcript_mappings=SimpleNamespace(
                    get_gene_symbol_from_refeq_protein=lambda _: gene_name,
                    get_gene_symbol_from_ensembl_protein=lambda _: gene_name,
                )
            )
        )


class _DummyTransformer(Transformer):
    async def transform(self, *args, **kwargs) -> None:  # noqa: ARG002
        return None

    @staticmethod
    def _create_cache() -> _DummyCache:
        return _DummyCache()


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


def _get_transformer(
    tmp_path,
    aliases: list[str],
    gene_name: str | None = "BRAF",
) -> _DummyTransformer:
    normalizers = Mock()
    normalizers.variation_normalizer = _DummyVariationNormalizer(aliases, gene_name)
    if gene_name:
        normalizers.normalize_gene = Mock(
            return_value=(
                SimpleNamespace(gene=SimpleNamespace(name=gene_name)),
                "hgnc:1097",
            )
        )
    else:
        normalizers.normalize_gene = Mock(
            return_value=(SimpleNamespace(gene=None), None)
        )
    return _DummyTransformer(data_dir=tmp_path, normalizers=normalizers)


def test_get_normalized_protein_consequence_name(tmp_path) -> None:
    transformer = _get_transformer(tmp_path, aliases=["refseq:NP_004324.2"])
    allele = _get_test_allele(ref="V", alt="E")
    normalized_name = transformer.get_normalized_protein_consequence_name(allele)
    assert normalized_name == "BRAF V600E"


def test_get_normalized_protein_consequence_name_unsupported_edit(tmp_path) -> None:
    transformer = _get_transformer(tmp_path, aliases=["refseq:NP_004324.2"])
    allele = _get_test_allele(ref="V", alt="EE")
    with pytest.raises(NotImplementedError):
        transformer.get_normalized_protein_consequence_name(allele)


def test_get_normalized_protein_consequence_name_missing_location_sequence(
    tmp_path,
) -> None:
    transformer = _get_transformer(tmp_path, aliases=["refseq:NP_004324.2"])
    allele = _get_test_allele(include_location_sequence=False)
    with pytest.raises(NotImplementedError):
        transformer.get_normalized_protein_consequence_name(allele)


def test_get_normalized_protein_consequence_name_non_protein_sequence(tmp_path) -> None:
    transformer = _get_transformer(tmp_path, aliases=["refseq:NC_000007.14"])
    allele = _get_test_allele(ref="V", alt="E")
    with pytest.raises(ValueError, match="is not a protein sequence"):
        transformer.get_normalized_protein_consequence_name(allele)


def test_categorical_variant_node_uses_normalized_name_for_name() -> None:
    allele = _get_test_allele()
    cv = CategoricalVariant(
        id="civic.mpid:1",
        name="BRAF V600E",
        constraints=[DefiningAlleleConstraint(allele=allele)],
    )
    cv_node = CategoricalVariantNode.from_gks(cv)
    assert cv_node.name == "BRAF V600E"
