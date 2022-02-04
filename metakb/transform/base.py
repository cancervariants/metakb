"""A module for the Transform base class."""
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from ga4gh.core import sha512t24u

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas import PropositionType, Predicate, DiagnosticPredicate, \
    PrognosticPredicate, PredictivePredicate, FunctionalPredicate, \
    PathogenicPredicate
from metakb.normalizers import VICCNormalizers

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[VICCNormalizers] = None) -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param VICCNormalizers normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

        if normalizers is None:
            self.vicc_normalizers = VICCNormalizers()
        else:
            self.vicc_normalizers = normalizers

        self.statements = list()
        self.propositions = list()
        self.variation_descriptors = list()
        self.gene_descriptors = list()
        self.therapy_descriptors = list()
        self.disease_descriptors = list()
        self.methods = list()
        self.documents = list()

        self.next_node_id = {}

    def transform(self, *args, **kwargs):
        """Transform harvested data to the Common Data Model."""
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
                    f"Unable to open harvester file: {self.harvester_path}"
                )
        with open(self.harvester_path, "r") as f:
            return json.load(f)

    predicate_validation = {
        PropositionType.PREDICTIVE: PredictivePredicate,
        PropositionType.DIAGNOSTIC: DiagnosticPredicate,
        PropositionType.PROGNOSTIC: PrognosticPredicate,
        PropositionType.PATHOGENIC: PathogenicPredicate,
        PropositionType.FUNCTIONAL: FunctionalPredicate
    }

    def _get_proposition_id(
        self,
        prop_type: PropositionType,
        pred: Predicate,
        variation_ids: List[str] = [],
        disease_ids: List[str] = [],
        therapy_ids: List[str] = []
    ) -> Optional[str]:
        """Retrieve stable ID for a proposition

        :param PropositionType prop_type: type of Proposition
        :param Predicate pred: proposition predicate value
        :param str variation_id: VRS ID
        :param str disease_id: normalized disease ID
        :param str therapy_id: normalized therapy ID
        :return: proposition ID, or None if prop_type and pred conflict or
            if provided parameters cannot determine correct proposition ID
        """
        if not isinstance(pred, self.predicate_validation[prop_type]):
            msg = f"{prop_type} in query conflicts with {pred}"
            logger.error(msg)
            raise ValueError(msg)

        concept_ids = variation_ids + disease_ids + therapy_ids
        terms = [prop_type.value, pred.value] + concept_ids
        terms_sorted = sorted([t.lower() for t in terms])
        blob = json.dumps(terms_sorted).encode("ascii")
        digest = sha512t24u(blob=blob)
        return f"proposition:{digest}"

    @staticmethod
    def _get_document_id(**parameters) -> str:
        """Retrieve stable ID for a document.
        :parameters: property names and values to get ID for. Assumes values
            are strings.
        :return: identifying document ID value
        """
        params_sorted = {
            key.lower(): parameters[key].lower() for key in sorted(parameters)
        }
        blob = json.dumps(params_sorted).encode("ascii")
        return f"document:{sha512t24u(blob=blob)}"

    def create_json(self, transform_dir: Optional[Path] = None,
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
