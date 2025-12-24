"""A module to convert MOA resources to common data model"""

import logging
from pathlib import Path

from ga4gh.cat_vrs.models import (
    CategoricalVariant,
    DefiningAlleleConstraint,
    FeatureContextConstraint,
)
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)
from ga4gh.va_spec.aac_2017 import (
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Direction,
    Document,
    EvidenceLine,
    PrognosticPredicate,
    Statement,
    Therapeutic,
    TherapeuticResponsePredicate,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Variation

from metakb.config import get_config
from metakb.harvesters.moa import MoaHarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import MoaEvidenceLevel, Transformer

_logger = logging.getLogger(__name__)


class MoaTransformer(Transformer):
    """A class for transforming MOA resources to common data model."""

    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize MOAlmanac Transformer class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested MOA data
        :param normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transformer")[0]
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = get_config().data_dir / self.name
        self.harvester_path = harvester_path
        self.vicc_normalizers = (
            ViccNormalizers() if normalizers is None else normalizers
        )

    async def transform(self, harvested_data: MoaHarvestedData) -> None:
        """Transform MOA harvested JSON to common data model. Will store transformed
        results in ``processed_data`` instance variable.

        # loop through statements
        # try to normalize variant, disease, drug
        # if success -> aggregated
        # otherwise -> no
        # need to handle therapy combos obviously

        :param harvested_data: MOA harvested data
        """
        sources_map = {source["id"] for source in harvested_data.sources}
        statements = []
        for assertion in harvested_data.assertions:
            normalized_gene, gene = self._normalize_moa_gene(
                assertion["variant"]["gene"]
            )
            normalized_disease, disease = self._normalize_moa_disease(
                assertion["disease"]
            )
            normalized_therapy, therapy = self._normalize_moa_therapy(
                assertion["therapy"]
            )
            normalized_variant, variant = await self._normalize_moa_variant(
                assertion["variant"]
            )
            did_normalize = (
                normalized_gene
                and normalized_disease
                and normalized_therapy
                and normalized_variant
            )
            if assertion["favorable_prognosis"] == "":
                statement = VariantTherapeuticResponseStudyStatement(
                    proposition=VariantTherapeuticResponseProposition(
                        geneContextQualifier=gene,
                        subjectVariant=variant,
                        conditionQualifier=disease,
                        objectTherapeutic=therapy,
                    ),
                    reportedIn=self._add_document(sources_map[assertion["source_id"]]),
                )
                if did_normalize:
                    statement = VariantPrognosticStudyStatement(
                        proposition=VariantTherapeuticResponseProposition(
                            geneContextQualifier=normalized_gene,
                            subjectVariant=normalized_variant,
                            conditionQualifier=normalized_disease,
                            objectTherapeutic=normalized_therapy,
                        ),
                        hasEvidenceLines=EvidenceLine(hasEvidenceItems=[statement]),
                    )
            else:
                statement = VariantPrognosticStudyStatement(
                    proposition=VariantPrognosticProposition(
                        geneContextQualifier=gene,
                        subjectVariant=variant,
                        objectCondition=disease,
                    ),
                    reportedIn=self._add_document(sources_map[assertion["source_id"]]),
                )
                if did_normalize:
                    statement = VariantPrognosticStudyStatement(
                        proposition=VariantPrognosticProposition(
                            geneContextQualifier=normalized_gene,
                            subjectVariant=normalized_variant,
                            objectCondition=normalized_disease,
                        ),
                        hasEvidenceLines=EvidenceLine(hasEvidenceItems=[statement]),
                    )
            statements.append(statement)

    def _normalize_moa_gene(
        self,
        gene_name: str,
    ) -> tuple[MappableConcept | None, MappableConcept]:
        """Transform MOA gene name to GKS MappableConcept and attempt normalization"""
        normalized_gene_response, _ = self.vicc_normalizers.normalize_gene(gene_name)
        moa_gene = MappableConcept(id=f"moa.gene:{gene_name}", name=gene_name)
        if normalized_gene_response and normalized_gene_response.gene:
            normalized_gene = normalized_gene_response.gene
            normalized_gene.extensions = None
            normalized_gene.mappings = None
        else:
            normalized_gene = None
        return normalized_gene, moa_gene

    def _normalize_moa_disease(
        self, disease: dict
    ) -> tuple[MappableConcept | None, MappableConcept]:
        """Transform MOA disease object to GKS MappableConcept and attempt normalization"""
        name = disease["name"]
        disease_id = f"moa.disease:{name}"
        queries = [name]
        mappings = []
        ot_code = disease["oncotree_code"]
        ot_term = disease["oncotree_term"]
        if ot_code:
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        id=f"oncotree:{ot_code}",
                        code=ot_code,
                        system="https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                        name=ot_term,
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            )
            queries.append(f"oncotree:{disease['oncotree_code']}")
        if ot_term:
            queries.append(ot_term)
        moa_disease = MappableConcept(
            id=disease_id,
            conceptType="Disease",
            name=name,
            mappings=mappings,
        )
        normalized_disease = None
        for query in queries:
            normalize_response, _ = self.vicc_normalizers.normalize_disease(query)
            if normalize_response and normalize_response.disease:
                normalized_disease = normalize_response.disease
                normalized_disease.extensions = []
                normalized_disease.mappings = []
                break
        return normalized_disease, moa_disease

    async def _normalize_moa_variant(
        self, variant: dict
    ) -> tuple[CategoricalVariant | None, CategoricalVariant]:
        """Transform MOA variant to CatVar and attempt normalization"""
        variant_id = f"moa.variant{variant['id']}"
        feature = variant["feature"]
        gene = variant.get("gene") or variant.get("gene1")
        protein_change = variant.get("protein_change")
        normalized_catvar = None

        # it's a fusion
        if variant.get("gene2"):
            pass
        # it's a feature context constraint-based catvar
        elif (
            variant["feature_type"] == "somatic_variant"
            and variant["alternate_allele"] is None
            and feature == gene
            and protein_change is None
            # no slam-dunk catvar solution exists for defining specific exons as features --
            # see https://github.com/ga4gh/cat-vrs/discussions/161
            and variant["exon"] is None
        ):
            feature = f"{feature} Mutation"
            normalized_gene, _ = self._normalize_moa_gene(feature)
            if normalized_gene:
                normalized_catvar = CategoricalVariant(
                    id=f"catvar:{feature}",
                    name=feature,
                    constraints=[
                        FeatureContextConstraint(featureContext=normalized_gene)
                    ],
                )
        # it's some other unsupported stuff
        elif "rearrangement_type" in variant or not protein_change or not gene:
            _logger.debug(
                "Variation Normalizer does not support %s: %s",
                variant_id,
                feature,
            )
        # it's a defining allele constraint-based catvar
        else:
            query = f"{gene} {protein_change[2:]}"
            vrs_variation = await self.vicc_normalizers.normalize_variation(query)
            if not vrs_variation:
                _logger.debug(
                    "Variation Normalizer unable to normalize: moa.variant: %s using query: %s",
                    variant_id,
                    query,
                )
            else:
                # Create VRS Variation object
                params = vrs_variation.model_dump(exclude_none=True)
                params["id"] = vrs_variation.id
                moa_variation = Variation(**params)
                normalized_catvar = CategoricalVariant(
                    id=f"catvar:{vrs_variation.id}",
                    name=query,
                    constraints=[DefiningAlleleConstraint(allele=moa_variation.root)],
                )

        extensions, members, mappings = await self._get_variant_extras(variant)
        return normalized_catvar, CategoricalVariant(
            id=variant_id,
            name=feature,
            extensions=extensions,
            members=members,
            mappings=mappings,
        )

    async def _get_variant_extras(
        self, variant: dict
    ) -> tuple[list[Extension], list[Variation], list[ConceptMapping]]:
        """Add extensions/members/mappings to MOA CatVar"""
        extensions = []
        coordinates_keys = [
            "chromosome",
            "start_position",
            "end_position",
            "reference_allele",
            "alternate_allele",
            "cdna_change",
            "protein_change",
            "exon",
        ]
        moa_rep_coord = {k: variant.get(k) for k in coordinates_keys}
        if any(moa_rep_coord.values()):
            extensions.append(
                Extension(name="MOA representative coordinate", value=moa_rep_coord)
            )

        if variant.get("locus"):
            extensions.append(Extension(name="MOA locus", value=variant["locus"]))
        members = await self._get_variation_members(moa_rep_coord)
        mappings = []
        if variant.get("rsid"):
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        code=variant["rsid"],
                        system="https://www.ncbi.nlm.nih.gov/snp/",
                    ),
                    relation=Relation.RELATED_MATCH,
                )
            )
        return extensions, members, mappings

    async def _get_variation_members(
        self, moa_rep_coord: dict
    ) -> list[Variation] | None:
        """Get members field for variation object. This is the related variant concepts.

        For now, only looks at genomic representative coordinate.

        :param moa_rep_coord: MOA Representative Coordinate
        :return: List containing one VRS variation record for associated genomic
            representation, if variation-normalizer was able to successfully normalize
        """
        members = None
        chromosome = moa_rep_coord.get("chromosome")
        pos = moa_rep_coord.get("start_position")
        ref = moa_rep_coord.get("reference_allele")
        alt = moa_rep_coord.get("alternate_allele")

        if all((chromosome, pos is not None, ref and ref != "-", alt and alt != "-")):
            gnomad_vcf = f"{chromosome}-{pos}-{ref}-{alt}"

            vrs_genomic_variation = await self.vicc_normalizers.normalize_variation(
                gnomad_vcf
            )

            if vrs_genomic_variation:
                genomic_params = vrs_genomic_variation.model_dump(exclude_none=True)
                genomic_params["extensions"] = (
                    None  # Don't care about capturing extensions for now
                )
                genomic_params["name"] = gnomad_vcf
                members = [Variation(**genomic_params)]
            else:
                _logger.debug(
                    "Variation Normalizer unable to normalize genomic representation: %s",
                    gnomad_vcf,
                )
        else:
            _logger.debug(
                "Not enough enough information provided to create genomic representation: %s",
                moa_rep_coord,
            )

        return members

    def _add_document(self, source: dict) -> None:
        """Create document object"""
        source_id = source["id"]
        return Document(
            id=f"moa.source:{source_id}",
            title=source["citation"],
            urls=[source["url"]] if source["url"] else None,
            pmid=source["pmid"] if source["pmid"] else None,
            doi=source["doi"] if source["doi"] else None,
            extensions=[Extension(name="source_type", value=source["type"])],
        )

    def _normalize_moa_therapy(
        self, therapy: dict
    ) -> tuple[Therapeutic | None, Therapeutic]:
        name = therapy["name"]
        if not name:
            raise ValueError
        if "+" in name:
            pass  # TODO handle combo case

        drug = Therapeutic(
            root=MappableConcept(id=f"moa.drug:{name}", conceptType="Drug", name=name)
        )
        normalized_drug = None
        return normalized_drug, drug

    #     if "+" in therapy_name:
    #         # Indicates multiple therapies
    #         if therapy_type.upper() in {
    #             "COMBINATION THERAPY",
    #             "IMMUNOTHERAPY",
    #             "RADIATION THERAPY",
    #             "TARGETED THERAPY",
    #         }:
    #             membership_operator = MembershipOperator.AND
    #         else:
    #             # skipping HORMONE and CHEMOTHERAPY for now
    #             return None
    #
    #         therapies = [{"name": tn.strip()} for tn in therapy_name.split("+")]
    #         therapeutic_digest = self._get_digest_for_str_lists(
    #             [f"moa.therapy:{tn}" for tn in therapies]
    #         )
    #         therapy_id = f"moa.ctid:{therapeutic_digest}"
    #     else:
    #         therapy_id = f"moa.therapy:{_sanitize_name(therapy_name)}"
    #         therapies = [{"name": therapy_name}]
    #         membership_operator = None
    #
    #     return self._add_therapy(
    #         therapy_id,
    #         therapies,
    #         membership_operator,
    #         therapy_type,
    #     )

    # def _resolve_concept_discrepancy(
    #     self,
    #     cached_id: str,
    #     cached_obj: MappableConcept,
    #     cached_label: str,
    #     moa_concept_label: str,
    #     is_disease: bool = False,
    # ) -> None:
    #     """Resolve conflict where MOA disease or therapy resolve to same normalized
    #     concept
    #
    #     The min name will be used as the primary name for the mappable concept, and
    #     the other name will be added as an alias in extensions.
    #     The cache will be updated with updated object.
    #     The cached object will be removed from ``self.processed_data``
    #
    #     :param cached_id: ID found in cache
    #     :param cached_obj: Mappable concept found in cache for ``cached_id``. This will
    #         be mutated
    #     :param cached_label: Label for ``cached_obj``
    #     :param moa_concept_label: MOA concept name
    #     :param is_disease: ``True`` if ``cached_obj`` is a disease. ``False`` if
    #         ``cached_obj`` is a therapy
    #     """
    #     _logger.debug(
    #         "MOA %s and %s resolve to same concept %s",
    #         moa_concept_label,
    #         cached_label,
    #         cached_id,
    #     )
    #     alias = max(moa_concept_label, cached_label)
    #     cached_obj.name = min(moa_concept_label, cached_label)
    #     extensions = cached_obj.extensions or []
    #
    #     aliases_ext = next(
    #         (ext for ext in extensions if ext.name == "aliases"),
    #         None,
    #     )
    #     if aliases_ext:
    #         if cached_obj.name in aliases_ext.value:
    #             aliases_ext.value.remove(cached_obj.name)
    #         aliases_ext.value.append(alias)
    #     else:
    #         extensions.append(Extension(name="aliases", value=[alias]))
    #         cached_obj.extensions = extensions
    #
    #     if is_disease:
    #         self.processed_data.conditions = [
    #             c for c in self.processed_data.conditions if c.id != cached_obj.id
    #         ]
    #         cache = self._cache.conditions
    #     else:
    #         self.processed_data.therapies = [
    #             t for t in self.processed_data.therapies if t.id != cached_id
    #         ]
    #         cache = self._cache.normalized_therapies
    #
    #     cache[cached_id] = cached_obj

    # def _get_therapy(self, therapy_id: str, therapy: dict) -> MappableConcept:
    #     """Get Therapy mappable concept for a MOA therapy name.
    #
    #     Will run `name` through therapy-normalizer.
    #
    #     :param therapy_id: Generated therapy ID
    #     :param therapy: MOA therapy name
    #     :return: Therapy represented as a mappable concept
    #     """
    #
    #     def _resolve_therapy_discrepancy(
    #         cached_id: str, moa_concept_label: str
    #     ) -> MappableConcept:
    #         """Resolve conflict where MOA therapy labels resolve to the same normalized
    #         concept
    #
    #         If conflict occurs, the min name will be used as the primary name for the
    #         mappable concept, and the other name will be added as an alias in
    #         extensions. The cache will be updated.
    #
    #         :param cached_id: Cached ID for therapy concept that is in
    #             ``self._cache.normalized_therapies``
    #         :param moa_concept_label: MOA provided name for therapy concept
    #         :return: Therapy represented as a mappable concept
    #         """
    #         therapy_norm_obj = self._cache.normalized_therapies[cached_id]
    #         og_therapy_norm_label = therapy_norm_obj.name
    #         if moa_concept_label != og_therapy_norm_label:
    #             self._resolve_concept_discrepancy(
    #                 cached_id,
    #                 therapy_norm_obj,
    #                 og_therapy_norm_label,
    #                 moa_concept_label,
    #                 is_disease=False,
    #             )
    #         return therapy_norm_obj
    #
    #     mappings = []
    #     extensions = []
    #     name = therapy["name"]
    #
    #     (
    #         therapy_norm_resp,
    #         normalized_therapeutic_id,
    #     ) = self.vicc_normalizers.normalize_therapy(name)
    #
    #     if not normalized_therapeutic_id:
    #         _logger.debug("Therapy Normalizer unable to normalize: %s", therapy)
    #         extensions.append(self._get_vicc_normalizer_failure_ext())
    #         id_ = therapy_id
    #     else:
    #         id_ = f"moa.{therapy_norm_resp.therapy.id}"
    #
    #         if id_ in self._cache.normalized_therapies:
    #             return _resolve_therapy_discrepancy(id_, name)
    #
    #         regulatory_approval_extension = (
    #             self.vicc_normalizers.get_regulatory_approval_extension(
    #                 therapy_norm_resp
    #             )
    #         )
    #
    #         if regulatory_approval_extension:
    #             extensions.append(regulatory_approval_extension)
    #
    #         mappings.extend(
    #             self._get_vicc_normalizer_mappings(
    #                 normalized_therapeutic_id, therapy_norm_resp
    #             )
    #         )
    #
    #     therapy_concept = MappableConcept(
    #         id=id_,
    #         conceptType="Therapy",
    #         name=name,
    #         mappings=mappings or None,
    #         extensions=extensions or None,
    #     )
    #     self._cache.normalized_therapies[id_] = therapy_concept
    #     return therapy_concept

    async def _add_variant_study_stmt(self, assertion: dict) -> None:
        """Create Variant Study Statements from MOA assertions.
        Will add associated values to ``processed_data`` instance variable
        (``therapies``, ``conditions``, and ``statements``).
        ``_cache`` will also be mutated for associated therapies and conditions.

        :param assertions: MOA assertion record
        """
        assertion_id = f"moa.assertion:{assertion['id']}"
        variant_id = assertion["variant"]["id"]

        # Check cache for variation record (which contains gene information)
        variation_gene_map = self._cache.variations.get(variant_id)
        if not variation_gene_map:
            _logger.debug(
                "%s has no variation for variant_id %s", assertion_id, variant_id
            )
            return

        # Get strength
        predictive_implication = (
            assertion["predictive_implication"]
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
            .upper()
        )
        evidence_level = MoaEvidenceLevel[predictive_implication]
        strength = MappableConcept(
            primaryCoding=Coding(
                system="https://moalmanac.org/about",
                code=evidence_level.value,
            ),
            mappings=self.evidence_level_to_vicc_concept_mapping[evidence_level],
        )

        # Add disease
        moa_disease = self._add_disease(assertion["disease"])
        if not moa_disease:
            _logger.debug(
                "%s has no disease for disease %s", assertion_id, assertion["disease"]
            )
            return

        # Add document
        document = self._cache.documents.get(assertion["source_id"])

        feature_type = assertion["variant"]["feature_type"]
        if feature_type == "somatic_variant":
            allele_origin_qualifier = MappableConcept(name="somatic")
        elif feature_type == "germline_variant":
            allele_origin_qualifier = MappableConcept(name="germline")
        else:
            allele_origin_qualifier = None

        stmt_params = {
            "id": assertion_id,
            "description": assertion["description"],
            "strength": strength,
            "specifiedBy": self.processed_data.methods[0],
            "reportedIn": [document],
        }
        prop_params = {
            "alleleOriginQualifier": allele_origin_qualifier,
            "geneContextQualifier": variation_gene_map["moa_gene"],
            "subjectVariant": variation_gene_map["cv"],
        }

        if assertion["favorable_prognosis"] == "":  # can be either 0, 1, or ""
            prop_params["objectTherapeutic"] = self._get_therapy_or_group(assertion)

            if not prop_params["objectTherapeutic"]:
                _logger.debug(
                    "%s has no therapy for therapy_name %s",
                    assertion_id,
                    assertion["therapy"]["name"],
                )
                return

            if assertion["therapy"]["resistance"] != "":  # can be either 0, 1, or ""
                predicate = TherapeuticResponsePredicate.RESISTANCE
                stmt_params["direction"] = (
                    Direction.SUPPORTS
                    if assertion["therapy"]["resistance"]
                    else Direction.DISPUTES
                )
            else:
                predicate = TherapeuticResponsePredicate.SENSITIVITY
                stmt_params["direction"] = (
                    Direction.SUPPORTS
                    if assertion["therapy"]["sensitivity"]
                    else Direction.DISPUTES
                )

            prop_params["predicate"] = predicate
            prop_params["conditionQualifier"] = moa_disease
            stmt_params["proposition"] = VariantTherapeuticResponseProposition(
                **prop_params
            )
        else:
            if assertion["favorable_prognosis"]:
                predicate = PrognosticPredicate.BETTER_OUTCOME
                direction = Direction.SUPPORTS
            else:
                predicate = PrognosticPredicate.WORSE_OUTCOME
                direction = Direction.DISPUTES

            prop_params["predicate"] = predicate
            stmt_params["direction"] = direction
            prop_params["objectCondition"] = moa_disease
            stmt_params["proposition"] = VariantPrognosticProposition(**prop_params)
        self.processed_data.statements_evidence.append(Statement(**stmt_params))
