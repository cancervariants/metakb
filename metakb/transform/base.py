"""A module for the Transform base class."""
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from ga4gh.core import sha512t24u

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas import PropositionType, Predicate
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
                    f"{default_path.absolute().as_uri()}"
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
    def _set_ix(documents_ix, search_key) -> int:
        """Set indexes for documents.

        :param dict documents_ix: Keeps track of documents indexes
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        # dict_key_ix = 'document_index'
        if documents_ix["documents"].get(search_key):
            index = documents_ix["documents"].get(search_key)
        else:
            index = documents_ix.get("document_index")
            documents_ix["documents"][search_key] = index
            documents_ix["document_index"] += 1
        return index

    @staticmethod
    def _get_proposition_ID(prop_type: PropositionType, pred: Predicate,
                            concept_ids: List[str]) -> str:
        """Produce hashed ID for a proposition.

        :param PropositionType prop_type: type of Proposition
        :param Predicate pred: proposition predicate value
        :param List[str] concept_ids: all concept IDs relevant to the
        proposition (therapies, variations, diseases). Order irrelevant.
        :return: proposition ID including the SHA-512 hash of the provided IDs
        """
        terms = [prop_type.value, pred.value] + concept_ids
        terms_lower = [t.lower() for t in terms]
        combined = "".join(sorted(terms_lower))
        return f"proposition:{sha512t24u(combined.encode())}"

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
