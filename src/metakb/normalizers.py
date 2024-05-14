"""Handle construction of and relay requests to VICC normalizer services."""
import logging

from disease.database import create_db as create_disease_db
from disease.query import QueryHandler as DiseaseQueryHandler
from disease.schemas import NormalizationService as NormalizedDisease
from ga4gh.core import core_models
from ga4gh.vrs import models
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
    """Manage VICC concept normalization services.

    The therapy, disease, and gene normalizer wrappers all behave roughly the same way:
    given a list of possible terms, run each of them through the normalizer, and return
    the normalized record for the one with the highest match type (tie goes to the
    earlier search term). Variations are handled differently; from the provided list of
    terms, the first one that normalizes completely is returned, so order is
    particularly important when multiple terms are given.
    """

    def __init__(self) -> None:
        """Initialize normalizers. Construct a normalizer instance for each service
        (gene, variation, disease, therapy) and retain them as instance properties.

        Note that gene concept lookups within the Variation Normalizer are resolved
        using the Gene Normalizer instance, rather than creating a second sub-instance.
        """
        self.gene_query_handler = GeneQueryHandler(create_gene_db())
        self.variation_normalizer = VariationQueryHandler(
            gene_query_handler=self.gene_query_handler
        )
        self.disease_query_handler = DiseaseQueryHandler(create_disease_db())
        self.therapy_query_handler = TherapyQueryHandler(create_therapy_db())

    async def normalize_variation(self, queries: list[str]) -> models.Variation | None:
        """Normalize variation queries.

        :param queries: Candidate query strings to attempt to normalize. Should be
            provided in order of preference, as the result of the first one to normalize
            successfully will be returned. Use in the event that a prioritized MANE
            transcript is unavailable and multiple possible candidates are known.
        :return: A normalized variation, if available.
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
        """Normalize gene queries.

        Given a collection of terms, return the normalized concept with the highest
        match (see the
        `Gene Normalizer docs <https://gene-normalizer.readthedocs.io/latest/usage.html#match-types>`_ for
        more details on match types, and how queries are resolved).

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> gene_terms = [
        ...     "gibberish",  # won't match
        ...     "NETS",  # alias
        ...     "hgnc:1097",  # HGNC identifier for BRAF
        ...     "MARCH3",  # previous symbol
        ... ]
        >>> v.normalize_gene(gene_terms)[0].normalized_id
        'hgnc:1097'

        :param queries: A list of possible gene terms to normalize. Order is irrelevant,
            except for breaking ties (choose earlier if equal).
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
        """Normalize disease queries.

        Given a collection of terms, return the normalized concept with the highest
        match.

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> disease_terms = [
        ...     "AML",  # alias
        ...     "von hippel-lindau syndrome",  # alias
        ...     "ncit:C9384",  # concept ID
        ... ]
        >>> v.normalize_disease(disease_terms)[0].normalized_id
        'ncit:C9384'

        :param queries: Disease queries to normalize. Order is irrelevant, except for
            breaking ties (choose earlier if equal).
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

        Given a collection of terms, return the normalized concept with the highest
        match.

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> therapy_terms = [
        ...     "VAZALORE",  # trade name
        ...     "RHUMAB HER2",  # alias
        ...     "rxcui:5032",  # concept ID
        ... ]
        >>> v.normalize_therapy(therapy_terms)[0].normalized_id
        'rxcui:5032'

        :param queries: Therapy queries to normalize. Order is irrelevant, except for
            breaking ties (choose earlier term if equal).
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
    ) -> core_models.Extension | None:
        """Given therapy normalization service response, extract out the regulatory
        approval extension

        :param NormalizedTherapy therapy_norm_resp: Response from normalizing therapy
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

                regulatory_approval_extension = core_models.Extension(
                    name="regulatory_approval",
                    value={
                        "approval_rating": "FDA"
                        if matched_ext_value == "FDA"
                        else "ChEMBL",
                        "has_indications": matched_indications,
                    },
                )

        return regulatory_approval_extension
