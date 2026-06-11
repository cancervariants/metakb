import json
from pathlib import Path

import pytest
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.aac_2017.models import AmpAscoCapStrengthCode
from ga4gh.va_spec.base import Statement, System

from metakb.transformers.methodology import (
    src_strength_to_vicc_code,
)


@pytest.fixture(scope="session")
def statements(test_data_dir: Path) -> dict[str, Statement]:
    with (
        test_data_dir / "transformers" / "base_construct_statements_input.json"
    ).open() as f:
        data = json.load(f)
        return {k: Statement(**v) for k, v in data.items()}


def test_moa_strength_to_vicc_code():
    moa = MappableConcept(
        id="moa.strength:FDA-Approved",
        extensions=[Extension(name="metakb_display_value", value="A")],
        primaryCoding=Coding(
            system="https://moalmanac.org/about", code=code("FDA-Approved")
        ),
    )
    response = src_strength_to_vicc_code(moa)
    assert response.id == "vicc:e000002"
    assert response.name == "FDA recognized evidence"
    assert response.extensions == [Extension(name="metakb_display_value", value="A")]
    assert response.mappings == [
        ConceptMapping(
            coding=Coding(
                system="https://moalmanac.org/about", code=code("FDA-Approved")
            ),
            relation=Relation("exactMatch"),
        ),
        ConceptMapping(
            coding=Coding(system="AMP/ASCO/CAP Guidelines, 2017", code=code("Level A")),
            relation=Relation.RELATED_MATCH,
        ),
    ]


def test_civic_strength_to_vicc_code():
    civic = MappableConcept(
        id="civic.strength:C",
        extensions=[Extension(name="metakb_display_value", value="C")],
        name="Case study",
        primaryCoding=Coding(
            system="https://civic.readthedocs.io/en/latest/model/evidence/level.html",
            code=code("C"),
        ),
        mappings=[
            ConceptMapping(
                coding=Coding(
                    name="clinical case study evidence",
                    system="https://go.osu.edu/evidence-codes",
                    code=code("e000008"),
                ),
                relation=Relation("exactMatch"),
            )
        ],
    )
    response = src_strength_to_vicc_code(civic)
    assert response.id == "vicc:e000008"
    assert response.name == "case study evidence"
    assert response.extensions == [Extension(name="metakb_display_value", value="C")]
    assert response.mappings == [
        ConceptMapping(
            coding=Coding(
                system="https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                code=code("C"),
            ),
            relation=Relation("exactMatch"),
        ),
        ConceptMapping(
            coding=Coding(system="AMP/ASCO/CAP Guidelines, 2017", code=code("Level C")),
            relation=Relation.RELATED_MATCH,
        ),
    ]


def test_aac_strength_to_vicc_code():
    aac = MappableConcept(
        id="amp_asco_cap:strong",
        extensions=[Extension(name="metakb_display_value", value="strong")],
        conceptType=None,
        name=None,
        primaryCoding=Coding(
            system=System.AMP_ASCO_CAP.value,
            code=code(root=AmpAscoCapStrengthCode.STRONG.value),
        ),
    )
    response = src_strength_to_vicc_code(aac)
    assert response.id == "vicc:e000008"
    assert response.name == "case study evidence"
    assert response.extensions == [Extension(name="metakb_display_value", value="C")]
    assert response.mappings == [
        ConceptMapping(
            coding=Coding(
                system="https://civic.readthedocs.io/en/latest/model/evidence/level.html",
                code=code("C"),
            ),
            relation=Relation("exactMatch"),
        ),
        ConceptMapping(
            coding=Coding(system="AMP/ASCO/CAP Guidelines, 2017", code=code("Level C")),
            relation=Relation.RELATED_MATCH,
        ),
    ]


def test_fda_strength_to_vicc_code():
    pass  # TODO


def test_initialize_assertion(statements: dict[str, Statement]):
    pass  # TODO


def test_merge_assertions():
    pass  # TODO


def test_add_evidence_to_assertion():
    pass  # TODO
