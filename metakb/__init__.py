"""The MetaKB package."""
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logging.basicConfig(
    filename='metakb.log',
    format='[%(asctime)s] %(levelname)s : %(message)s')
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class FileDownloadException(Exception):
    """Exception class for handling failed downloads of source files."""

    def __init__(self, *args, **kwargs):
        """Initialize exception."""
        super().__init__(*args, **kwargs)
