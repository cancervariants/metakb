"""A module for the Transform base class."""
from typing import Dict, Optional, List, Tuple
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from neo4j.work.transaction import Transaction

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas import PropositionType, Predicate, DiagnosticPredicate, \
    PrognosticPredicate, PredictivePredicate, FunctionalPredicate, \
    PathogenicPredicate
from metakb.normalizers import VICCNormalizers
from metakb.query import QueryHandler

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 uri: str = "",
                 credentials: Tuple[str, str] = ("", ""),
                 harvester_path: Optional[Path] = None) -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param str uri: location to send Neo4j requests to
        :param Tuple[str, str] credentials: database username and password
        :param Optional[Path] harvester_path: Path to previously harvested data
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

        self.query_handler = QueryHandler(uri, credentials)

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
                    f"Unable to open harvester file: {self.harvester_path}"
                )
        with open(self.harvester_path, "r") as f:
            return json.load(f)

    def _get_next_node_id(self, label: str) -> str:
        """Get next available ID number.
        :param str label: Node label (first letter must be capitalized)
        :return: valid CURIE with next unused ID number, e.g. `proposition:101`
        """
        label_lower = label.lower()

        def _get_highest_id(tx: Transaction) -> Optional[str]:
            query = f"""
            MATCH (x:{label})
            WHERE x.id STARTS WITH "{label_lower}:"
            RETURN x
            ORDER BY x.id DESC
            LIMIT 1
            """
            query_result = [x[0] for x in tx.run(query)]
            if len(query_result) == 0:
                return None
            else:
                return query_result[0].get("id")

        with self.query_handler.driver.session() as session:
            highest_id = session.read_transaction(_get_highest_id)
            if highest_id is None:
                return f"{label_lower}:1"
            else:
                id_number = highest_id.split(":")
                return f"{label_lower}:{int(id_number) + 1}"

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
        variation_id: str = "",
        disease_id: str = "",
        therapy_id: str = ""
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
            logger.error(f"{prop_type} in query conflicts with {pred}")
            return None
        params = {
            "prop_type": prop_type,
            "pred": pred,
            "normalized_variation": variation_id,
            "normalized_disease": disease_id,
            "normalized_therapy": therapy_id
        }
        with self.query_handler.driver.session() as session:
            response = session.read_transaction(
                self.query_handler._get_propositions,
                **params
            )
        num_matches = len(response)
        if num_matches > 1:
            logger.warning(f"Found >1 propositions matching {params}")
            return None
        elif num_matches == 1:
            return response[0].get("id")
        else:
            self._get_next_node_id("Proposition")

    def _get_document_id(self, **parameters) -> Optional[str]:
        """Retrieve stable ID for a document.
        :kwargs: property names and values to get ID for
        :return: identifying document ID value
        """
        if len(parameters) == 0:
            return self._get_next_node_id("Document")
        with self.query_handler.driver.session() as session:
            document_response = session.read_transaction(
                self.query_handler._get_documents,
                **parameters
            )
        num_matches = len(document_response)
        if num_matches > 1:
            logger.warning(f"Found >1 propositions matching {parameters}")
            return None
        elif num_matches == 1:
            return document_response[0].get("id")
        else:
            return self._get_next_node_id("Document")

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
