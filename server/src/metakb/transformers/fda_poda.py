import logging
from pathlib import Path
from typing import ClassVar
import uuid

from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Condition,
    ConditionSet,
    Document,
    Statement,
    TherapyGroup,
)
from ga4gh.vrs.models import Allele

from metakb.harvesters.fda_poda import FdaPodaHarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import (
    MethodId,
    TransformedRecordsCache,
    Transformer,
    sanitize_name,
)

_logger = logging.getLogger(__name__)


class _FdaTransformedCache(TransformedRecordsCache):
    """Create model for caching FDA PODA data"""

    categorical_variants: ClassVar[dict[str, CategoricalVariant]] = {}
    documents: ClassVar[dict[str, Document]] = {}
    evidence: ClassVar[
        dict[
            str,
            Statement,
        ]
    ] = {}


class FdaPodaTransformer(Transformer):
    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )
        # Method will always be the same
        self.processed_data.methods = [
            self.methods_mapping[MethodId.FDA_APPROV_SOP.value]
        ]
        self._cache = self._create_cache()

    def _create_cache(self) -> _FdaTransformedCache:
        return _FdaTransformedCache()

    async def transform(self, harvested_data: FdaPodaHarvestedData) -> None:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """
        genes = [s.proposition.geneContextQualifier for s in harvested_data.statements]
        self._add_genes(genes)
        variants = [s.proposition.subjectVariant for s in harvested_data.statements]
        await self._add_categorical_variants(variants)
        diseases = [s.proposition.conditionQualifier for s in harvested_data.statements]
        self._add_diseases(diseases)
        documents = [d for s in harvested_data.statements for d in s.reportedIn]
        self._add_documents(documents)

        for statements in harvested_data.statements:
            pass

    def _add_genes(self, genes: list[MappableConcept]) -> None:
        """Create gene objects

        Mutates ``genes`` arg and the instance cache

        :param genes: All genes in FDA PODA data artifact
        """
        for gene in genes:
            name: str = gene.name  # type: ignore[reportAssignmentType]
            gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(
                name
            )
            if normalized_gene_id:
                gene.mappings = [
                    self._get_vicc_normalizer_mappings(
                        normalized_gene_id, gene_norm_resp
                    )
                ]
                gene.id = f"fda_poda.{gene_norm_resp.gene.id}"
            else:
                gene.extensions = [self._get_vicc_normalizer_failure_ext()]
            self._cache.genes[sanitize_name(name)] = gene
            self.processed_data.genes.append(gene)

    async def _add_categorical_variants(
        self, variants: list[CategoricalVariant]
    ) -> None:
        """Create normalized Categorical Variant objects

        Mutates ``variants`` arg and instance cache

        :param variants: Input variants
        """
        for variant in variants:
            variant_id: str = variant.id  # type: ignore[reportAssignmentType]
            extensions = []

            query: str = variant.name  # type: ignore[reportAssignmentType]
            vrs_variation = await self.vicc_normalizers.normalize_variation(query)

            if not vrs_variation:
                _logger.debug(
                    "Variation Normalizer unable to normalize query: %s",
                    query,
                )
                extensions.append(self._get_vicc_normalizer_failure_ext())
            else:
                if not isinstance(vrs_variation, Allele):
                    raise NotImplementedError
                variant.constraints = [DefiningAlleleConstraint(allele=vrs_variation)]

            self._cache.categorical_variants[variant_id] = variant
            self.processed_data.categorical_variants.append(variant)

    def _add_diseases(self, diseases: list[Condition]) -> None:
        for disease in diseases:
            if isinstance(disease.root, ConditionSet):
                raise NotImplementedError
            query = disease.root.name
            response, normalized_id = self.vicc_normalizers.normalize_disease(query)
            if normalized_id:
                disease.root.mappings = [
                    self._get_vicc_normalizer_mappings(normalized_id, response)
                ]
                disease.root.id = f"fda_poda.{response.disease.id}"
            else:
                disease.root.extensions = [self._get_vicc_normalizer_failure_ext()]
            self._cache.conditions[sanitize_name(disease.root.name)] = disease.root
            self.processed_data.conditions.append(disease.root)

    def _add_documents(self, documents: list[Document]) -> None:
        for document in documents:
            # TODO remove this once IDs are in source artifact
            if not document.id:
                document.id = f"fda_poda.doc:{uuid.uuid1()}"
            self._cache.documents[document.id] = document
            self.processed_data.documents.append(document)

    def _get_therapy(self, therapy: dict) -> MappableConcept | None:
        """Get therapy mappable concept for source therapy object

        :param therapy: source therapy object
        :return: therapy mappable concept
        """

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
    ) -> TherapyGroup | None:
        """Get Therapeutic Substitute Group for therapies

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies: List of therapy objects
        :return: Therapeutic Substitute Group
        """
