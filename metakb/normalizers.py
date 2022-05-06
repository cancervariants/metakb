"""Module for VICC normalizers."""
from typing import Optional, Tuple

from ga4gh.vrsatile.pydantic.vrs_models import VRSTypes
from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, Extension
from variation.query import QueryHandler as VariationQueryHandler
from therapy.query import QueryHandler as TherapyQueryHandler
from therapy.schemas import NormalizationService as NormalizedTherapy, ApprovalRating
from disease.query import QueryHandler as DiseaseQueryHandler
from disease.schemas import NormalizationService as NormalizedDisease
from gene.query import QueryHandler as GeneQueryHandler
from gene.schemas import NormalizeService as NormalizedGene
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

    async def normalize_variation(self,
                                  queries) -> Optional[VariationDescriptor]:
        """Normalize variation queries.

        :param list queries: Possible query strings to try to normalize
            which are used in the event that a MANE transcript cannot be found
        :return: A normalized variation
        """
        for query in queries:
            if not query:
                continue

            try:
                variation_norm_resp = \
                    await self.variation_normalizer.normalize(query)
                if variation_norm_resp:
                    if variation_norm_resp.variation.type != VRSTypes.TEXT:
                        return variation_norm_resp
            except Exception as e:  # noqa: E722
                logger.warning(f"Variation Normalizer raised an exception "
                               f"using query {query}: {e}")
        return None

    def normalize_gene(self, queries)\
            -> Tuple[Optional[NormalizedGene], Optional[str]]:
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

            try:
                gene_norm_resp = self.gene_query_handler.normalize(query_str)
            except Exception as e:
                logger.warning(f"Gene Normalizer raised an exception using "
                               f"query {query_str}: {e}")
            else:
                if gene_norm_resp.match_type > highest_match:
                    highest_match = gene_norm_resp.match_type
                    normalized_gene_id = \
                        gene_norm_resp.gene_descriptor.gene_id
                    if highest_match == 100:
                        break
        return gene_norm_resp, normalized_gene_id

    def normalize_disease(self, queries)\
            -> Tuple[Optional[NormalizedDisease], Optional[str]]:
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
                logger.warning(f"Disease Normalizer raised an exception using "
                               f"query {query}: {e}")
            else:
                if disease_norm_resp.match_type > highest_match:
                    highest_match = disease_norm_resp.match_type
                    normalized_disease_id = \
                        disease_norm_resp.disease_descriptor.disease_id
                    if highest_match == 100:
                        break
        return disease_norm_resp, normalized_disease_id

    def normalize_therapy(self, queries)\
            -> Tuple[Optional[NormalizedTherapy], Optional[str]]:
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
