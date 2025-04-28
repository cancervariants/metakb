"""Handle construction of and relay requests to VICC normalizer services."""

import logging
import os
from collections.abc import Iterable
from enum import Enum

from botocore.exceptions import TokenRetrievalError
from disease.cli import update as update_disease_db
from disease.database import create_db as create_disease_db
from disease.database.database import AWS_ENV_VAR_NAME as DISEASE_AWS_ENV_VAR_NAME
from disease.query import QueryHandler as DiseaseQueryHandler
from disease.schemas import NormalizationService as NormalizedDisease
from ga4gh.core.models import Extension
from ga4gh.vrs.models import (
    Allele,
    CopyNumberChange,
    CopyNumberCount,
)
from gene.cli import update as update_gene_db
from gene.database import create_db as create_gene_db
from gene.database.database import AWS_ENV_VAR_NAME as GENE_AWS_ENV_VAR_NAME
from gene.query import QueryHandler as GeneQueryHandler
from gene.schemas import NormalizeService as NormalizedGene
from therapy.cli import update_normalizer_db as update_therapy_db
from therapy.database import create_db as create_therapy_db
from therapy.database.database import AWS_ENV_VAR_NAME as THERAPY_AWS_ENV_VAR_NAME
from therapy.query import QueryHandler as TherapyQueryHandler
from therapy.schemas import ApprovalRating
from therapy.schemas import NormalizationService as NormalizedTherapy
from variation.query import QueryHandler as VariationQueryHandler

__all__ = [
    "NORMALIZER_AWS_ENV_VARS",
    "IllegalUpdateError",
    "NormalizerName",
    "ViccNormalizers",
    "check_normalizers",
    "update_normalizer",
]

_logger = logging.getLogger(__name__)


class ViccNormalizers:
    """Manage VICC concept normalization services.

    The therapy, disease, and gene normalizer wrappers all behave roughly the same way:
    given a list of possible terms, run each of them through the normalizer, and return
    the normalized record for the one with the highest match type (tie goes to the
    earlier search term). Variations are handled differently; from the provided list of
    terms, the first one that normalizes completely is returned, so order is
    particularly important when multiple terms are given.

    See :ref:`concept normalization services<normalization>` in the documentation for
    more.
    """

    def __init__(self, db_url: str | None = None) -> None:
        """Initialize normalizers. Construct a normalizer instance for each service
        (gene, variation, disease, therapy) and retain them as instance properties.

        >>> from metakb.normalizers import ViccNormalizers
        >>> norm = ViccNormalizers()

        Note that gene concept lookups within the Variation Normalizer are resolved
        using the Gene Normalizer instance, rather than creating a second sub-instance.

        >>> id(norm.gene_query_handler) == id(
        ...     norm.variation_normalizer.gnomad_vcf_to_protein_handler.gene_normalizer
        ... )
        True

        :param db_url: optional definition of shared normalizer database. Because the
            same parameter is passed to each concept normalizer, this only works for
            connecting a DynamoDB backend. If not given, each normalizer falls back
            on default behavior for connecting to a database, which includes checking
            their corresponding environment variables.
        """
        self.gene_query_handler = GeneQueryHandler(create_gene_db(db_url))
        self.variation_normalizer = VariationQueryHandler(
            gene_query_handler=self.gene_query_handler
        )
        self.disease_query_handler = DiseaseQueryHandler(create_disease_db(db_url))
        self.therapy_query_handler = TherapyQueryHandler(create_therapy_db(db_url))

    async def normalize_variation(
        self, query: str
    ) -> Allele | CopyNumberChange | CopyNumberCount | None:
        """Attempt to normalize a variation query

        :param query: Variation query to normalize
        :raises TokenRetrievalError: If AWS credentials are expired
        :return: A normalized variation, if available.
        """
        try:
            variation_norm_resp = (
                await self.variation_normalizer.normalize_handler.normalize(query)
            )
            if variation_norm_resp and variation_norm_resp.variation:
                return variation_norm_resp.variation
        except TokenRetrievalError:
            raise
        except Exception:
            _logger.exception(
                "Variation Normalizer raised an exception using query %s",
                query,
            )
        return None

    def normalize_gene(self, query: str) -> tuple[NormalizedGene, str | None]:
        """Attempt to normalize a gene query

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> v.normalize_gene("BRAF")[1]
        'hgnc:1097'

        :param query: Gene query to normalize
        :raises TokenRetrievalError: If AWS credentials are expired
        :return: Gene normalization response and normalized gene ID, if available.
        """
        return self._normalize_concept(query, self.gene_query_handler, "gene")

    def normalize_disease(self, query: str) -> tuple[NormalizedDisease, str | None]:
        """Attempt to normalize a disease query

        Given a collection of terms, return the normalized concept with the highest
        match.

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> v.normalize_disease("von hippel-lindau syndrome")[1]
        'ncit:C3105'

        :param query: Disease query normalize
        :raises TokenRetrievalError: If AWS credentials are expired
        :return: Disease normalization response and normalized disease ID, if available.
        """
        return self._normalize_concept(query, self.disease_query_handler, "disease")

    def normalize_therapy(self, query: str) -> tuple[NormalizedTherapy, str | None]:
        """Attempt to normalize a therapy query

        >>> from metakb.normalizers import ViccNormalizers
        >>> v = ViccNormalizers()
        >>> v.normalize_therapy("VAZALORE")[1]
        'rxcui:1191'

        :param query: Therapy query normalize
        :raises TokenRetrievalError: If AWS credentials are expired
        :return: Therapy normalization response and normalized therapy ID, if available.
        """
        return self._normalize_concept(query, self.therapy_query_handler, "therapy")

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
            therapy_norm_resp.model_dump().get("therapy", {}).get("extensions") or []
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
                                "conceptType": indication["conceptType"],
                                "name": indication["name"],
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

    @staticmethod
    def _normalize_concept(
        query: str,
        query_handler: GeneQueryHandler | DiseaseQueryHandler | TherapyQueryHandler,
        concept_name: str,
    ) -> tuple[NormalizedGene | NormalizedDisease | NormalizedTherapy, str | None]:
        """Attempt to normalize a concept

        :param query: Query to normalize
        :param query_handler: Query handler for normalizer
        :param concept_name: Name of concept (gene, disease, therapy)
        :raises TokenRetrievalError: If AWS credentials are expired
        :return: Normalizer response and normalized ID, if available.
        """
        normalizer_resp = None
        normalized_id = None

        try:
            normalizer_resp = query_handler.normalize(query)
        except TokenRetrievalError:
            raise
        except Exception:
            _logger.exception(
                "%s Normalizer raised an exception using query %s",
                concept_name.capitalize(),
                query,
            )
        else:
            if normalizer_resp.match_type:
                normalized_id = getattr(normalizer_resp, concept_name).id.split(
                    f"normalize.{concept_name}."
                )[-1]

        return normalizer_resp, normalized_id


class NormalizerName(str, Enum):
    """Constrain normalizer CLI options."""

    GENE = "gene"
    DISEASE = "disease"
    THERAPY = "therapy"

    def __repr__(self) -> str:
        """Print as simple string rather than enum wrapper, e.g. 'gene' instead of
        <NormalizerName.GENE: 'gene'>.

        Makes Click error messages prettier.

        :return: formatted enum value
        """
        return f"'{self.value}'"


def check_normalizers(
    db_url: str | None, normalizers: Iterable[NormalizerName] | None = None
) -> bool:
    """Perform basic health checks on the gene, disease, and therapy normalizers.

    Uses the internal health check methods provided by each. Note that health check
    failures (i.e. tables unavailable or unpopulated) are logged as WARNINGs, but
    unhandled exceptions encountered during checks are suppressed and logged as ERRORs.

    >>> from metakb.normalizers import check_normalizers, NormalizerName
    >>> check_normalizers([NormalizerName.DISEASE])
    True  # indicates success
    >>> check_normalizers([NormalizerName.THERAPY])
    False  # indicates failure

    :param db_url: optional designation of DB URL to use for each. Currently only
        works for DynamoDB. If not given, normalizers will fall back on their own
        env var/default configurations.
    :param normalizers: names of specific normalizers to check (check all if empty/None)
    :return: True if all normalizers pass all checks, False if any failures are
        encountered.
    """
    success = True
    normalizer_map = {
        NormalizerName.DISEASE: create_disease_db,
        NormalizerName.THERAPY: create_therapy_db,
        NormalizerName.GENE: create_gene_db,
    }
    if normalizers:
        normalizer_map = {k: v for k, v in normalizer_map.items() if k in normalizers}
    for name, create_db in normalizer_map.items():
        db = create_db(db_url)
        try:
            schema_initialized = db.check_schema_initialized()
            if not schema_initialized:
                _logger.warning(
                    "Schema for %s normalizer appears incomplete or nonexistent.",
                    name.value,
                )
                success = False
                continue
            tables_populated = db.check_tables_populated()
            if not tables_populated:
                _logger.warning(
                    "Tables for %s normalizer appear to be unpopulated.", name.value
                )
                success = False
        except Exception:
            _logger.exception(
                "Encountered exception while checking %s normalizer", name.value
            )
            success = False
    return success


class IllegalUpdateError(Exception):
    """Raise if illegal update operation is attempted."""


# map normalizer to env var used to designate production DB setting
NORMALIZER_AWS_ENV_VARS = {
    NormalizerName.DISEASE: DISEASE_AWS_ENV_VAR_NAME,
    NormalizerName.THERAPY: THERAPY_AWS_ENV_VAR_NAME,
    NormalizerName.GENE: GENE_AWS_ENV_VAR_NAME,
}

# map normalizer to update function
_NORMALIZER_METHOD_DISPATCH = {
    NormalizerName.GENE: update_gene_db,
    NormalizerName.THERAPY: update_therapy_db,
    NormalizerName.DISEASE: update_disease_db,
}


def update_normalizer(normalizer: NormalizerName, db_url: str | None) -> None:
    """Refresh data for a normalizer.

    :param normalizer: name of service to refresh
    :param db_url: normalizer DB URL. If not given, will fall back on normalizer
        defaults.
    :raise IllegalUpdateError: if attempting to update cloud DB instances
    """
    if NORMALIZER_AWS_ENV_VARS[normalizer] in os.environ:
        raise IllegalUpdateError
    updater_args = ["--update_all", "--update_merged"]
    if db_url:
        updater_args += ["--db_url", db_url]
    _NORMALIZER_METHOD_DISPATCH[normalizer](updater_args)
