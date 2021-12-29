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

    def __init__(self, data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None) -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param Path harvester_path: Path to previously harvested data
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

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

    def extract_harvester(self) -> Dict[str, List]:
        """Get harvested data from file.

        :return: Dict containing Lists of entries for each object type
        """
        if self.harvester_path is None:
            today = dt.strftime(dt.today(), DATE_FMT)
            default_fname = f"{self.name}_harvester_{today}.json"
            default_path = self.data_dir / "harvester" / default_fname
            if not default_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvest file under default filename: "
                    f"{default_path.absolute().as_uri()}"
                )
            self.harvester_path = default_path
        else:
            if not self.harvester_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvester file: "
                    f"{self.harvester_path}"
                )
        with open(self.harvester_path, "r") as f:
            return json.load(f)

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

    @staticmethod
    def _get_document_ID(attributes: List[str]) -> str:
        """Produce hashed ID for a document.
        :param List[str] attributes: list of attribute values constituting the
        document.
        :return: identifying document ID value
        """
        attributes_lower = [attribute.lower() for attribute in attributes]
        combined = "".join(sorted(attributes_lower))
        return f"document:{sha512t24u(combined.encode())}"

    def _create_json(self, transform_dir: Optional[Path] = None,
                     filename: Optional[str] = None) -> None:
        """Create a composite JSON for transformed data.

        :param Optional[Path] transform_dir: Path to data directory for
            transformed data
        :param Optional[str] filename: Name of transformed file
        """
        if transform_dir is None:
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
