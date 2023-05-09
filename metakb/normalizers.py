"""Module for VICC normalizers."""
import logging
from typing import List, Optional, Tuple

from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, Extension
from variation.query import QueryHandler as VariationQueryHandler
from therapy.query import QueryHandler as TherapyQueryHandler
from therapy.schemas import NormalizationService as NormalizedTherapy, ApprovalRating
from disease.query import QueryHandler as DiseaseQueryHandler
from disease.schemas import NormalizationService as NormalizedDisease
from gene.database.dynamodb import DynamoDbDatabase
from gene.query import QueryHandler as GeneQueryHandler
from gene.schemas import NormalizeService as NormalizedGene


logger = logging.getLogger(__name__)


class VICCNormalizers:
    """A class for normalizing terms using VICC normalizers."""

    def __init__(
        self, gene_query_handler: Optional[GeneQueryHandler] = None,
        variation_query_handler: Optional[VariationQueryHandler] = None,
        disease_query_handler: Optional[DiseaseQueryHandler] = None,
        therapy_query_handler: Optional[TherapyQueryHandler] = None
    ) -> None:
        """Initialize the VICC Normalizers.

        :param gene_query_handler: Gene QueryHandler instance
        :param variation_query_handler: Variation QueryHandler instance
        :param disease_query_handler: Disease QueryHandler instance
        :param therapy_query_handler: Therapy QueryHandler instance
        """
        self.disease_query_handler = disease_query_handler or DiseaseQueryHandler()
        self.therapy_query_handler = therapy_query_handler or TherapyQueryHandler()
        self.gene_query_handler = (gene_query_handler or GeneQueryHandler(DynamoDbDatabase()))  # noqa: E501

        if variation_query_handler:
            self.variation_query_handler = variation_query_handler
        else:
            self.variation_query_handler = VariationQueryHandler(
                gene_query_handler=self.gene_query_handler
            )

    async def normalize_variation(
        self, queries: List[str]
    ) -> Optional[VariationDescriptor]:
        """Normalize variation queries.

        :param queries: Possible query strings to try to normalize
            which are used in the event that a MANE transcript cannot be found
        :return: A normalized variation
        """
        for query in queries:
            if not query:
                continue
            try:
                variation_norm_resp = await self.variation_query_handler.normalize_handler.normalize(query)  # noqa: E501
                if variation_norm_resp and variation_norm_resp.variation_descriptor:
                    return variation_norm_resp.variation_descriptor
            except Exception as e:  # noqa: E722
                logger.warning(f"Variation Normalizer raised an exception using query"
                               f" {query}: {e}")
        return None

    def normalize_gene(
        self, queries: List[str]
    ) -> Tuple[Optional[NormalizedGene], Optional[str]]:
        """Normalize gene queries

        :param queries: Gene queries to normalize
        :return: The highest matched gene's normalized response and ID, if successful
        """
        gene_norm_resp = None
        normalized_gene_id = None
        highest_match = 0
        for query_str in queries:
            if not query_str:
                continue

            try:
                gene_norm_resp = self.gene_query_handler.normalize(query_str)
            except Exception as e:
                logger.warning(f"Gene Normalizer raised an exception using query "
                               f"{query_str}: {e}")
            else:
                if gene_norm_resp.match_type > highest_match:
                    highest_match = gene_norm_resp.match_type
                    normalized_gene_id = \
                        gene_norm_resp.gene_descriptor.gene_id
                    if highest_match == 100:
                        break
        return gene_norm_resp, normalized_gene_id

    def normalize_disease(
        self, queries: List[str]
    ) -> Tuple[Optional[NormalizedDisease], Optional[str]]:
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

            try:
                disease_norm_resp = self.disease_query_handler.normalize(query)
            except Exception as e:
                logger.warning(f"Disease Normalizer raised an exception using query "
                               f"{query}: {e}")
            else:
                if disease_norm_resp.match_type > highest_match:
                    highest_match = disease_norm_resp.match_type
                    normalized_disease_id = \
                        disease_norm_resp.disease_descriptor.disease_id
                    if highest_match == 100:
                        break
        return disease_norm_resp, normalized_disease_id

    def normalize_therapy(
        self, queries: List[str]
    ) -> Tuple[Optional[NormalizedTherapy], Optional[str]]:
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

            try:
                therapy_norm_resp = self.therapy_query_handler.normalize(query)
            except Exception as e:
                logger.warning(f"Therapy Normalizer raised an exception using "
                               f"query {query}: {e}")
            else:
                if therapy_norm_resp.match_type > highest_match:
                    highest_match = therapy_norm_resp.match_type
                    normalized_therapy_id = therapy_norm_resp.therapy_descriptor.therapy_id  # noqa: E501
                    if highest_match == 100:
                        break
        return therapy_norm_resp, normalized_therapy_id

    @staticmethod
    def get_regulatory_approval_extension(
        therapy_norm_resp: NormalizedTherapy
    ) -> Optional[Extension]:
        """Given therapy normalization service response, extract out the regulatory
        approval extension

        :param NormalizedTherapy therapy_norm_resp: Response from normalizing therapy
        :return: Extension containing transformed regulatory approval and indication
            data if it `regulatory_approval` extensions exists in therapy normalizer
        """
        regulatory_approval_extension = None
        tn_resp_exts = therapy_norm_resp.dict().get("therapy_descriptor", {}).get("extensions") or []  # noqa: E501
        tn_ext = [v for v in tn_resp_exts if v["name"] == "regulatory_approval"]

        if tn_ext:
            ext_value = tn_ext[0]["value"]
            approval_ratings = ext_value.get("approval_ratings", [])
            matched_ext_value = None

            if any(ar in {ApprovalRating.FDA_PRESCRIPTION, ApprovalRating.FDA_OTC}
                    for ar in approval_ratings):
                if ApprovalRating.FDA_DISCONTINUED not in approval_ratings or \
                    ApprovalRating.CHEMBL_4 in approval_ratings:  # noqa: E125
                    matched_ext_value = "FDA"
            elif ApprovalRating.CHEMBL_4 in approval_ratings:
                matched_ext_value = "chembl_phase_4"

            if matched_ext_value:
                has_indications = ext_value.get("has_indication", [])
                matched_indications = list()

                for indication in has_indications:
                    indication_exts = indication.get("extensions", [])
                    for indication_ext in indication_exts:
                        if indication_ext["value"] == matched_ext_value:
                            matched_indications.append({
                                "id": indication["id"],
                                "type": indication["type"],
                                "label": indication["label"],
                                "disease_id": indication["disease_id"]
                            })

                regulatory_approval_extension = Extension(
                    name="regulatory_approval",
                    value={
                        "approval_rating": "FDA" if matched_ext_value == "FDA" else "ChEMBL",  # noqa: E501
                        "has_indications": matched_indications
                    })

        return regulatory_approval_extension
