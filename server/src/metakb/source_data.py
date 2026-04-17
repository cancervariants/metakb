"""Provide the ``SourceDataStore`` class for managing data acquired and transformed from sources

This class is useful across different parts of the ingest pipeline for standardizing
how files are saved, where they're located, etc.
"""

from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2
from typing import ClassVar

from pydantic import BaseModel

from metakb.config import get_config
from metakb.schemas.app import SourceName
from metakb.schemas.data import TransformedData


class SourceDataStore(BaseModel):
    """Manage on-disk storage locations for source harvest and transform artifacts."""

    TIMESTAMP_FMT: ClassVar[str] = "%Y%m%d%H%M%S"
    _FILENAME_PART_COUNT: ClassVar[int] = 3

    src_name: SourceName
    harvested_dir: Path | None = None
    transformed_dir: Path | None = None

    def _get_harvested_dir(self) -> Path:
        """Get directory for harvested data"""
        if self.harvested_dir:
            return self.harvested_dir
        return get_config().data_dir / self.src_name / "harvested"

    def _get_transformed_dir(self) -> Path:
        """Get directory for transformed data"""
        if self.transformed_dir:
            return self.transformed_dir
        return get_config().data_dir / self.src_name / "transformed"

    @classmethod
    def _parse_timestamp(cls, path: Path) -> datetime | None:
        """Parse a timestamp from a MetaKB-managed filename.

        :param path: File path whose stem should contain a trailing timestamp.
        :returns: Parsed UTC timestamp, or ``None`` if parsing fails.
        """
        parts = path.stem.split("_")
        if len(parts) < cls._FILENAME_PART_COUNT:
            return None

        ts_str = parts[-1]
        try:
            return datetime.strptime(ts_str, cls.TIMESTAMP_FMT).replace(tzinfo=UTC)
        except ValueError:
            return None

    @classmethod
    def _get_timestamp_str(cls) -> str:
        """Return the current UTC timestamp string for filenames.

        :returns: Timestamp string matching :attr:`TIMESTAMP_FMT`.
        """
        return datetime.now(UTC).strftime(cls.TIMESTAMP_FMT)

    @classmethod
    def _get_latest_file(cls, directory: Path, prefix: str) -> Path:
        """Return the most recent file in ``directory`` matching ``prefix``.

        :param directory: Directory containing candidate files.
        :param prefix: Filename prefix ending in an underscore.
        :returns: Path to the most recent matching file.
        :raise FileNotFoundError: If no valid matching files are found.
        """
        candidates: list[tuple[Path, datetime]] = []

        for path in directory.glob(f"{prefix}*"):
            if not path.is_file():
                continue
            timestamp = cls._parse_timestamp(path)
            if timestamp is not None:
                candidates.append((path, timestamp))

        if not candidates:
            msg = f"No valid files found for prefix '{prefix}' in {directory}"
            raise FileNotFoundError(msg)

        return max(candidates, key=lambda item: item[1])[0]

    @staticmethod
    def _write_text(path: Path, data: str) -> None:
        """Write text data to disk.

        :param path: Destination path.
        :param data: Text to write.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{data}\n", encoding="utf-8")

    def _build_harvested_path(self, suffix: str) -> Path:
        """Construct a timestamped harvested artifact path.

        :param suffix: File suffix including leading dot, e.g. ``.json`` or ``.pkl``.
        :returns: Destination path for a harvested artifact.
        """
        timestamp = self._get_timestamp_str()
        return (
            self._get_harvested_dir() / f"{self.src_name}_harvest_{timestamp}{suffix}"
        )

    def _build_transformed_path(self, suffix: str = ".json") -> Path:
        """Construct a timestamped transformed artifact path.

        :param suffix: File suffix including leading dot.
        :returns: Destination path for a transformed artifact.
        """
        timestamp = self._get_timestamp_str()
        return self._get_transformed_dir() / f"{self.src_name}_cdm_{timestamp}{suffix}"

    def get_latest_harvested_file(self) -> Path:
        """Return the most recent harvested file for this source.

        Files are expected to follow the naming convention::

            <src_name>_harvest_<timestamp><suffix>

        where ``<timestamp>`` matches :attr:`TIMESTAMP_FMT`.

        :returns: Path to the most recent harvested file.
        :raise FileNotFoundError: If no matching harvested files are found.
        """
        prefix = f"{self.src_name}_harvest_"
        return self._get_latest_file(self._get_harvested_dir(), prefix)

    def get_latest_transformed_file(self) -> Path:
        """Return the most recent transformed file for this source.

        Files are expected to follow the naming convention::

            <src_name>_cdm_<timestamp><suffix>

        where ``<timestamp>`` matches :attr:`TIMESTAMP_FMT`.

        :returns: Path to the most recent transformed file.
        :raise FileNotFoundError: If no matching transformed files are found.
        """
        prefix = f"{self.src_name}_cdm_"
        return self._get_latest_file(self._get_transformed_dir(), prefix)

    def save_harvested_data(self, harvested_data: BaseModel) -> Path:
        """Serialize and save harvested data as JSON.

        :param harvested_data: Harvested data object to serialize and save.
        :returns: Path written.
        """
        harvested_json = harvested_data.model_dump_json(exclude_none=True)
        path = self._build_harvested_path(".json")
        self._write_text(path, harvested_json)
        return path

    def save_harvested_file(self, source_file: Path, suffix: str | None = None) -> Path:
        """Copy an existing harvested artifact into managed storage.

        This is useful for harvesters that already persist data in an external
        cache or library-managed location.

        :param source_file: Existing local file to copy.
        :param suffix: Optional suffix for the destination file. If omitted,
            uses ``source_file.suffix``.
        :returns: Path written.
        :raise FileNotFoundError: If ``source_file`` does not exist.
        """
        if not source_file.is_file():
            msg = f"Harvested source file does not exist: {source_file}"
            raise FileNotFoundError(msg)

        destination = self._build_harvested_path(suffix or source_file.suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_file, destination)
        return destination

    def save_cdm(self, transformed_data: TransformedData) -> Path:
        """Serialize and save transformed data as JSON.

        :param transformed_data: Transformed data object to serialize and save.
        :returns: Path written.
        """
        cdm_json = transformed_data.model_dump_json(exclude_none=True)
        path = self._build_transformed_path(".json")
        self._write_text(path, cdm_json)
        return path
