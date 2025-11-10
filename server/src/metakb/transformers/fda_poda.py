from pathlib import Path
from typing import ClassVar

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.va_spec.base import Statement
from pydantic import BaseModel

from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import (
    MethodId,
    Transformer,
    _HarvestedData,
    _TransformedRecordsCache,
)


class CivicHarvestedData(_HarvestedData):
    """Define output for harvested data from CIViC"""

    genes: list[dict]
    evidence: list[dict]
    molecular_profiles: list[dict]
    assertions: list[dict]


class _FdaTransformedCache(_TransformedRecordsCache):
    """Create model for caching FDA PODA data"""

    categorical_variants: ClassVar[dict[str, CategoricalVariant]] = {}
    evidence: ClassVar[
        dict[
            str,
            Statement,
        ]
    ] = {}


class FdaPodaTransformer(Transformer):
    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )
        # Method will always be the same
        self.processed_data.methods = [
            self.methods_mapping[MethodId.FDA_APPROV_SOP.value]
        ]
        self._cache = self._create_cache()

    def _create_cache(self) -> _FdaTransformedCache:
        return _FdaTransformedCache()
