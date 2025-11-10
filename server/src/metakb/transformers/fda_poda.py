from pathlib import Path

from ga4gh.cat_vrs.models import CategoricalVariant

from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import MethodId, Transformer, _HarvestedData


class CivicHarvestedData(_HarvestedData):
    """Define output for harvested data from CIViC"""

    genes: list[dict]
    evidence: list[dict]
    molecular_profiles: list[dict]
    assertions: list[dict]


class CivicTransformer(Transformer):
    """A class for transforming CIViC to the common data model."""

    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize CIViC Transformer class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested CIViC data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        # Method will always be the same
        self.processed_data.methods = [
            self.methods_mapping[MethodId.FDA_APPROV_SOP.value]
        ]
        self._cache = self._create_cache()
