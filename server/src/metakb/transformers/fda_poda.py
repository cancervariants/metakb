from pathlib import Path
from typing import ClassVar

from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    Document,
    Statement,
    TherapyGroup,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Allele

from metakb.harvesters.fda_poda import FdaPodaHarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import (
    MethodId,
    TransformedData,
    TransformedRecordsCache,
    Transformer,
)


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

    async def transform(self, harvested_data: FdaPodaHarvestedData) -> None:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """
        cdm = {
            "statements_evidence": [],
            "categorical_variants": [],
            "variations": [],
            "genes": [],
            "therapies": [],
            "conditions": [],
            "methods": [],
            "documents": [],
        }
        for statement in harvested_data.statements:
            proposition: VariantTherapeuticResponseProposition = statement.proposition  # type: ignore
            variant_query = proposition.subjectVariant.name
            normalized_variation = await self.vicc_normalizers.normalize_variation(
                variant_query
            )
            if normalized_variation:
                if isinstance(normalized_variation, Allele):
                    proposition.subjectVariant.constraints = [
                        DefiningAlleleConstraint(allele=normalized_variation)
                    ]
                    cdm["variants"].append(normalized_variation)
                else:
                    raise NotImplementedError
            cdm["categorical_variants"].append(proposition.subjectVariant)

            gene_query = proposition.geneContextQualifier.name
            normalized_gene_response, normalized_gene_id = (
                self.vicc_normalizers.normalize_gene(gene_query)
            )
            gene_mappings = proposition.geneContextQualifier.mappings or []
            gene_extensions = proposition.geneContextQualifier.extensions or []
            if normalized_gene_id:
                gene_mappings.extend(
                    self._get_vicc_normalizer_mappings(
                        normalized_gene_id, normalized_gene_response
                    )
                )
            else:
                gene_extensions.append(self._get_vicc_normalizer_failure_ext())
            cdm["genes"].append(proposition.geneContextQualifier)

            if not isinstance(proposition.conditionQualifier.root, MappableConcept):
                raise NotImplementedError
            disease_query = proposition.conditionQualifier.root.name
            normalized_disease_response, normalized_disease_id = (
                self.vicc_normalizers.normalize_disease(disease_query)
            )
            disease_mappings = proposition.conditionQualifier.root.mappings or []
            disease_extensions = proposition.conditionQualifier.root.extensions or []
            if normalized_disease_id:
                disease_mappings.extend(
                    self._get_vicc_normalizer_mappings(
                        normalized_disease_id, normalized_disease_response
                    )
                )
            else:
                disease_extensions.append(self._get_vicc_normalizer_failure_ext())
            cdm["conditions"].append(proposition.conditionQualifier)

            if not isinstance(proposition.objectTherapeutic.root, MappableConcept):
                raise NotImplementedError
            therapy_query = proposition.objectTherapeutic.root.name
            normalized_therapy_response, normalized_therapy_id = (
                self.vicc_normalizers.normalize_therapy(therapy_query)
            )
            therapy_mappings = proposition.objectTherapeutic.root.mappings or []
            therapy_extensions = proposition.objectTherapeutic.root.extensions or []
            if normalized_therapy_id:
                therapy_mappings.extend(
                    self._get_vicc_normalizer_mappings(
                        normalized_therapy_id, normalized_therapy_response
                    )
                )
            else:
                therapy_extensions.append(self._get_vicc_normalizer_failure_ext())
            cdm["therapies"].append(proposition.objectTherapeutic)

            if not cdm["methods"]:
                cdm["methods"].append(statement.specifiedBy)
            cdm["documents"].extend(statement.reportedIn)
            cdm["statements_evidence"].append(statement)

        self.transformed_data = TransformedData(**cdm)

    def _get_therapy(self, therapy: dict) -> MappableConcept | None:
        """Get therapy mappable concept for source therapy object

        :param therapy: source therapy object
        :return: therapy mappable concept
        """
        raise NotImplementedError

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
        raise NotImplementedError
