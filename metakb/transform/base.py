"""A module for the Transform base class."""
from typing import Dict, List
import json
import logging

from ga4gh.core import sha512t24u

from metakb.schemas import PropositionType, Predicate
from metakb.normalizers import VICCNormalizers

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self, file_path: str):
        """Initialize Transform base class.

        :param str file_path: Path to harvested json to transform
        """
        self.file_path = file_path
        self.vicc_normalizers = VICCNormalizers()

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
