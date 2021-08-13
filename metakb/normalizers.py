"""Module for VICC normalizers."""
from typing import Optional, Tuple
from ga4gh.vrs.dataproxy import SeqRepoDataProxy
from variation.classifiers.classify import Classify
from variation.data_sources.mane_transcript_mappings import \
    MANETranscriptMappings
from variation.data_sources.seq_repo_access import SeqRepoAccess
from variation.data_sources.transcript_mappings import TranscriptMappings
from variation.data_sources.uta import UTA
from variation.mane_transcript import MANETranscript
from variation.to_vrs import ToVRS
from variation.tokenizers.caches.amino_acid_cache import AminoAcidCache
from variation.tokenizers.caches.gene_symbol_cache import GeneSymbolCache
from variation.tokenizers.gene_symbol import GeneSymbol
from variation.tokenizers.tokenize import Tokenize
from ga4gh.vrs.extras.translator import Translator
from variation.translators.translate import Translate
from variation.validators.validate import Validate
from variation.normalize import Normalize as VariationNormalizer
from therapy.query import QueryHandler as TherapyQueryHandler
from disease.query import QueryHandler as DiseaseQueryHandler
from gene.query import QueryHandler as GeneQueryHandler
import logging

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class VICCNormalizers:
    """A class for normalizing terms using VICC normalizers."""

    def __init__(self):
        """Initialize the VICC Normalizers."""
        self.gene_query_handler = GeneQueryHandler()
        self.seqrepo_access = SeqRepoAccess()
        self.uta = UTA()
        self.variation_normalizer = VariationNormalizer(
            self.seqrepo_access, self.uta
        )
        self.disease_query_handler = DiseaseQueryHandler()
        self.therapy_query_handler = TherapyQueryHandler()
        self.variation_to_vrs = self._initialize_variation()
        self.amino_acid_cache = AminoAcidCache()

    def _initialize_variation(self) -> ToVRS:
        """Initialize variation toVRS.

        :return: toVRS instance
        """
        tokenizer = Tokenize()
        classifier = Classify()
        transcript_mappings = TranscriptMappings()
        gene_symbol = GeneSymbol(GeneSymbolCache())
        amino_acid_cache = AminoAcidCache()
        mane_transcript_mappings = MANETranscriptMappings()
        dp = SeqRepoDataProxy(self.seqrepo_access.seq_repo_client)
        tlr = Translator(data_proxy=dp)
        mane_transcript = MANETranscript(
            self.seqrepo_access, transcript_mappings, mane_transcript_mappings,
            self.uta
        )
        validator = Validate(
            self.seqrepo_access, transcript_mappings, gene_symbol,
            mane_transcript, self.uta, dp, tlr, amino_acid_cache
        )
        translator = Translate()

        return ToVRS(
            tokenizer, classifier, self.seqrepo_access, transcript_mappings,
            gene_symbol, amino_acid_cache, self.uta, mane_transcript_mappings,
            mane_transcript, validator, translator
        )

    def normalize_variant(self, queries, normalizer_responses=None)\
            -> Optional[dict]:
        """Normalize variation queries.

        :param list queries: Possible query strings to try to normalize
        :param list normalizer_responses: A list to store normalizer_responses
            which are used in the event that a MANE transcript cannot be found
        :return: A normalized variation
        """
        variation_norm_resp = None
        for query in queries:
            if not query:
                continue

            try:
                validations, warnings = \
                    self.variation_to_vrs.get_validations(
                        query, normalize_endpoint=True
                    )
                variation_norm_resp = self.variation_normalizer.normalize(
                    query, validations, warnings
                )

                if variation_norm_resp:
                    del variation_norm_resp.value.id
                    if normalizer_responses:
                        normalizer_responses.append(variation_norm_resp)
                    if not self.variation_normalizer.warnings:
                        break
            except:  # noqa: E722
                logger.warning("Variation Normalizer does not support: "
                               f"{query}")
        return variation_norm_resp

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
            if gene_norm_resp['match_type'] > highest_match:
                highest_match = gene_norm_resp['match_type']
                normalized_gene_id = \
                    gene_norm_resp['gene_descriptor']['value']['id']
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
                    disease_norm_resp['value_object_descriptor']['value']['id']
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
                normalized_therapy_id = therapy_norm_resp['value_object_descriptor']['value']['id']  # noqa: E501
                if highest_match == 100:
                    break
        return therapy_norm_resp, normalized_therapy_id
