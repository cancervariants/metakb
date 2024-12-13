"""A module to convert MOA resources to common data model"""

import json
import logging
from pathlib import Path
from urllib.parse import quote

from ga4gh.cat_vrs.core_models import CategoricalVariant, DefiningContextConstraint
from ga4gh.core import sha512t24u
from ga4gh.core.domain_models import (
    CombinationTherapy,
    Disease,
    Gene,
    TherapeuticAgent,
    TherapeuticSubstituteGroup,
)
from ga4gh.core.entity_models import (
    Coding,
    ConceptMapping,
    Document,
    Extension,
    Relation,
)
from ga4gh.va_spec.profiles.var_study_stmt import (
    AlleleOriginQualifier,
    PrognosticPredicate,
    TherapeuticResponsePredicate,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
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
    TherapeuticProcedureType,
    Transformer,
)

logger = logging.getLogger(__name__)


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
        self.able_to_normalize = {
            "variations": {},
            "conditions": {},
            "therapeutic_procedures": {},
            "genes": {},
            "documents": {},
        }

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
        (``therapeutic_procedures``, ``conditions``, and ``statements``).
        ``able_to_normalize`` and ``unable_to_normalize`` will
        also be mutated for associated therapeutic_procedures and conditions.

        :param assertions: MOA assertion record
        """
        assertion_id = f"moa.assertion:{assertion['id']}"
        variant_id = assertion["variant"]["id"]

        # Check cache for variation record (which contains gene information)
        variation_gene_map = self.able_to_normalize["variations"].get(variant_id)
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
        moa_evidence_level = MoaEvidenceLevel[predictive_implication]
        strength = self.evidence_level_to_vicc_concept_mapping[moa_evidence_level]

        # Add disease
        moa_disease = self._add_disease(assertion["disease"])
        if not moa_disease:
            logger.debug(
                "%s has no disease for disease %s", assertion_id, assertion["disease"]
            )
            return

        # Add document
        document = self.able_to_normalize["documents"].get(assertion["source_id"])

        feature_type = assertion["variant"]["feature_type"]
        if feature_type == "somatic_variant":
            allele_origin_qualifier = AlleleOriginQualifier.SOMATIC
        elif feature_type == "germline_variant":
            allele_origin_qualifier = AlleleOriginQualifier.GERMLINE
        else:
            allele_origin_qualifier = None

        params = {
            "id": assertion_id,
            "description": assertion["description"],
            "strength": strength,
            "subjectVariant": variation_gene_map["cv"],
            "alleleOriginQualifier": allele_origin_qualifier,
            "geneContextQualifier": variation_gene_map["moa_gene"],
            "specifiedBy": self.processed_data.methods[0],
            "reportedIn": [document],
        }

        if assertion["favorable_prognosis"] == "":
            params["conditionQualifier"] = moa_disease
            params["predicate"] = (
                TherapeuticResponsePredicate.RESISTANCE
                if assertion["therapy"]["resistance"]
                else TherapeuticResponsePredicate.SENSITIVITY
            )
            params["objectTherapeutic"] = self._get_therapeutic_procedure(assertion)

            if not params["objectTherapeutic"]:
                logger.debug(
                    "%s has no therapeutic procedure for therapy_name %s",
                    assertion_id,
                    assertion["therapy"]["name"],
                )
                return
            statement = VariantTherapeuticResponseStudyStatement(**params)
        else:
            params["objectCondition"] = moa_disease
            params["predicate"] = (
                PrognosticPredicate.BETTER_OUTCOME
                if assertion["favorable_prognosis"]
                else PrognosticPredicate.WORSE_OUTCOME
            )
            statement = VariantPrognosticStudyStatement(**params)

        self.processed_data.statements.append(statement)

    async def _add_categorical_variants(self, variants: list[dict]) -> None:
        """Create Categorical Variant objects for all MOA variant records.
        Mutates instance variables ``able_to_normalize['variations']`` and
        ``processed_data.variations``, if the variation-normalizer can successfully
        normalize the variant

        :param variants: All variants in MOAlmanac
        """
        for variant in variants:
            variant_id = variant["id"]
            moa_variant_id = f"moa.variant:{variant_id}"
            feature = variant["feature"]
            # Skipping Fusion + Translocation + rearrangements that variation normalizer
            # does not support
            if "rearrangement_type" in variant:
                logger.debug(
                    "Variation Normalizer does not support %s: %s",
                    moa_variant_id,
                    feature,
                )
                continue

            # Gene is required to form query
            gene = variant.get("gene")
            if not gene:
                logger.debug(
                    "Variation Normalizer does not support %s: %s (no gene provided)",
                    moa_variant_id,
                    feature,
                )
                continue

            moa_gene = self.able_to_normalize["genes"].get(quote(gene))
            if not moa_gene:
                logger.debug(
                    "moa.variant:%s has no gene for gene, %s", variant_id, gene
                )
                continue

            # Form query and run through variation-normalizer
            # For now, the normalizer only support amino acid substitution
            vrs_variation = None
            if variant.get("protein_change"):
                gene = moa_gene.label
                query = f"{gene} {variant['protein_change'][2:]}"
                vrs_variation = await self.vicc_normalizers.normalize_variation([query])

                if not vrs_variation:
                    logger.debug(
                        "Variation Normalizer unable to normalize: moa.variant: %s using query: %s",
                        variant_id,
                        query,
                    )
                    continue
            else:
                logger.debug(
                    "Variation Normalizer does not support %s: %s",
                    moa_variant_id,
                    feature,
                )
                continue

            # Create VRS Variation object
            params = vrs_variation.model_dump(exclude_none=True)
            moa_variant_id = f"moa.variant:{variant_id}"
            params["id"] = vrs_variation.id
            moa_variation = Variation(**params)

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
            extensions = [
                Extension(name="MOA representative coordinate", value=moa_rep_coord)
            ]
            members = await self._get_variation_members(moa_rep_coord)

            # Add mappings data
            mappings = [
                ConceptMapping(
                    coding=Coding(
                        code=str(variant_id),
                        system="https://moalmanac.org/api/features/",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            ]

            if variant["rsid"]:
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
                label=feature,
                constraints=[DefiningContextConstraint(definingContext=moa_variation)],
                mappings=mappings or None,
                extensions=extensions,
                members=members,
            )

            self.able_to_normalize["variations"][variant_id] = {
                "cv": cv,
                "moa_gene": moa_gene,
            }
            self.processed_data.categorical_variants.append(cv)

    async def _get_variation_members(
        self, moa_rep_coord: dict
    ) -> list[Variation] | None:
        """Get members field for variation object. This is the related variant concepts.
        FOr now, only looks at genomic representative coordinate.

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
                [gnomad_vcf]
            )

            if vrs_genomic_variation:
                genomic_params = vrs_genomic_variation.model_dump(exclude_none=True)
                genomic_params["label"] = gnomad_vcf
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
        Mutates instance variables ``able_to_normalize['genes']`` and
        ``processed_data.genes``, if the gene-normalizer can successfully normalize the
        gene

        :param genes: All genes in MOAlmanac
        """
        for gene in genes:
            gene_norm_resp, normalized_gene_id = self.vicc_normalizers.normalize_gene(
                [gene]
            )
            if normalized_gene_id:
                moa_gene = Gene(
                    id=f"moa.normalize.gene:{quote(gene)}",
                    label=gene,
                    extensions=[
                        self._get_vicc_normalizer_extension(
                            normalized_gene_id, gene_norm_resp
                        )
                    ],
                )
                self.able_to_normalize["genes"][quote(gene)] = moa_gene
                self.processed_data.genes.append(moa_gene)
            else:
                logger.debug("Gene Normalizer unable to normalize: %s", gene)

    def _add_documents(self, sources: list) -> None:
        """Create document objects for all MOA sources.
        Mutates instance variables ``processed_data.documents`` and
        ``self.able_to_normalize["documents"]``

        :param sources: All sources in MOA
        """
        for source in sources:
            source_id = source["id"]

            if source["nct"]:
                mappings = [
                    ConceptMapping(
                        coding=Coding(
                            code=source["nct"],
                            system="https://clinicaltrials.gov/search?term=",
                        ),
                        relation=Relation.EXACT_MATCH,
                    )
                ]
            else:
                mappings = None

            document = Document(
                id=f"moa.source:{source_id}",
                title=source["citation"],
                urls=[source["url"]] if source["url"] else None,
                pmid=source["pmid"] if source["pmid"] else None,
                doi=source["doi"] if source["doi"] else None,
                mappings=mappings,
                extensions=[Extension(name="source_type", value=source["type"])],
            )
            self.able_to_normalize["documents"][source_id] = document
            self.processed_data.documents.append(document)

    def _get_therapeutic_procedure(
        self, assertion: dict
    ) -> TherapeuticAgent | TherapeuticSubstituteGroup | CombinationTherapy | None:
        """Get therapeutic procedure object

        :param assertion: MOA assertion record
        :return: Therapeutic procedure object, if found and able to be normalized
        """
        therapy = assertion["therapy"]
        therapy_name = therapy["name"]
        if not therapy_name:
            logger.debug("%s has no therapy_name", assertion["id"])
            return None

        therapy_interaction_type = therapy["type"]

        if "+" in therapy_name:
            # Indicates multiple therapies
            if therapy_interaction_type.upper() in {
                "COMBINATION THERAPY",
                "IMMUNOTHERAPY",
                "RADIATION THERAPY",
                "TARGETED THERAPY",
            }:
                therapeutic_procedure_type = (
                    TherapeuticProcedureType.COMBINATION_THERAPY
                )
            else:
                # skipping HORMONE and CHEMOTHERAPY for now
                return None

            therapies = [{"label": tn.strip()} for tn in therapy_name.split("+")]
            therapeutic_digest = self._get_digest_for_str_lists(
                [f"moa.therapy:{tn}" for tn in therapies]
            )
            therapeutic_procedure_id = f"moa.ctid:{therapeutic_digest}"
        else:
            therapeutic_procedure_id = f"moa.therapy:{therapy_name}"
            therapies = [{"label": therapy_name}]
            therapeutic_procedure_type = TherapeuticProcedureType.THERAPEUTIC_AGENT

        return self._add_therapeutic_procedure(
            therapeutic_procedure_id,
            therapies,
            therapeutic_procedure_type,
            therapy_interaction_type,
        )

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
        therapy_interaction_type: str,
    ) -> None:
        """MOA does not support therapeutic substitute group

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies: List of therapy objects
        :param therapy_interaction_type: Therapy type provided by MOA
        :return: None, since not supported by MOA
        """

    def _get_therapeutic_agent(self, therapy: dict) -> TherapeuticAgent | None:
        """Get Therapeutic Agent for a MOA therapy name.

        Will run `label` through therapy-normalizer.

        :param therapy: MOA therapy name
        :return: If able to normalize therapy, returns therapeutic agent
        """
        (
            therapy_norm_resp,
            normalized_therapeutic_id,
        ) = self.vicc_normalizers.normalize_therapy([therapy["label"]])

        if not normalized_therapeutic_id:
            logger.debug("Therapy Normalizer unable to normalize: %s", therapy)
            return None

        extensions = [
            self._get_vicc_normalizer_extension(
                normalized_therapeutic_id, therapy_norm_resp
            )
        ]

        regulatory_approval_extension = (
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)
        )

        if regulatory_approval_extension:
            extensions.append(regulatory_approval_extension)

        return TherapeuticAgent(
            id=f"moa.{therapy_norm_resp.therapeutic_agent.id}",
            label=therapy["label"],
            extensions=extensions,
        )

    def _add_disease(self, disease: dict) -> dict | None:
        """Create or get disease given MOA disease.

        First looks in cache for existing disease, if not found will attempt to
        normalize. Will generate a digest from the original MOA disease object oncotree
        fields. This will be used as the key in the caches. Will add the generated digest
        to ``processed_data.conditions`` and ``able_to_normalize['conditions']`` if
        disease-normalizer is able to normalize. Else will add the generated digest to
        ``unable_to_normalize['conditions']``.

        Since there may be duplicate Oncotree code/terms with different names, the first
        name will be used as the Disease label. Others will be added to the
        alternativeLabels field.

        :param disease: MOA disease object
        :return: Disease object if disease-normalizer was able to normalize
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

        vrs_disease = self.able_to_normalize["conditions"].get(disease_id)
        if vrs_disease:
            source_disease_name = disease["name"]
            if source_disease_name != vrs_disease.label:
                vrs_disease.alternativeLabels = vrs_disease.alternativeLabels or []

                if source_disease_name not in vrs_disease.alternativeLabels:
                    vrs_disease.alternativeLabels.append(source_disease_name)
            return vrs_disease

        vrs_disease = None
        if disease_id not in self.unable_to_normalize["conditions"]:
            vrs_disease = self._get_disease(disease)
            if vrs_disease:
                self.able_to_normalize["conditions"][disease_id] = vrs_disease
                self.processed_data.conditions.append(vrs_disease)
            else:
                self.unable_to_normalize["conditions"].add(disease_id)
        return vrs_disease

    def _get_disease(self, disease: dict) -> Disease | None:
        """Get Disease object for a MOA disease

        :param disease: MOA disease record
        :return: If able to normalize, Disease. Otherwise, `None`
        """
        queries = []
        mappings = []

        ot_code = disease["oncotree_code"]
        ot_term = disease["oncotree_term"]
        if ot_code:
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        code=ot_code,
                        system="https://oncotree.mskcc.org/",
                        label=ot_term,
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

        (
            disease_norm_resp,
            normalized_disease_id,
        ) = self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.debug("Disease Normalizer unable to normalize: %s", queries)
            return None

        return Disease(
            id=f"moa.{disease_norm_resp.disease.id}",
            label=disease_name,
            mappings=mappings if mappings else None,
            extensions=[
                self._get_vicc_normalizer_extension(
                    normalized_disease_id, disease_norm_resp
                )
            ],
        )
