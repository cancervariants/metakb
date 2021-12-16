"""A module for the Transform base class."""
from typing import Dict, Tuple, Optional
import json
import logging

from metakb.schemas import PropositionType, Predicate, PredictivePredicate, \
    DiagnosticPredicate, PrognosticPredicate, PathogenicPredicate, \
    FunctionalPredicate
from metakb.normalizers import VICCNormalizers
from metakb.query import QueryHandler

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self, file_path: str, uri: str = "",
                 credentials: Tuple[str, str] = ("", "")):
        """Initialize Transform base class.

        :param str file_path: Path to harvested json to transform
        """
        self.file_path = file_path
        self.vicc_normalizers = VICCNormalizers()
        self.query_handler = QueryHandler(uri, credentials)

    def transform(self, *args, **kwargs) -> Dict[str, dict]:
        """Transform harvested data to the Common Data Model.

        :return: Updated indexes for propositions and documents
        """
        raise NotImplementedError

    def extract_harvester(self) -> Dict[str, list]:
        """Extract source data"""
        with open(self.file_path, 'r') as f:
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

    def get_proposition_id(
            self,
            prop_type: PropositionType,
            pred: Predicate,
            variation_id: str = "",
            disease_id: str = "",
            therapy_id: str = "") -> Optional[str]:
        """Retrieve ID for proposition if it exists, in order to avoid creating
        duplicate proposition entries. Should be passed as callback to Neo4j
        read_transcation API.
        :param PropositionType prop_type: type of proposition
        :param Predicate pred: value of predicate
        :param str variation_id: VRS ID
        :param str disease_id: normalized disease ID
        :param str therapy_id: normalized therapy ID
        :return: complete proposition ID (eg `'proposition:182'`) or None
        """
        if (prop_type == PropositionType.PREDICTIVE
                and not isinstance(pred, PredictivePredicate)) \
            or (prop_type == PropositionType.DIAGNOSTIC
                and not isinstance(pred, DiagnosticPredicate)) \
            or (prop_type == PropositionType.PROGNOSTIC
                and not isinstance(pred, PrognosticPredicate)) \
            or (prop_type == PropositionType.PATHOGENIC
                and not isinstance(pred, PathogenicPredicate)) \
            or (prop_type == PropositionType.FUNCTIONAL
                and not isinstance(pred, FunctionalPredicate)):
            logger.error(
                f"{prop_type} in query conflicts with {pred}"
            )
            return None
        with self.query_handler.driver.session() as session:
            params = {
                "prop_type": prop_type,
                "pred": pred,
                "normalized_variation": variation_id,
                "normalized_disease": disease_id,
                "normalized_therapy": therapy_id
            }
            response = session.read_transaction(
                self.query_handler._get_propositions,
                **params
            )
            if len(response) < 1:
                return None
            elif len(response) > 1:
                logger.warning(f"Found >1 propositions matching {params}")
                return None
            else:
                return response[0].get("id")
