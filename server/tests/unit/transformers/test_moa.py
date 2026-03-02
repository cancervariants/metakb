import pytest
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import Coding, ConceptMapping, Extension, Relation, code

from metakb.transformers.base import Transformer
from metakb.transformers.moa import MoaTransformer


@pytest.fixture(scope="session")
def transformer() -> MoaTransformer:
    return MoaTransformer()


@pytest.fixture(scope="session")
def moa_variants() -> dict[str, dict]:
    return {
        "1": {
            "id": 1,
            "feature_type": "rearrangement",
            "gene1": "BCR",
            "gene2": "ABL1",
            "locus": None,
            "rearrangement_type": "Fusion",
            "feature": "BCR--ABL1 Fusion",
        },
        "30": {
            "id": 30,
            "feature_type": "rearrangement",
            "gene1": "FGFR2",
            "gene2": None,
            "locus": None,
            "rearrangement_type": None,
            "feature": "FGFR2",
        },
        "66": {
            "id": 66,
            "alternate_allele": "T",
            "cdna_change": "c.944C>T",
            "chromosome": "9",
            "end_position": "133748283",
            "exon": "5",
            "feature_type": "somatic_variant",
            "gene": "ABL1",
            "protein_change": "p.T315I",
            "reference_allele": "C",
            "rsid": "rs121913459",
            "start_position": "133748283",
            "variant_annotation": "Missense",
            "feature": "ABL1 p.T315I (Missense)",
        },
        "74": {
            "id": 74,
            "alternate_allele": None,
            "cdna_change": None,
            "chromosome": "9",
            "end_position": None,
            "exon": None,
            "feature_type": "somatic_variant",
            "gene": "ABL1",
            "protein_change": None,
            "reference_allele": None,
            "rsid": None,
            "start_position": None,
            "variant_annotation": None,
            "feature": "ABL1",
        },
        "118": {
            "id": 118,
            "alternate_allele": None,
            "cdna_change": None,
            "chromosome": None,
            "end_position": None,
            "exon": None,
            "feature_type": "somatic_variant",
            "gene": "ARID1A",
            "protein_change": None,
            "reference_allele": None,
            "rsid": None,
            "start_position": None,
            "variant_annotation": "Nonsense",
            "feature": "ARID1A (Nonsense)",
        },
    }


@pytest.mark.ci_ok
def test_create_moa_variant(transformer: MoaTransformer, moa_variants: dict[str, dict]):
    result = transformer._create_moa_variant(moa_variants["1"])
    assert result == CategoricalVariant(
        id="moa.variant:1",
        name="BCR--ABL1 Fusion",
        extensions=[Extension(name="moa_feature_type", value="rearrangement")],
    )

    result = transformer._create_moa_variant(moa_variants["30"])
    assert result == CategoricalVariant(
        id="moa.variant:30",
        name="FGFR2",
        extensions=[Extension(name="moa_feature_type", value="rearrangement")],
    )

    result = transformer._create_moa_variant(moa_variants["66"])
    assert result == CategoricalVariant(
        id="moa.variant:66",
        name="ABL1 T315I",
        extensions=[
            Extension(
                name="moa_representative_coordinate",
                value={
                    "chromosome": "9",
                    "start_position": "133748283",
                    "end_position": "133748283",
                    "reference_allele": "C",
                    "alternate_allele": "T",
                    "cdna_change": "c.944C>T",
                    "protein_change": "p.T315I",
                    "exon": "5",
                },
            ),
            Extension(name="moa_feature_type", value="somatic_variant"),
            Extension(name="moa_variant_annotation", value="Missense"),
        ],
        mappings=[
            ConceptMapping(
                coding=Coding(
                    system="https://www.ncbi.nlm.nih.gov/snp/", code=code("rs121913459")
                ),
                relation=Relation("relatedMatch"),
            )
        ],
    )

    result = transformer._create_moa_variant(moa_variants["74"])
    assert result == CategoricalVariant(
        id="moa.variant:74",
        name="ABL1 Mutation",
        extensions=[
            Extension(
                name="moa_representative_coordinate",
                value={
                    "chromosome": "9",
                    "start_position": None,
                    "end_position": None,
                    "reference_allele": None,
                    "alternate_allele": None,
                    "cdna_change": None,
                    "protein_change": None,
                    "exon": None,
                },
            ),
            Extension(name="moa_feature_type", value="somatic_variant"),
        ],
    )

    result = transformer._create_moa_variant(moa_variants["118"])
    assert result == CategoricalVariant(
        id="moa.variant:118",
        name="ARID1A (Nonsense)",
        extensions=[
            Extension(name="moa_feature_type", value="somatic_variant"),
            Extension(name="moa_variant_annotation", value="Nonsense"),
        ],
    )


def test_normalize_moa_variant(transformer: MoaTransformer):
    # TODO
    pass


def test_create_moa_therapeutic(transformer: Transformer):
    # TODO
    pass


def test_transform(transformer: Transformer):
    # TODO
    pass
