"""Module for VICC normalizers."""
from typing import Optional, Tuple
from variation.query import QueryHandler as VariationQueryHandler
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler
from gene.query import QueryHandler as GeneQueryHandler
import logging

logger = logging.getLogger('metakb.normalizers')
logger.setLevel(logging.DEBUG)


class VICCNormalizers:
    """A class for normalizing terms using VICC normalizers."""

    def __init__(self):
        """Initialize the VICC Normalizers."""
        self.gene_query_handler = GeneQueryHandler()
        self.variation_normalizer = VariationQueryHandler()
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()

    def normalize_variation(self, queries, normalizer_responses=None)\
            -> Optional[dict]:
        """Normalize variation queries.

        :param list queries: Possible query strings to try to normalize
        :param list normalizer_responses: A list to store normalizer_responses
            which are used in the event that a MANE transcript cannot be found
        :return: A normalized variation
        """
        for query in queries:
            if not query:
                continue

            try:
                variation_norm_resp = \
                    self.variation_normalizer.normalize(query)
                if variation_norm_resp:
                    if normalizer_responses and \
                            variation_norm_resp.value.type != 'Text':
                        normalizer_responses.append(variation_norm_resp)
                    if not self.variation_normalizer.normalize_handler.warnings:  # noqa: E501
                        return variation_norm_resp.dict(exclude_none=True)
            except Exception as e:  # noqa: E722
                logger.warning(f"Variation Normalizer could not "
                               f"normalize {query}: {e}")
        return None

    def normalize_gene(self, queries) -> Tuple[Optional[dict], Optional[str]]:
        """Normalize gene queries

        :param list queries: Gene queries to normalize
        :return: The highest matched gene's normalized response and ID
        """
        gene_norm_resp = None
        normalized_gene_id = None
        highest_match = 0
        for query_str in queries:
            if not query_str:
                continue

            gene_norm_resp = self.gene_query_handler.normalize(query_str)
            if gene_norm_resp.match_type > highest_match:
                highest_match = gene_norm_resp.match_type
                normalized_gene_id = \
                    gene_norm_resp.gene_descriptor.gene_id
                if highest_match == 100:
                    break
        return gene_norm_resp, normalized_gene_id

    def normalize_disease(self, queries)\
            -> Tuple[Optional[dict], Optional[str]]:
        """Normalize disease queries

        :param list queries: Disease queries to normalize
        :return: The highest matched disease's normalized response and ID
        """
        highest_match = 0
        normalized_disease_id = None
        disease_norm_resp = None

        for query in queries:
            if not query:
                continue

            disease_norm_resp = self.disease_query_handler.search_groups(query)
            if disease_norm_resp['match_type'] > highest_match:
                highest_match = disease_norm_resp['match_type']
                normalized_disease_id = \
                    disease_norm_resp['disease_descriptor']['disease_id']
                if highest_match == 100:
                    break
        return disease_norm_resp, normalized_disease_id

    def normalize_therapy(self, queries)\
            -> Tuple[Optional[dict], Optional[str]]:
        """Normalize therapy queries

        :param list queries: Therapy queries to normalize
        :return: The highest matched therapy's normalized response and ID
        """
        highest_match = 0
        normalized_therapy_id = None
        therapy_norm_resp = None

        for query in queries:
            if not query:
                continue

            therapy_norm_resp = self.therapy_query_handler.search_groups(query)
            if therapy_norm_resp['match_type'] > highest_match:
                highest_match = therapy_norm_resp['match_type']
                normalized_therapy_id = therapy_norm_resp['therapy_descriptor']['therapy_id']  # noqa: E501
                if highest_match == 100:
                    break
        return therapy_norm_resp, normalized_therapy_id
