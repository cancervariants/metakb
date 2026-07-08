import json
from pathlib import Path

import pytest
from ga4gh.core.models import Extension
from ga4gh.va_spec.aac_2017.models import VariantClinicalSignificanceStatement

from metakb.schemas.app import SourceName
from metakb.source_data import SourceDataStore
from metakb.transformers.mci import MciTransformer


@pytest.fixture
def transformer() -> MciTransformer:
    return MciTransformer(src_data_store=SourceDataStore(src_name=SourceName.MCI))


@pytest.fixture
def mci_harvested_data_path(test_data_dir: Path) -> Path:
    return test_data_dir / "transformers" / "mci_harvested_data.json"


@pytest.fixture(scope="session")
def mci_statements(
    mci_harvested_data_path: Path,
) -> dict[str, VariantClinicalSignificanceStatement]:
    with mci_harvested_data_path.open() as f:
        return {
            d["id"]: VariantClinicalSignificanceStatement(**d)
            for d in json.load(f)["statements"]
        }


@pytest.mark.asyncio
async def test_mci_transform(
    transformer: MciTransformer,
    mci_harvested_data_path: Path,
):
    result = await transformer.transform(mci_harvested_data_path)

    statement = next(s for s in result.evidence)
    assert statement.id == "mci.statement:rsVJ6-pOVi4M6CKD-dzXowHq0M9X2_X8"
    assert statement.specifiedBy.id == "mci.method:1"
    assert (
        statement.proposition.subjectVariant.id
        == "mci.cv:ga4gh_VA.5ajmZMdX9tr2XjgGNlw-wNl4_yG_FaDe"
    )
    assert statement.proposition.geneContextQualifier.id == "mci.gene:NRAS"
    assert (
        statement.proposition.objectCondition.root.id
        == "mci.cs:nj_j0JvsOAcfIIOThgqTkp4M9oWM7w1h"
    )
    assert statement.strength.id == "amp_asco_cap:B"
    assert statement.strength.extensions == [
        Extension(name="metakb_display_value", value="B")
    ]

    aggr_statement = next(s for s in result.assertions)
    assert aggr_statement.id == "metakb.assertion:QMPgi5533ZvUISJ7ePt3Xt2POvnY9aEF"
    assert (
        aggr_statement.proposition.subjectVariant.id
        == "metakb.cv:DAC.VA.5ajmZMdX9tr2XjgGNlw-wNl4_yG_FaDe"
    )
    assert aggr_statement.proposition.geneContextQualifier.id == "metakb.gene:hgnc_7989"
    assert (
        aggr_statement.proposition.objectCondition.root.id
        == "metakb.cs:sDKFIiIdr6Mxyq_bgCTYPLOQso3Efamu"
    )
