"""A module for the Transform base class."""
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from metakb import APP_ROOT, DATE_FMT
from metakb.normalizers import VICCNormalizers

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self, data_dir: Path = APP_ROOT / "data") -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name

        self.vicc_normalizers = VICCNormalizers()

        self.statements = list()
        self.propositions = list()
        self.variation_descriptors = list()
        self.gene_descriptors = list()
        self.therapy_descriptors = list()
        self.disease_descriptors = list()
        self.methods = list()
        self.documents = list()

    def transform(self, *args, **kwargs) -> Dict[str, dict]:
        """Transform harvested data to the Common Data Model.

        :return: Updated indexes for propositions and documents
        """
        raise NotImplementedError

    def extract_harvester(
        self, harvest_path: Optional[Path] = None
    ) -> Dict[str, List]:
        """Get harvested data from file.
        :param Optional[Path] harvest_path: path to harvest JSON file. If not
        provided, will attempt to open file with current date at default
        location.
        :return: Dict containing Lists of entries for each object type
        """
        if harvest_path is None:
            today = dt.strftime(dt.today(), DATE_FMT)
            default_fname = f"{self.name}_harvester_{today}.json"
            default_path = self.data_dir / "harvester" / default_fname
            if not default_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvest file under default filename: "
                    f"{(default_path.absolute() / default_fname).as_uri()}"
                )
            harvest_path = default_path
        else:
            if not harvest_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvest file under provided filename: "
                    f"{harvest_path.absolute().as_uri()}"
                )
        with open(harvest_path, "r") as f:
            return json.load(f)

    @staticmethod
    def _set_ix(propositions_documents_ix, dict_key, search_key) -> int:
        """Set indexes for documents or propositions.

        :param dict propositions_documents_ix: Keeps track of
            proposition and documents indexes
        :param str dict_key: 'sources' or 'propositions'
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        if dict_key == 'documents':
            dict_key_ix = 'document_index'
        elif dict_key == 'propositions':
            dict_key_ix = 'proposition_index'
        else:
            raise KeyError("dict_key can only be `documents` or "
                           "`propositions`.")
        if propositions_documents_ix[dict_key].get(search_key):
            index = propositions_documents_ix[dict_key].get(search_key)
        else:
            index = propositions_documents_ix.get(dict_key_ix)
            propositions_documents_ix[dict_key][search_key] = index
            propositions_documents_ix[dict_key_ix] += 1
        return index

    def _create_json(self, filename: Optional[str] = None) -> None:
        """Create a composite JSON for transformed data.

        :param Optional[str] filename: custom filename to save as
        """
        transform_dir = self.data_dir / "transform"
        transform_dir.mkdir(exist_ok=True, parents=True)

        composite_dict = {
            'statements': self.statements,
            'propositions': self.propositions,
            'variation_descriptors': self.variation_descriptors,
            'gene_descriptors': self.gene_descriptors,
            'therapy_descriptors': self.therapy_descriptors,
            'disease_descriptors': self.disease_descriptors,
            'methods': self.methods,
            'documents': self.documents
        }

        today = dt.strftime(dt.today(), DATE_FMT)
        if filename is None:
            filename = f"{self.name}_cdm_{today}.json"
        out = transform_dir / filename
        with open(out, 'w+') as f:
            json.dump(composite_dict, f, indent=4)
