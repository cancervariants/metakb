"""A module for the Transform base class."""
from typing import Dict
from metakb.normalizers import VICCNormalizers
import json
import logging

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    def __init__(self, file_path):
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
