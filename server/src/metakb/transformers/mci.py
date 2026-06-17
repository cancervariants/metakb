"""Transform AMP/ASCO/CAP statements from the MCI project into MetaKB-ready format"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from tqdm import tqdm
from ga4gh.cat_vrs.models import CategoricalVariant

from metakb.harvesters.mci import MciHarvestedData
from metakb.schemas.data import TransformedData
from metakb.transformers.base import Transformer

if TYPE_CHECKING:
    from ga4gh.va_spec.aac_2017 import VariantClinicalSignificanceStatement
    from ga4gh.va_spec.base import Statement


class MciTransformer(Transformer):
    """Transform MCI data."""

    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform MCI statements JSON dump to common data model.

        Will store transformed results in ``processed_data`` instance variable.

        :param harvested_data: FDA-PODA harvested data
        :return: transformed statements
        """
        with harvested_data_path.open() as f:
            harvested_data = MciHarvestedData(**json.load(f))
        statements: list[VariantClinicalSignificanceStatement | Statement] = []
        assertions: dict[str, VariantClinicalSignificanceStatement | Statement] = {}
        for ev_item in tqdm(harvested_data.statements):
            # TODO
            # double check that conditionsets and therapygroups are ID'd
            # and documents
            # ensure metakb_display_value in strength.extensions
            statements.append(ev_item)
            await self._upsert_assertion_from_evidence(ev_item, assertions)
        return TransformedData(
            evidence=statements, assertions=list(assertions.values())
        )

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        raise NotImplementedError
