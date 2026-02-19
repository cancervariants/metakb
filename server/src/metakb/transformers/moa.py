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
    code,
)
from ga4gh.va_spec.base import (
    Direction,
    Document,
    MembershipOperator,
    Method,
    PrognosticPredicate,
    Statement,
    TherapeuticResponsePredicate,
    TherapyGroup,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Variation
from pydantic import ValidationError
from tqdm import tqdm

from metakb.harvesters.moa import MoaHarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.schemas.app import SourceName
from metakb.transformers.base import (
    MoaEvidenceLevel,
    Transformer,
    _sanitize_name,
)

_logger = logging.getLogger(__name__)


class MoaTransformer(Transformer):
    """A class for transforming MOA resources to common data model."""

    def _create_method(self) -> Method:
        """Get MOA classification method object for use in study statements

        :return: MOA method
        """
        return Method(
            id="moa.method:2021",
            name="MOAlmanac (2021)",
            reportedIn=Document(
                name="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
                doi="10.1038/s43018-021-00243-3",
                pmid="35121878",
            ),
        )

    async def transform(self, harvested_data: MoaHarvestedData) -> None:
        """Transform MOA harvested JSON to common data model. Will store transformed
        results in ``processed_data`` instance variable.

        :param harvested_data: MOA harvested data
        """
        total = len(harvested_data.sources) + len(harvested_data.assertions)
        pbar = tqdm(total=total)

        docs_map = {}
        for source in harvested_data.sources:
            source_doc = self._create_document(source)
            docs_map[source["id"]] = source_doc
            pbar.update(1)

        # Add variant therapeutic response study statement data. Will update `statements`
        for assertion in harvested_data.assertions:
            await self._transform_assertion(assertion, docs_map)
            pbar.update(1)
        pbar.close()

    async def _transform_assertion(
        self, assertion: dict, docs_map: dict[str, Document]
    ) -> None:
        """Create Variant Study Statements from MOA assertions.

        Will add associated values to ``processed_data`` instance variable
        (``therapies``, ``conditions``, and ``statements``).

        :param assertions: MOA assertion record
        :param docs_map: map from moa source ID to corresponding GKS Document object
        """
        assertion_id = f"moa.assertion:{assertion['id']}"

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
                code=code(evidence_level.value),
            ),
            mappings=self.evidence_level_to_vicc_concept_mapping[evidence_level],
        )

        # Add variant
        variant = await self._create_categorical_variant(assertion["variant"])
        if not variant:
            return

        # Add disease
        moa_disease = self._create_disease(assertion["disease"])
        if not moa_disease:
            _logger.debug(
                "%s has no disease for disease %s", assertion_id, assertion["disease"]
            )
            return

        # Add gene
        if gene_name := assertion["variant"].get("gene"):
            moa_gene = self._create_gene(gene_name)
        else:
            return

        # Add document
        document = docs_map[assertion["source_id"]]

        # Add allele origin
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
            "specifiedBy": self._create_method(),
            "reportedIn": [document],
        }
        prop_params = {
            "alleleOriginQualifier": allele_origin_qualifier,
            "geneContextQualifier": moa_gene,
            "subjectVariant": variant,
        }

        if assertion["favorable_prognosis"] == "":  # can be either 0, 1, or ""
            prop_params["objectTherapeutic"] = self._create_therapeutic(assertion)

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

    async def _create_categorical_variant(
        self, variant: dict
    ) -> CategoricalVariant | None:
        """Create Categorical Variant object for MOA variant record

        Mutates instance variable ``processed_data.variations``

        :param variant: variants in MOAlmanac
        :return: constructed categorical variant object, if able to normalize
        """
        if variant.get("gene2"):
            # Do not support gene fusions for now
            return None

        variant_id = variant["id"]
        moa_variant_id = f"moa.variant:{variant_id}"
        feature = variant["feature"]
        moa_variation = None
        moa_gene_value = variant.get("gene") or variant.get("gene1")
        protein_change = variant.get("protein_change")
        constraints = None
        extensions = []

        if (
            variant["feature_type"] == "somatic_variant"
            and variant["alternate_allele"] is None
            and feature == moa_gene_value
            and protein_change is None
            # no slam-dunk catvar solution exists for defining specific exons as features --
            # see https://github.com/ga4gh/cat-vrs/discussions/161
            and variant["exon"] is None
        ):
            gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(
                feature
            )
            feature = f"{feature} Mutation"
            if not normalized_gene_id:
                _logger.debug("Unable to normalize feature term: %s", feature)
                extensions.append(self._get_vicc_normalizer_failure_ext())
            else:
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
                    id_ = f"moa.gene:{_sanitize_name(feature)}"
                    extensions.append(self._get_vicc_normalizer_failure_ext())

                gene_concept = MappableConcept(
                    id=id_,
                    conceptType="Gene",
                    name=gene_norm_resp.gene.name if gene_norm_resp.gene else None,
                    mappings=mappings or None,
                    extensions=extensions or None,
                )
                constraints = [FeatureContextConstraint(featureContext=gene_concept)]
        elif (
            "rearrangement_type" in variant or not protein_change or not moa_gene_value
        ):
            _logger.debug(
                "Variation Normalizer does not support %s: %s",
                moa_variant_id,
                feature,
            )
            extensions.append(self._get_vicc_normalizer_failure_ext())
        else:
            # Form query and run through variation-normalizer
            # For now, the normalizer only support amino acid substitution
            vrs_variation = None
            normalize_gene_response = self.vicc_normalizers.normalize_gene(
                moa_gene_value
            )
            if not normalize_gene_response[0].gene:
                extensions.append(self._get_vicc_normalizer_failure_ext())
            else:
                query = f"{normalize_gene_response[0].gene.name} {protein_change[2:]}"
                vrs_variation = await self.vicc_normalizers.normalize_variation(query)

                if not vrs_variation:
                    _logger.debug(
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
                    code=code(str(variant_id)),
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

        self.processed_data.categorical_variants.append(cv)
        return cv

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

    def _create_gene(self, gene: str) -> MappableConcept:
        """Create gene object for MOA gene record

        Mutates instance variable ``processed_data.genes``

        :param gene: gene from MOAlmanac
        :return:
        """
        gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(gene)
        mappings = []
        extensions = []
        if normalized_gene_id:
            mappings.extend(
                self._get_vicc_normalizer_mappings(normalized_gene_id, gene_norm_resp)
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
        self.processed_data.genes.append(moa_gene)
        return moa_gene

    def _create_document(self, source: dict) -> Document:
        """Create document object for MOA source

        Mutates instance variable ``processed_data.documents``

        :param sources: All sources in MOA
        """
        source_id = source["id"]
        document = Document(
            id=f"moa.source:{source_id}",
            title=source["citation"],
            urls=[source["url"]] if source["url"] else None,
            pmid=str(source["pmid"]) if source["pmid"] else None,
            doi=source["doi"] or None,
            extensions=[Extension(name="source_type", value=source["type"])],
        )
        self.processed_data.documents.append(document)
        return document

    def _create_therapeutic(
        self, assertion: dict
    ) -> MappableConcept | TherapyGroup | None:
        """Get therapy mappable concept (single) or therapy group (multiple)

        :param assertion: MOA assertion record
        :return: Therapy object represented as a mappable concept or therapy group
        """
        therapy = assertion["therapy"]
        therapy_name = therapy["name"]
        if not therapy_name:
            _logger.debug("%s has no therapy_name", assertion["id"])
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
            therapy_id = self._compute_combo_id(
                self.name,
                TherapyGroup,
                membership_operator,
                [f"moa.therapy:{t['name']}" for t in therapies],
            )
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

    def _add_therapy(
        self,
        therapy_id: str,
        therapies: list[dict],
        membership_operator: MembershipOperator | None,
        therapy_type: str | None = None,
    ) -> MappableConcept | None:
        """Create therapy mappable concept given therapies

        Will add ``therapy_id`` to ``therapies``

        :param therapy_id: ID for therapy
        :param therapies: List of therapy objects. If `membership_operator` is `None`,
            the list will only contain a single therapy.
        :param membership_operator: The logical relationship between ``therapies``
        :param therapy_type: Therapy type
        :return: Therapy mappable concept, if ``therapy_type`` is supported
        """
        if membership_operator is None:
            therapy = self._get_therapy(therapy_id, therapies[0])
            self.processed_data.therapies.append(therapy)
        elif membership_operator == MembershipOperator.AND:
            therapy = self._get_combination_therapy(
                therapy_id, therapies, therapy_type=therapy_type
            )
            self.processed_data.therapy_groups.append(therapy)
        else:
            _logger.debug(
                "Membership operator is not supported: %s", membership_operator
            )
            return None

        return therapy

    def _get_combination_therapy(
        self,
        combination_therapy_id: str,
        therapies_in: list[dict],
        therapy_type: str | None = None,
    ) -> TherapyGroup | None:
        """Get Combination Therapy representation for source therapies

        :param combination_therapy_id: ID for Combination Therapy
        :param therapies: List of source therapy objects
        :param therapy_type: Therapy type provided by source
        :return: Combination Therapy
        """
        therapies = []

        for therapy in therapies_in:
            therapy_id = f"moa.therapy:{_sanitize_name(therapy['name'])}"
            therapy_mc = self._add_therapy(
                therapy_id,
                [therapy],
                membership_operator=None,
            )
            if not therapy_mc:
                return None

            therapies.append(therapy_mc)

        extensions = [
            Extension(name=f"{SourceName.MOA.value}_therapy_type", value=therapy_type)
        ]

        try:
            tg = TherapyGroup(
                id=combination_therapy_id,
                therapies=therapies,
                extensions=extensions,
                membershipOperator=MembershipOperator.AND,
            )
        except ValidationError as e:
            # if combination validation checks fail
            _logger.debug(
                "ValidationError raised when attempting to create Combination Therapy: %s",
                e,
            )
            tg = None

        return tg

    def _get_therapy(self, therapy_id: str, therapy: dict) -> MappableConcept:
        """Get Therapy mappable concept for a MOA therapy name.

        Will run `name` through therapy-normalizer.

        :param therapy_id: Generated therapy ID
        :param therapy: MOA therapy name
        :return: Therapy represented as a mappable concept
        """
        mappings = []
        extensions = []
        name = therapy["name"]

        (
            therapy_norm_resp,
            normalized_therapeutic_id,
        ) = self.vicc_normalizers.normalize_therapy(name)

        if not normalized_therapeutic_id:
            _logger.debug("Therapy Normalizer unable to normalize: %s", therapy)
            extensions.append(self._get_vicc_normalizer_failure_ext())
            id_ = therapy_id
        else:
            id_ = f"moa.{therapy_norm_resp.therapy.id}"

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

        return MappableConcept(
            id=id_,
            conceptType="Therapy",
            name=name,
            mappings=mappings or None,
            extensions=extensions or None,
        )

    def _create_disease(self, disease: dict) -> MappableConcept | None:
        """Create or get disease given MOA disease.

        Since there may be duplicate Oncotree code/terms with different names, the first
        name will be used as the Disease name. Others will be added to the extensions
        aliases field.

        :param disease: MOA disease object
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

        normalized_disease_id = None
        for query in queries:  # Order matters (use highest match first)
            (
                disease_norm_resp,
                normalized_disease_id,
            ) = self.vicc_normalizers.normalize_disease(query)
            if normalized_disease_id:
                break

        if not normalized_disease_id:
            _logger.debug("Disease Normalizer unable to normalize: %s", queries)
            extensions.append(self._get_vicc_normalizer_failure_ext())
            id_ = f"moa.disease:{_sanitize_name(disease_name)}"
        else:
            id_ = f"moa.{disease_norm_resp.disease.id}"
            mappings.extend(
                self._get_vicc_normalizer_mappings(
                    normalized_disease_id, disease_norm_resp
                )
            )

        moa_disease = MappableConcept(
            id=id_,
            conceptType="Disease",
            name=disease_name,
            mappings=mappings or None,
            extensions=extensions or None,
        )

        self.processed_data.conditions.append(moa_disease)
        return moa_disease
