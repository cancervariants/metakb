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
        self.vicc_normalizers = self.query_handler.vicc_normalizers

        self._proposition_lookup = {}
        self._document_lookup = {}

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

    def _get_next_node_id(self, label: str) -> str:
        """Get next available ID number.
        :param str label: Node label (first letter must be capitalized)
        :return: valid CURIE with next unused ID number, e.g. `proposition:101`
        """
        label_lower = label.lower()

        if label_lower in self.next_node_id:
            next_id = self.next_node_id[label_lower]
            self.next_node_id[label_lower] += 1

        else:
            def _get_highest_id(tx: Transaction) -> Optional[str]:
                query = f"""
                MATCH (x:{label})
                WHERE x.id STARTS WITH "{label_lower}:"
                RETURN x
                ORDER BY toInteger(replace(x.id, "{label_lower}:", ""))
                DESC
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
                    next_id = 1
                    self.next_node_id[label_lower] = 2
                else:
                    next_id = int(highest_id.split(":")[-1]) + 1
                    self.next_node_id[label_lower] = next_id + 1

        return f"{label_lower}:{next_id}"

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

        args = tuple([
            a for a in [prop_type, pred, variation_id, disease_id, therapy_id]
            if a
        ])
        if args in self._proposition_lookup:
            return self._proposition_lookup[args]

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
            prop_id = response[0].get("id")
        else:
            prop_id = self._get_next_node_id("Proposition")
        self._proposition_lookup[args] = prop_id
        return prop_id

    def _get_document_id(self, **parameters) -> Optional[str]:
        """Retrieve stable ID for a document.
        :kwargs: property names and values to get ID for
        :return: identifying document ID value
        """
        # sort and get arg values for deterministic lookup
        args = tuple(dict(sorted(parameters.items())).values())
        if args in self._document_lookup:
            return self._document_lookup[args]

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
            doc_id = document_response[0].get("id")
        else:
            doc_id = self._get_next_node_id("Document")
        self._document_lookup[args] = doc_id
        return doc_id

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
