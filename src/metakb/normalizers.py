"""Module for VICC normalizers."""
import logging
from typing import List, Optional, Tuple
from typing import List, Optional, Tuple, Union

from disease.database import create_db as create_disease_db
from disease.query import QueryHandler as DiseaseQueryHandler
from disease.schemas import NormalizationService as NormalizedDisease
from ga4gh.core import core_models
from ga4gh.vrs._internal.models import Variation
from ga4gh.core import core_models
from ga4gh.vrs import models
from ga4gh.core._internal.models import Extension
from ga4gh.vrs._internal.models import Allele, CopyNumberChange, CopyNumberCount
from gene.database import create_db as create_gene_db
from gene.query import QueryHandler as GeneQueryHandler
from gene.schemas import NormalizeService as NormalizedGene
from therapy.database import create_db as create_therapy_db
from therapy.query import QueryHandler as TherapyQueryHandler
from therapy.schemas import ApprovalRating
from therapy.schemas import NormalizationService as NormalizedTherapy
from variation.query import QueryHandler as VariationQueryHandler

logger = logging.getLogger(__name__)


class ViccNormalizers:
    """A class for normalizing terms using VICC normalizers."""

    def __init__(self) -> None:
        """Initialize the VICC normalizers query handler instances."""
        self.gene_query_handler = GeneQueryHandler(create_gene_db())
        self.variation_normalizer = VariationQueryHandler(
            gene_query_handler=self.gene_query_handler
        )
        self.disease_query_handler = DiseaseQueryHandler(create_disease_db())
        self.therapy_query_handler = TherapyQueryHandler(create_therapy_db())

    async def normalize_variation(self, queries: list[str]) -> Allele | CopyNumberChange | CopyNumberCount | None:
        """Normalize variation queries.

        :param queries: Possible query strings to try to normalize which are used in
            the event that a MANE transcript cannot be found
        :return: A normalized variation
        """
        for query in queries:
            if not query:
                continue
            try:
                variation_norm_resp = (
                    await self.variation_normalizer.normalize_handler.normalize(query)
                )
                if variation_norm_resp and variation_norm_resp.variation:
                    return variation_norm_resp.variation
            except Exception as e:
                logger.warning(
                    "Variation Normalizer raised an exception using query %s: %s",
                    query,
                    e,
                )
        return None

    def normalize_gene(
        self, queries: list[str]
    ) -> tuple[NormalizedGene | None, str | None]:
        """Normalize gene queries

        :param queries: Gene queries to normalize
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
                logger.warning(
                    "Gene Normalizer raised an exception using query %s: %s",
                    query_str,
                    e,
                )
            else:
                if gene_norm_resp.match_type > highest_match:
                    highest_match = gene_norm_resp.match_type
                    normalized_gene_id = gene_norm_resp.normalized_id
                    if highest_match == 100:
                        break
        return gene_norm_resp, normalized_gene_id

    def normalize_disease(
        self, queries: list[str]
    ) -> tuple[NormalizedDisease | None, str | None]:
        """Normalize disease queries

        :param queries: Disease queries to normalize
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
                logger.warning(
                    "Disease Normalizer raised an exception using query %s: %s",
                    query,
                    e,
                )
            else:
                if disease_norm_resp.match_type > highest_match:
                    highest_match = disease_norm_resp.match_type
                    normalized_disease_id = disease_norm_resp.normalized_id
                    if highest_match == 100:
                        break
        return disease_norm_resp, normalized_disease_id

    def normalize_therapy(
        self, queries: list[str]
    ) -> tuple[NormalizedTherapy | None, str | None]:
        """Normalize therapy queries

        :param queries: Therapy queries to normalize
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
                logger.warning(
                    "Therapy Normalizer raised an exception using query %s: %s",
                    query,
                    e,
                )
            else:
                if therapy_norm_resp.match_type > highest_match:
                    highest_match = therapy_norm_resp.match_type
                    normalized_therapy_id = therapy_norm_resp.normalized_id
                    if highest_match == 100:
                        break
        return therapy_norm_resp, normalized_therapy_id

    @staticmethod
    def get_regulatory_approval_extension(
        therapy_norm_resp: NormalizedTherapy,
    ) -> Extension | None:
        """Given therapy normalization service response, extract out the regulatory
        approval extension

        :param therapy_norm_resp: Response from normalizing therapy
        :return: Extension containing transformed regulatory approval and indication
            data if it `regulatory_approval` extensions exists in therapy normalizer
        """
        regulatory_approval_extension = None
        tn_resp_exts = (
            therapy_norm_resp.model_dump()
            .get("therapeutic_agent", {})
            .get("extensions")
            or []
        )
        tn_ext = [v for v in tn_resp_exts if v["name"] == "regulatory_approval"]

        if tn_ext:
            ext_value = tn_ext[0]["value"]
            approval_ratings = ext_value.get("approval_ratings", [])
            matched_ext_value = None

            if any(
                ar in {ApprovalRating.FDA_PRESCRIPTION, ApprovalRating.FDA_OTC}
                for ar in approval_ratings
            ):
                if (
                    ApprovalRating.FDA_DISCONTINUED not in approval_ratings
                    or ApprovalRating.CHEMBL_4 in approval_ratings
                ):
                    matched_ext_value = "FDA"
            elif ApprovalRating.CHEMBL_4 in approval_ratings:
                matched_ext_value = "chembl_phase_4"

            if matched_ext_value:
                has_indications = ext_value.get("has_indication", [])
                matched_indications = []

                for indication in has_indications:
                    indication_exts = indication.get("extensions", [])
                    for indication_ext in indication_exts:
                        if indication_ext["value"] == matched_ext_value:
                            matched_ind = {
                                "id": indication["id"],
                                "type": indication["type"],
                                "label": indication["label"],
                            }

                            if indication.get("mappings"):
                                matched_ind["mappings"] = indication["mappings"]

                            matched_indications.append(matched_ind)

                regulatory_approval_extension = Extension(
                    name="regulatory_approval",
                    value={
                        "approval_rating": "FDA"
                        if matched_ext_value == "FDA"
                        else "ChEMBL",
                        "has_indications": matched_indications,
                    },
                )

        return regulatory_approval_extension
