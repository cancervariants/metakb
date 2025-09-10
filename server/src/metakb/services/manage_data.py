"""Load and manage data for the database."""

import json
import logging
from pathlib import Path

from metakb.repository.base import AbstractRepository
from metakb.transformers.base import TransformedData

_logger = logging.getLogger(__name__)


def load_from_json(src_transformed_cdm: Path, repository: AbstractRepository) -> None:
    """Load evidence into DB from given CDM JSON file.

    :param src_transformed_cdm: path to file for a source's transformed data to
        common data model containing statements, variation, therapies, conditions,
        genes, methods, documents, etc.
    :param driver: Neo4j graph driver, if available
    """
    _logger.info("Loading data from %s", src_transformed_cdm)
    with src_transformed_cdm.open() as f:
        items = json.load(f)
        data = TransformedData(**items)
        repository.add_transformed_data(data)
