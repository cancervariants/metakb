"""The MetaKB package."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[0]

# default date format for all saved data files
DATE_FMT = "%Y%m%d"


try:
    __version__ = version("metakb")
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
