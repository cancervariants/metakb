"""A module to convert MOA resources to common data model"""

import json
import logging
from pathlib import Path
from typing import ClassVar

from ga4gh.cat_vrs.models import CategoricalVariant, DefiningAlleleConstraint
from ga4gh.core import sha512t24u
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
)
from ga4gh.va_spec.base import (
    Direction,
    Document,
    MembershipOperator,
    PrognosticPredicate,
    Statement,
    TherapeuticResponsePredicate,
    TherapyGroup,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Variation

from metakb import APP_ROOT
from metakb.harvesters.moa import MoaHarvestedData
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.transformers.base import (
    MethodId,
    MoaEvidenceLevel,
    Transformer,
    _sanitize_name,
    _TransformedRecordsCache,
)

logger = logging.getLogger(__name__)


class _MoaTransformedCache(_TransformedRecordsCache):
    """Create model for caching MOA data"""

    variations: ClassVar[dict[str, dict]] = {}
    documents: ClassVar[dict[str, Document]] = {}
    normalized_therapies: ClassVar[
        dict[str, MappableConcept]
    ] = {}  # normalized_id: therapy


class MoaTransformer(Transformer):
    """A class for transforming MOA resources to common data model."""

    def __init__(
        self,
        data_dir: Path = APP_ROOT / "data",
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize MOAlmanac Transformer class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested MOA data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        # Method will always be the same
        self.processed_data.methods = [
            self.methods_mapping[MethodId.MOA_ASSERTION_BIORXIV.value]
        ]
        self._cache = self._create_cache()

    def _create_cache(self) -> _MoaTransformedCache:
        """Create cache for transformed records"""
        return _MoaTransformedCache()

    async def transform(self, harvested_data: MoaHarvestedData) -> None:
        """Transform MOA harvested JSON to common data model. Will store transformed
        results in ``processed_data`` instance variable.

        :param harvested_data: MOA harvested data
        """
        # Add gene, variant, and source data to ``processed_data`` instance variable
        # (``genes``, ``variations``, and ``documents``)
        self._add_genes(harvested_data.genes)
        await self._add_categorical_variants(harvested_data.variants)
        self._add_documents(harvested_data.sources)

        # Add variant therapeutic response study statement data. Will update `statements`
        for assertion in harvested_data.assertions:
            await self._add_variant_study_stmt(assertion)

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
            logger.debug(
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
            logger.debug(
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
                logger.debug(
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

    async def _add_categorical_variants(self, variants: list[dict]) -> None:
        """Create Categorical Variant objects for all MOA variant records.

        Mutates instance variables ``_cache['variations']`` and
        ``processed_data.variations``

        :param variants: All variants in MOAlmanac
        """
        for variant in variants:
            if variant.get("gene2"):
                # Do not support gene fusions for now
                continue

            variant_id = variant["id"]
            moa_variant_id = f"moa.variant:{variant_id}"
            feature = variant["feature"]
            moa_variation = None
            gene = variant.get("gene") or variant.get("gene1")
            moa_gene = self._cache.genes[_sanitize_name(gene)] if gene else None
            protein_change = variant.get("protein_change")
            constraints = None
            extensions = []

            if "rearrangement_type" in variant or not protein_change or not gene:
                logger.debug(
                    "Variation Normalizer does not support %s: %s",
                    moa_variant_id,
                    feature,
                )
                extensions.append(self._get_vicc_normalizer_failure_ext())
            else:
                # Form query and run through variation-normalizer
                # For now, the normalizer only support amino acid substitution
                vrs_variation = None
                gene = moa_gene.name
                query = f"{gene} {protein_change[2:]}"
                vrs_variation = await self.vicc_normalizers.normalize_variation(query)

                if not vrs_variation:
                    logger.debug(
                        "Variation Normalizer unable to normalize: moa.variant: %s using query: %s",
                        variant_id,
                        query,
                    )
                    extensions.append(self._get_vicc_normalizer_failure_ext())
                else:
                    # Create VRS Variation object
                    params = vrs_variation.model_dump(exclude_none=True)
                    moa_variant_id = f"moa.variant:{variant_id}"
                    params["id"] = vrs_variation.id
                    moa_variation = Variation(**params)
                    constraints = [DefiningAlleleConstraint(allele=moa_variation.root)]

            # Add MOA representative coordinate data to extensions
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

            # Add mappings data
            mappings = [
                ConceptMapping(
                    coding=Coding(
                        id=moa_variant_id,
                        code=str(variant_id),
                        system="https://moalmanac.org",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            ]

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

            cv = CategoricalVariant(
                id=moa_variant_id,
                name=feature,
                constraints=constraints,
                mappings=mappings or None,
                extensions=extensions,
                members=members,
            )

            self._cache.variations[variant_id] = {
                "cv": cv,
                "moa_gene": moa_gene,
            }
            self.processed_data.categorical_variants.append(cv)

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
                logger.debug(
                    "Variation Normalizer unable to normalize genomic representation: %s",
                    gnomad_vcf,
                )
        else:
            logger.debug(
                "Not enough enough information provided to create genomic representation: %s",
                moa_rep_coord,
            )

        return members

    def _add_genes(self, genes: list[str]) -> None:
        """Create gene objects for all MOA gene records.

        Mutates instance variables ``_cache['genes']`` and ``processed_data.genes``

        :param genes: All genes in MOAlmanac
        """
        for gene in genes:
            gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(
                gene
            )
            mappings = []
            extensions = []
            if normalized_gene_id:
                mappings.extend(
                    self._get_vicc_normalizer_mappings(
                        normalized_gene_id, gene_norm_resp
                    )
                )
                id_ = f"moa.{gene_norm_resp.gene.id}"
            else:
                id_ = f"moa.gene:{_sanitize_name(gene)}"
                extensions.append(self._get_vicc_normalizer_failure_ext())

            moa_gene = MappableConcept(
                id=id_,
                conceptType="Gene",
                name=gene,
                mappings=mappings or None,
                extensions=extensions or None,
            )
            self._cache.genes[_sanitize_name(gene)] = moa_gene
            self.processed_data.genes.append(moa_gene)

    def _add_documents(self, sources: list) -> None:
        """Create document objects for all MOA sources.
        Mutates instance variables ``processed_data.documents`` and
        ``self._cache.documents"]``

        :param sources: All sources in MOA
        """
        for source in sources:
            source_id = source["id"]
            document = Document(
                id=f"moa.source:{source_id}",
                title=source["citation"],
                urls=[source["url"]] if source["url"] else None,
                pmid=source["pmid"] if source["pmid"] else None,
                doi=source["doi"] if source["doi"] else None,
                extensions=[Extension(name="source_type", value=source["type"])],
            )
            self._cache.documents[source_id] = document
            self.processed_data.documents.append(document)

    def _get_therapy_or_group(
        self, assertion: dict
    ) -> MappableConcept | TherapyGroup | None:
        """Get therapy mappable concept (single) or therapy group (multiple)

        :param assertion: MOA assertion record
        :return: Therapy object represented as a mappable concept or therapy group
        """
        therapy = assertion["therapy"]
        therapy_name = therapy["name"]
        if not therapy_name:
            logger.debug("%s has no therapy_name", assertion["id"])
            return None

        therapy_type = therapy["type"]

        if "+" in therapy_name:
            # Indicates multiple therapies
            if therapy_type.upper() in {
                "COMBINATION THERAPY",
                "IMMUNOTHERAPY",
                "RADIATION THERAPY",
                "TARGETED THERAPY",
            }:
                membership_operator = MembershipOperator.AND
            else:
                # skipping HORMONE and CHEMOTHERAPY for now
                return None

            therapies = [{"name": tn.strip()} for tn in therapy_name.split("+")]
            therapeutic_digest = self._get_digest_for_str_lists(
                [f"moa.therapy:{tn}" for tn in therapies]
            )
            therapy_id = f"moa.ctid:{therapeutic_digest}"
        else:
            therapy_id = f"moa.therapy:{_sanitize_name(therapy_name)}"
            therapies = [{"name": therapy_name}]
            membership_operator = None

        return self._add_therapy(
            therapy_id,
            therapies,
            membership_operator,
            therapy_type,
        )

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
    ) -> None:
        """MOA does not support therapeutic substitute group

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies: List of therapy objects
        :return: None, since not supported by MOA
        """

    def _resolve_concept_discrepancy(
        self,
        cached_id: str,
        cached_obj: MappableConcept,
        cached_label: str,
        moa_concept_label: str,
        is_disease: bool = False,
    ) -> None:
        """Resolve conflict where MOA disease or therapy resolve to same normalized
        concept

        The min name will be used as the primary name for the mappable concept, and
        the other name will be added as an alias in extensions.
        The cache will be updated with updated object.
        The cached object will be removed from ``self.processed_data``

        :param cached_id: ID found in cache
        :param cached_obj: Mappable concept found in cache for ``cached_id``. This will
            be mutated
        :param cached_label: Label for ``cached_obj``
        :param moa_concept_label: MOA concept name
        :param is_disease: ``True`` if ``cached_obj`` is a disease. ``False`` if
            ``cached_obj`` is a therapy
        """
        logger.debug(
            "MOA %s and %s resolve to same concept %s",
            moa_concept_label,
            cached_label,
            cached_id,
        )
        alias = max(moa_concept_label, cached_label)
        cached_obj.name = min(moa_concept_label, cached_label)
        extensions = cached_obj.extensions or []

        aliases_ext = next(
            (ext for ext in extensions if ext.name == "aliases"),
            None,
        )
        if aliases_ext:
            if cached_obj.name in aliases_ext.value:
                aliases_ext.value.remove(cached_obj.name)
            aliases_ext.value.append(alias)
        else:
            extensions.append(Extension(name="aliases", value=[alias]))
            cached_obj.extensions = extensions

        if is_disease:
            self.processed_data.conditions = [
                c for c in self.processed_data.conditions if c.id != cached_obj.id
            ]
            cache = self._cache.conditions
        else:
            self.processed_data.therapies = [
                t for t in self.processed_data.therapies if t.id != cached_id
            ]
            cache = self._cache.normalized_therapies

        cache[cached_id] = cached_obj

    def _get_therapy(self, therapy_id: str, therapy: dict) -> MappableConcept:
        """Get Therapy mappable concept for a MOA therapy name.

        Will run `name` through therapy-normalizer.

        :param therapy_id: Generated therapy ID
        :param therapy: MOA therapy name
        :return: Therapy represented as a mappable concept
        """

        def _resolve_therapy_discrepancy(
            cached_id: str, moa_concept_label: str
        ) -> MappableConcept:
            """Resolve conflict where MOA therapy labels resolve to the same normalized
            concept

            If conflict occurs, the min name will be used as the primary name for the
            mappable concept, and the other name will be added as an alias in
            extensions. The cache will be updated.

            :param cached_id: Cached ID for therapy concept that is in
                ``self._cache.normalized_therapies``
            :param moa_concept_label: MOA provided name for therapy concept
            :return: Therapy represented as a mappable concept
            """
            therapy_norm_obj = self._cache.normalized_therapies[cached_id]
            og_therapy_norm_label = therapy_norm_obj.name
            if moa_concept_label != og_therapy_norm_label:
                self._resolve_concept_discrepancy(
                    cached_id,
                    therapy_norm_obj,
                    og_therapy_norm_label,
                    moa_concept_label,
                    is_disease=False,
                )
            return therapy_norm_obj

        mappings = []
        extensions = []
        name = therapy["name"]

        (
            therapy_norm_resp,
            normalized_therapeutic_id,
        ) = self.vicc_normalizers.normalize_therapy(name)

        if not normalized_therapeutic_id:
            logger.debug("Therapy Normalizer unable to normalize: %s", therapy)
            extensions.append(self._get_vicc_normalizer_failure_ext())
            id_ = therapy_id
        else:
            id_ = f"moa.{therapy_norm_resp.therapy.id}"

            if id_ in self._cache.normalized_therapies:
                return _resolve_therapy_discrepancy(id_, name)

            regulatory_approval_extension = (
                self.vicc_normalizers.get_regulatory_approval_extension(
                    therapy_norm_resp
                )
            )

            if regulatory_approval_extension:
                extensions.append(regulatory_approval_extension)

            mappings.extend(
                self._get_vicc_normalizer_mappings(
                    normalized_therapeutic_id, therapy_norm_resp
                )
            )

        therapy_concept = MappableConcept(
            id=id_,
            conceptType="Therapy",
            name=name,
            mappings=mappings or None,
            extensions=extensions or None,
        )
        self._cache.normalized_therapies[id_] = therapy_concept
        return therapy_concept

    def _add_disease(self, disease: dict) -> MappableConcept | None:
        """Create or get disease given MOA disease.

        First looks in cache for existing disease, if not found will attempt to
        transform. Will generate a digest from the original MOA disease object oncotree
        fields. This will be used as the key in the caches. Will add the generated
        digest to ``processed_data.conditions`` and ``_cache['conditions']``.

        Since there may be duplicate Oncotree code/terms with different names, the first
        name will be used as the Disease name. Others will be added to the extensions
        aliases field.

        :param disease: MOA disease object
        :return: Disease represented as a mappable concept
        """
        if not all(value for value in disease.values()):
            return None

        # Since MOA disease objects do not have an ID, we will create a digest from
        # the original MOA disease object.
        # The `name` is as written in the source text. In an upcoming MOA release, these
        # will have leading underscore to differentiate "raw" values
        oncotree_code = disease["oncotree_code"]
        oncotree_key = "oncotree_code" if oncotree_code else "oncotree_term"
        oncotree_value = oncotree_code or disease[oncotree_key]
        oncotree_kv = [f"{oncotree_key}:{oncotree_value}"]
        blob = json.dumps(oncotree_kv, separators=(",", ":")).encode("ascii")
        disease_id = sha512t24u(blob)
        moa_disease = self._cache.conditions.get(disease_id)
        if moa_disease:
            source_disease_name = disease["name"]
            if source_disease_name != moa_disease.name:
                self._resolve_concept_discrepancy(
                    disease_id,
                    moa_disease,
                    moa_disease.name,
                    source_disease_name,
                    is_disease=True,
                )
                self.processed_data.conditions.append(moa_disease)
            return moa_disease

        moa_disease = None
        moa_disease = self._get_disease(disease)
        self._cache.conditions[disease_id] = moa_disease
        self.processed_data.conditions.append(moa_disease)
        return moa_disease

    def _get_disease(self, disease: dict) -> MappableConcept:
        """Get Disease object for a MOA disease

        :param disease: MOA disease record
        :return: Disease represented as a mappable concept
        """
        queries = []
        mappings = []
        extensions = []

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

        disease_name = disease["name"]
        if ot_term:
            queries.append(ot_term)

        if disease_name:
            queries.append(disease_name)

        for query in queries:  # Order matters (use highest match first)
            (
                disease_norm_resp,
                normalized_disease_id,
            ) = self.vicc_normalizers.normalize_disease(query)
            if normalized_disease_id:
                break

        if not normalized_disease_id:
            logger.debug("Disease Normalizer unable to normalize: %s", queries)
            extensions.append(self._get_vicc_normalizer_failure_ext())
            id_ = f"moa.disease:{_sanitize_name(disease_name)}"
        else:
            id_ = f"moa.{disease_norm_resp.disease.id}"
            mappings.extend(
                self._get_vicc_normalizer_mappings(
                    normalized_disease_id, disease_norm_resp
                )
            )

        return MappableConcept(
            id=id_,
            conceptType="Disease",
            name=disease_name,
            mappings=mappings or None,
            extensions=extensions or None,
        )
