"""A module to convert MOA resources to common data model"""

import logging
from functools import cache
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
from ga4gh.va_spec.aac_2017 import (
    Classification,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Condition,
    Direction,
    Document,
    EvidenceLine,
    MembershipOperator,
    Method,
    PrognosticPredicate,
    Statement,
    System,
    Therapeutic,
    TherapeuticResponsePredicate,
    TherapyGroup,
    VariantPrognosticProposition,
    VariantTherapeuticResponseProposition,
)
from ga4gh.vrs.models import Variation

from metakb.config import get_config
from metakb.harvesters.moa import MoaHarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.transformers.base import MethodId, TransformedData, Transformer

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
        # try to normalize variant, disease, drug, gene
        # if success -> aggregated
        # otherwise -> not aggregated

        :param harvested_data: MOA harvested data
        """
        sources_map = {
            source["id"]: self._build_document(source)
            for source in harvested_data.sources
        }
        method = self._build_method()
        agg_method = self._build_aggregate_method()
        tmp_class = MappableConcept(
            id="metakb.classification:1",
            name="tmp metakb tr classification",
            primaryCoding=Coding(
                system=System.AMP_ASCO_CAP, code=code(Classification.TIER_I)
            ),
        )  # TODO figure this out for real!!!
        statements = []
        aggregated_statements = []
        for assertion in harvested_data.assertions:
            source = sources_map[assertion["source_id"]]
            if assertion["favorable_prognosis"] == "":
                if (
                    assertion["therapy"]["resistance"] == ""
                    and assertion["therapy"]["sensitivity"] == ""
                ):
                    # handle cases like assertion ID 849
                    _logger.error(
                        "No prognostic or sensitity/resistance response available for assertion: %s",
                        assertion,
                    )
                    continue
                aggregated_statement, statement = await self._build_tr_statement(
                    assertion, source, method, agg_method, tmp_class
                )
            else:
                aggregated_statement, statement = await self._build_prog_statement(
                    assertion, source, method, agg_method, tmp_class
                )
            statements.append(statement)
            if aggregated_statement:
                aggregated_statements.append(aggregated_statement)
        self.processed_data = TransformedData(
            statements_evidence=statements, statements_assertions=aggregated_statements
        )

    async def _build_prog_statement(
        self,
        assertion: dict,
        source: Document,
        method: Method,
        agg_method: Method,
        tmp_class: MappableConcept,
    ) -> tuple[VariantPrognosticStudyStatement | None, Statement]:
        aggregated_statement = None
        if moa_gene_value := assertion["variant"].get("gene"):
            normalized_gene, gene = self._normalize_moa_gene(moa_gene_value)
        else:
            normalized_gene, gene = None, None
        normalized_disease, disease = self._normalize_moa_disease(
            assertion["disease"]["name"],
            assertion["disease"]["oncotree_code"],
            assertion["disease"]["oncotree_term"],
        )
        normalized_variant, variant = await self._normalize_moa_variant(
            assertion["variant"]
        )
        if assertion["favorable_prognosis"]:
            predicate = PrognosticPredicate.BETTER_OUTCOME
            direction = Direction.SUPPORTS
        else:
            predicate = PrognosticPredicate.WORSE_OUTCOME
            direction = Direction.DISPUTES
        statement = Statement(
            id=f"moa.assertion:{assertion['id']}",
            description=assertion["description"],
            proposition=VariantPrognosticProposition(
                geneContextQualifier=gene,
                subjectVariant=variant,
                objectCondition=disease,
                predicate=predicate,
            ),
            direction=direction,
            reportedIn=[source],
            specifiedBy=method,
        )
        if normalized_gene and normalized_disease and normalized_variant:
            aggregated_statement = VariantPrognosticStudyStatement(
                id="metakb:id that sums up the proposition parts",
                proposition=VariantPrognosticProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    objectCondition=normalized_disease,
                    predicate=predicate,
                ),
                direction=direction,
                specifiedBy=agg_method,
                classification=tmp_class,
                hasEvidenceLines=[
                    EvidenceLine(
                        hasEvidenceItems=[statement],
                        directionOfEvidenceProvided=Direction.SUPPORTS,  # TODO is this right?
                    )
                ],
            )
        return aggregated_statement, statement

    async def _build_tr_statement(
        self,
        assertion: dict,
        source: Document,
        method: Method,
        agg_method: Method,
        tmp_class: MappableConcept,
    ) -> tuple[VariantTherapeuticResponseStudyStatement | None, Statement]:
        aggregated_statement = None
        if moa_gene_value := assertion["variant"].get("gene"):
            normalized_gene, gene = self._normalize_moa_gene(moa_gene_value)
        else:
            normalized_gene, gene = None, None
        normalized_disease, disease = self._normalize_moa_disease(
            assertion["disease"]["name"],
            assertion["disease"]["oncotree_code"],
            assertion["disease"]["oncotree_term"],
        )
        normalized_variant, variant = await self._normalize_moa_variant(
            assertion["variant"]
        )
        therapy = assertion["therapy"]
        normalized_therapy, moa_therapy = self._normalize_moa_therapy(
            therapy["name"], therapy["type"]
        )
        resistance, sensitivity = therapy["resistance"], therapy["sensitivity"]
        if resistance != "":  # can be either 0, 1, or ""
            predicate = TherapeuticResponsePredicate.RESISTANCE
            direction = Direction.SUPPORTS if resistance else Direction.DISPUTES
        else:
            predicate = TherapeuticResponsePredicate.SENSITIVITY
            direction = Direction.SUPPORTS if sensitivity else Direction.DISPUTES
        statement = Statement(
            id=f"moa.assertion:{assertion['id']}",
            description=assertion["description"],
            proposition=VariantTherapeuticResponseProposition(
                geneContextQualifier=gene,
                subjectVariant=variant,
                conditionQualifier=disease,
                objectTherapeutic=moa_therapy,
                predicate=predicate,
            ),
            direction=direction,
            reportedIn=[source],
            specifiedBy=method,
        )
        if (
            normalized_disease
            and normalized_gene
            and normalized_variant
            and normalized_therapy
        ):
            aggregated_statement = VariantTherapeuticResponseStudyStatement(
                id="metakb:id that sums up the proposition parts",
                proposition=VariantTherapeuticResponseProposition(
                    geneContextQualifier=normalized_gene,
                    subjectVariant=normalized_variant,
                    conditionQualifier=normalized_disease,
                    objectTherapeutic=normalized_therapy,
                    predicate=predicate,
                ),
                direction=direction,
                specifiedBy=agg_method,
                classification=tmp_class,
                hasEvidenceLines=[
                    EvidenceLine(
                        hasEvidenceItems=[statement],
                        directionOfEvidenceProvided=Direction.SUPPORTS,  # TODO is this right?
                    )
                ],
            )
        return aggregated_statement, statement

    @staticmethod
    def _build_method() -> Method:
        """Return MOA assertion method

        :return: Reference for MOA curation method
        """
        return Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            name="MOAlmanac (2021)",
            reportedIn=Document(
                name="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
                doi="10.1038/s43018-021-00243-3",
                pmid="35121878",
            ),
        )

    @staticmethod
    def _build_aggregate_method() -> Method:
        """Return tmp aggregation Method

        :return: working aggregation Method
        """
        return Method(
            id="metakb.method:2026",
            name="MetaKB (2026)",
            reportedIn=Document(
                name="Wagnerds et al",
                title="MetaKB v2",
                doi="10.1038/1111-1-1111-111-1111",
                pmid="9999999",
            ),
        )

    @cache  # noqa: B019
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

    @cache  # noqa: B019
    def _normalize_moa_disease(
        self, name: str, oncotree_code: str, oncotree_term: str
    ) -> tuple[Condition | None, Condition]:
        """Transform MOA disease object to GKS MappableConcept and attempt normalization

        :param name: disease name
        :param oncotree_code: oncotree ID (e.g. "CML")
        :param oncotree_term: disease name in Oncotree
        :return: normalized disease concept, if successful, and original MOA disease
            structured as GKS MappableConcept
        """
        disease_id = f"moa.disease:{name}"
        queries = [name]
        mappings = []
        if oncotree_code:
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        id=f"oncotree:{oncotree_code}",
                        code=code(oncotree_code),
                        system="https://oncotree.mskcc.org/?version=oncotree_latest_stable&field=CODE&search=",
                        name=oncotree_term,
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            )
            queries.append(f"oncotree:{oncotree_code}")
        if oncotree_term:
            queries.append(oncotree_term)
        moa_disease = Condition(
            MappableConcept(
                id=disease_id,
                conceptType="Disease",
                name=name,
                mappings=mappings,
            )
        )
        normalized_disease = None
        for query in queries:
            response, _ = self.vicc_normalizers.normalize_disease(query)
            if response and response.disease:
                normalized_disease = Condition(response.disease)
                normalized_disease.root.extensions = None
                normalized_disease.root.mappings = None
                break
        return normalized_disease, moa_disease

    async def _normalize_moa_variant(
        self, variant: dict
    ) -> tuple[CategoricalVariant | None, CategoricalVariant]:
        """Transform MOA variant to CatVar and attempt normalization

        :param variant: entire MOA variant object. The object keys are sort of unreliable
            so we just pass through the whole thing and work it out within the method
        :return: normalized variation as a CatVar, if successful, and original MOA variant
            as a text catvar
        """
        variant_id = f"moa.variant:{variant['id']}"
        feature = variant["feature"]
        gene = variant.get("gene") or variant.get("gene1")
        protein_change = variant.get("protein_change")
        normalized_catvar = None

        if variant.get("gene2"):
            # it's a fusion
            _logger.debug(
                "Not attempting variant normalization because it looks like a fusion: %s",
                variant,
            )
        elif (
            variant["feature_type"] == "somatic_variant"
            and variant["alternate_allele"] is None
            and feature == gene
            and protein_change is None
            # no slam-dunk catvar solution exists for defining specific exons as features --
            # see https://github.com/ga4gh/cat-vrs/discussions/161
            and variant["exon"] is None
        ):
            # it's a feature context constraint-based catvar
            normalized_gene, _ = self._normalize_moa_gene(feature)
            feature = f"{feature} Mutation"
            if normalized_gene:
                normalized_catvar = CategoricalVariant(
                    id=f"catvar:{feature}",
                    name=feature,
                    constraints=[
                        FeatureContextConstraint(featureContext=normalized_gene)
                    ],
                )
        elif "rearrangement_type" not in variant and protein_change and gene:
            # it's a defining allele constraint-based catvar
            query = f"{gene} {protein_change[2:]}"
            vrs_variation = await self.vicc_normalizers.normalize_variation(query)
            if not vrs_variation:
                _logger.debug(
                    "Variation Normalizer unable to normalize: moa.variant: %s using query: %s",
                    variant_id,
                    query,
                )
            else:
                moa_variation = Variation(**vrs_variation.model_dump(exclude_none=True))
                normalized_catvar = CategoricalVariant(
                    id=f"catvar:{vrs_variation.id}",
                    name=query,
                    constraints=[DefiningAlleleConstraint(allele=moa_variation.root)],
                )
        else:
            # it's some other unsupported stuff, don't try to normalize it
            _logger.debug(
                "Variation Normalizer does not support %s: %s",
                variant_id,
                feature,
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
        """Add extensions/members/mappings to MOA CatVar

        Todo:
        * should members be generated? They're created as normalized alleles, which
          feels philosophically out of step with the other changes here.

        :param variant: original MOA variant object
        :return: tuple with constructed Extensions, catvar members, and mappings

        """
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
        if locus := variant.get("locus"):
            extensions.append(Extension(name="MOA locus", value=locus))
        members = await self._get_variation_members(moa_rep_coord)
        mappings = []
        if rsid := variant.get("rsid"):
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        code=code(rsid),
                        system="https://www.ncbi.nlm.nih.gov/snp/",
                    ),
                    relation=Relation.RELATED_MATCH,
                )
            )
        return extensions, members, mappings

    async def _get_variation_members(self, moa_rep_coord: dict) -> list[Variation]:
        """Get members field for variation object. This is the related variant concepts.

        For now, only looks at genomic representative coordinate.

        :param moa_rep_coord: MOA Representative Coordinate
        :return: List containing a VRS variation record for associated genomic
            representation if variation-normalizer was able to successfully normalize
        """
        members = []
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
                vrs_genomic_variation.extensions = (
                    None  # don't care about capturing extensions for now
                )
                vrs_genomic_variation.name = gnomad_vcf
                members = [
                    Variation(**vrs_genomic_variation.model_dump(exclude_none=True))
                ]
            else:
                _logger.debug(
                    "Variation Normalizer unable to normalize genomic representation: %s",
                    gnomad_vcf,
                )
        else:
            _logger.debug(
                "Not enough information provided to create genomic representation: %s",
                moa_rep_coord,
            )

        return members

    def _normalize_combo_therapy(
        self, name: str
    ) -> tuple[Therapeutic | None, Therapeutic]:
        """Convert MOA combo therapy into GKS Therapeutic and also try to get normalized version

        :param name: name of therapy (should include a " + " in the middle)
        :param therapy_type: MOA therapy type (currently just used to check if combination)
        :return: tuple containing normalized concept (if successful) and original MOA concept
        """
        moa_drugs = [
            MappableConcept(
                id=f"moa.drug:{member.strip()}",
                conceptType="Drug",
                name=member.strip(),
            )
            for member in name.split("+")
        ]
        moa_combo_therapy = Therapeutic(
            root=TherapyGroup(
                membershipOperator=MembershipOperator.AND, therapies=moa_drugs
            )
        )
        normalized_drugs = []
        for moa_drug in moa_drugs:
            response, _ = self.vicc_normalizers.normalize_therapy(moa_drug.name)
            if response and response.therapy:
                response.therapy.extensions = None
                response.therapy.mappings = None
                normalized_drugs.append(response.therapy)
            else:
                normalized_drugs.append(None)
                break
        if all(normalized_drugs):
            normalized_combo_therapy = Therapeutic(
                root=TherapyGroup(
                    membershipOperator=MembershipOperator.AND,
                    therapies=normalized_drugs,
                )
            )
        else:
            normalized_combo_therapy = None
        return normalized_combo_therapy, moa_combo_therapy

    @cache  # noqa: B019
    def _normalize_moa_therapy(
        self, name: str, therapy_type: str
    ) -> tuple[Therapeutic | None, Therapeutic]:
        """Convert MOA Therapy into GKS Therapeutic and also try to get normalized version

        :param name: name of therapy (might be a combo of names)
        :param therapy_type: MOA therapy type (currently just used to check if combination)
        :return: tuple containing normalized concept (if successful) and original MOA concept
        """
        if not name:
            _logger.error(
                "Attempted to normalize empty therapeutic; wrong kind of assertion?"
            )
            raise ValueError

        # check for supported combo types. Skipping HORMONE and CHEMOTHERAPY for now
        if "+" in name and therapy_type.upper() in {
            "COMBINATION THERAPY",
            "IMMUNOTHERAPY",
            "RADIATION THERAPY",
            "TARGETED THERAPY",
        }:
            return self._normalize_combo_therapy(name)

        therapy = Therapeutic(
            root=MappableConcept(id=f"moa.drug:{name}", conceptType="Drug", name=name)
        )
        response, _ = self.vicc_normalizers.normalize_therapy(name)
        if response and response.therapy:
            response.therapy.extensions = []
            response.therapy.mappings = []
            normalized_therapy = Therapeutic(root=response.therapy)
        else:
            normalized_therapy = None
        return normalized_therapy, therapy

    def _build_document(self, source: dict) -> Document:
        """Convert GKS Document from MOA source object

        :param source: raw MOA source object
        :return: equivalent Document
        """
        source_id = source["id"]
        return Document(
            id=f"moa.source:{source_id}",
            title=source["citation"],
            urls=[source["url"]] if source["url"] else None,
            pmid=str(source["pmid"]) if source["pmid"] else None,
            doi=source["doi"] if source["doi"] else None,
            extensions=[Extension(name="source_type", value=source["type"])],
        )
