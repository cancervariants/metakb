import json
from pathlib import Path

import pytest
from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.base import MembershipOperator, Therapeutic, TherapyGroup

from metakb.harvesters.moa import MoaHarvestedData
from metakb.transformers.moa import MoaTransformer


@pytest.fixture
def transformer() -> MoaTransformer:
    return MoaTransformer()


@pytest.fixture(scope="session")
def moa_variants(test_data_dir: Path) -> dict[str, dict]:
    with (
        test_data_dir / "transformers" / "moa_create_variants_input.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def moa_catvars(test_data_dir: Path) -> dict[str, CategoricalVariant]:
    with (
        test_data_dir / "transformers" / "moa_normalize_variants_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: CategoricalVariant(**v) for k, v in data.items()}


@pytest.fixture(scope="session")
def moa_harvested_data(test_data_dir: Path) -> MoaHarvestedData:
    with (test_data_dir / "transformers" / "moa_harvested_data.json").open() as f:
        data = json.load(f)
        return MoaHarvestedData(genes=[], variants=[], **data)


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


@pytest.mark.asyncio
async def test_normalize_moa_variant(
    transformer: MoaTransformer, moa_catvars: dict[str, CategoricalVariant]
):
    result = await transformer._normalize_variant(moa_catvars["moa.variant:120"])
    assert result is not None
    assert result.id == "metakb.cv:FC.hgnc_11110"
    assert result.name == "ARID1A Mutation"
    assert result.constraints
    assert len(result.constraints) == 1

    result = await transformer._normalize_variant(moa_catvars["moa.variant:141"])
    assert result is not None
    assert result.id == "metakb.cv:PSQ.VA.pDuCLNI3mHF25uUPNSDM8LbP8p4Fsuay"
    assert result.name == "BCOR N1425S"
    assert result.constraints
    assert len(result.constraints) == 1
    assert isinstance(result.constraints[0], DefiningAlleleConstraint)

    result = await transformer._normalize_variant(moa_catvars["moa.variant:27"])
    assert result is None

    result = await transformer._normalize_variant(moa_catvars["moa.variant:286"])
    assert result is None


def test_create_moa_therapeutic(transformer: MoaTransformer):
    result = transformer._create_moa_therapy("Nilotinib", "Targeted therapy")
    assert result == Therapeutic(
        root=MappableConcept(
            id="moa.drug:Nilotinib",
            extensions=[
                Extension(
                    name="moa_therapy_type",
                    value="Targeted therapy",
                )
            ],
            conceptType="Drug",
            name="Nilotinib",
        )
    )

    result = transformer._create_moa_therapy(
        "Azacitidine + Panobinostat", "Combination therapy"
    )
    assert result == Therapeutic(
        root=TherapyGroup(
            id="moa.tg:wbkLIrtKaCrCn0Vni_lJnf2TbDvnv3Kp",
            extensions=[
                Extension(
                    name="moa_therapy_type",
                    value="Combination therapy",
                )
            ],
            therapies=[
                MappableConcept(
                    id="moa.drug:Azacitidine",
                    conceptType="Drug",
                    name="Azacitidine",
                ),
                MappableConcept(
                    id="moa.drug:Panobinostat",
                    conceptType="Drug",
                    name="Panobinostat",
                ),
            ],
            membershipOperator=MembershipOperator("AND"),
        )
    )

    with pytest.raises(ValueError):  # noqa: PT011
        transformer._create_moa_therapy(None, None)


@pytest.mark.asyncio
async def test_transform(
    transformer: MoaTransformer, moa_harvested_data: MoaHarvestedData
):
    await transformer.transform(moa_harvested_data)
    result = transformer.processed_data

    statement = next(s for s in result.statements if s.id == "moa.assertion:66")
    assert statement

    aggr_statement = next(
        s
        for s in result.statements
        if s.id == "metakb.assertion:F-6C4CgAIyw3cf2zdxRVOVfe3L1GbHqa"
    )
    assert aggr_statement
