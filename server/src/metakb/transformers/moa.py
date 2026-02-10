"""A module to convert MOA resources to common data model"""

import logging
from functools import cache
from pathlib import Path

from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.aac_2017 import (
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Condition,
    Direction,
    Document,
    MembershipOperator,
    Method,
    PrognosticPredicate,
    Statement,
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

MOA_METHOD = Method(
    id=MethodId.MOA_ASSERTION_BIORXIV,
    name="MOAlmanac (2021)",
    reportedIn=Document(
        name="Reardon, B., Moore, N.D., Moore, N.S. et al.",
        title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
        doi="10.1038/s43018-021-00243-3",
        pmid="35121878",
    ),
)


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

        For each statement:
        * Build its base GKS equivalent
        * Try to normalize variant, disease, gene(, drug)
        * If they all normalize, also build the aggregate statement, supported by
          an evidence line to the base statement

        :param harvested_data: MOA harvested data
        """
        sources_map = {
            source["id"]: self._build_document(source)
            for source in harvested_data.sources
        }
        statements: list[Statement] = []
        aggregated_statements: list[Statement] = []
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
                    assertion, source
                )
            else:
                aggregated_statement, statement = await self._build_prog_statement(
                    assertion, source
                )
            statements.append(statement)
            if aggregated_statement:
                aggregated_statements.append(aggregated_statement)
        self.processed_data = TransformedData(
            statements=[s.id for s in statements + aggregated_statements]
        )

    async def _build_prog_statement(
        self,
        assertion: dict,
        source: Document,
    ) -> tuple[VariantPrognosticStudyStatement | None, Statement]:
        """Construct a prognostic statement and an aggregate parent assertion, if possible

        :param assertion: MOA assertion object (un-transformed)
        :param source: document from which MOA curated the statement
        :return: either an aggregate statement or None, and the MOA assertion modeled as
            a GKS statement
        """
        if moa_gene_value := assertion["variant"].get("gene"):
            gene = MappableConcept(id=f"moa.gene:{moa_gene_value}", name=moa_gene_value)
        else:
            gene = None
        disease = self._build_moa_disease(
            assertion["disease"]["name"],
            assertion["disease"]["oncotree_code"],
            assertion["disease"]["oncotree_term"],
        )
        variant = self._build_moa_variant(assertion["variant"])
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
            specifiedBy=MOA_METHOD,
        )
        aggregated_statement = await self._build_aggregated_prog_statement(statement)
        return aggregated_statement, statement

    async def _build_tr_statement(
        self,
        assertion: dict,
        source: Document,
    ) -> tuple[VariantTherapeuticResponseStudyStatement | None, Statement]:
        """Construct a therapeutic response statement and an aggregate parent assertion, if possible.

        :param assertion: MOA assertion object (un-transformed)
        :param source: document from which MOA curated the statement
        :return: either an aggregate statement or None, and the MOA assertion modeled as
            a GKS statement
        """
        if moa_gene_value := assertion["variant"].get("gene"):
            gene = MappableConcept(id=f"moa.gene:{moa_gene_value}", name=moa_gene_value)
        else:
            gene = None
        disease = self._build_moa_disease(
            assertion["disease"]["name"],
            assertion["disease"]["oncotree_code"],
            assertion["disease"]["oncotree_term"],
        )
        variant = self._build_moa_variant(assertion["variant"])
        therapy = assertion["therapy"]
        moa_therapy = self._build_moa_therapy(therapy["name"], therapy["type"])
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
            specifiedBy=MOA_METHOD,
        )
        aggregated_statement = await self._build_aggregated_tr_statement(statement)
        return aggregated_statement, statement

    def _build_moa_disease(
        self, name: str, oncotree_code: str | None, oncotree_term: str | None
    ) -> Condition:
        disease_id = f"moa.disease:{name}"
        if oncotree_code:
            mappings = [
                (
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
            ]
        else:
            mappings = None
        if oncotree_term and name != oncotree_term:
            extensions = [Extension(name="aliases", value=["oncotree_term"])]
        else:
            extensions = None
        return Condition(
            MappableConcept(
                id=disease_id,
                conceptType="Disease",
                name=name,
                mappings=mappings,
                extensions=extensions,
            )
        )

    @cache  # noqa: B019
    def _build_moa_variant(self, variant: dict) -> CategoricalVariant:
        """Transform MOA variant to CatVar

        TODO: some open questions here about how much to build out --
        * should we make a basic gene mappableconcept as the constraint for the feature catvar?

        :param variant: entire MOA variant object. The object keys are sort of unreliable
            so we just pass through the whole thing and work it out within the method
        :return: original MOA variant as a text catvar
        """
        variant_id = f"moa.variant:{variant['id']}"
        feature_name = variant["feature"]
        gene = variant.get("gene") or variant.get("gene1")
        protein_change = variant.get("protein_change")

        if variant.get("gene2"):
            # it's a fusion
            pass
        elif (
            variant["feature_type"] == "somatic_variant"
            and variant["alternate_allele"] is None
            and feature_name == gene
            and protein_change is None
            # no slam-dunk catvar solution exists for defining specific exons as features --
            # see https://github.com/ga4gh/cat-vrs/discussions/161
            and variant["exon"] is None
        ):
            # it's a feature context constraint-based catvar
            feature = f"{feature_name} Mutation"
        elif "rearrangement_type" not in variant and protein_change and gene:
            # it's a defining allele constraint-based catvar
            pass
        else:
            # it's some other unsupported stuff
            _logger.debug(
                "Variation Normalizer does not support %s: %s",
                variant_id,
                feature_name,
            )

        extensions, mappings = self._get_variant_extras(variant)
        return CategoricalVariant(
            id=variant_id,
            name=feature_name,
            extensions=extensions,
            mappings=mappings,
        )

    def _get_variant_extras(
        self, variant: dict
    ) -> tuple[list[Extension], list[ConceptMapping]]:
        """Add extensions/members/mappings to MOA CatVar

        Todo:
        * should members be generated? They're created as normalized alleles, which
          feels philosophically out of step with the other changes here.
          (Figure out before merging)
          - removing this for now

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
        return extensions, mappings

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

    def _build_moa_combo_therapy(self, name: str, therapy_type: str) -> Therapeutic:
        """Convert MOA combo therapy into GKS Therapeutic

        :param name: name of therapy (should include a " + " in the middle)
        :param therapy_type: MOA therapy type value (probably reflective of combo therapy)
        :param therapy_type: MOA therapy type (currently just used to check if combination)
        :return: original MOA concept as GKS therapeutic
        """
        moa_drugs = [
            MappableConcept(
                id=f"moa.drug:{member.strip()}",
                conceptType="Drug",
                name=member.strip(),
            )
            for member in name.split("+")
        ]
        return Therapeutic(
            root=TherapyGroup(
                membershipOperator=MembershipOperator.AND,
                therapies=moa_drugs,
                extensions=[Extension(name="moa_therapy_type", value=therapy_type)],
            )
        )

    @cache  # noqa: B019
    def _build_moa_therapy(self, name: str, therapy_type: str) -> Therapeutic:
        """Convert MOA Therapy into GKS Therapeutic

        :param name: name of therapy (might be a combo of names)
        :param therapy_type: MOA therapy type (currently just used to check if combination)
        :return: original MOA concept as GKS therapeutic
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
            return self._build_moa_combo_therapy(name, therapy_type)

        extensions = None
        if therapy_type:
            extensions = [Extension(name="moa_therapy_type", value=therapy_type)]
        return Therapeutic(
            root=MappableConcept(
                id=f"moa.drug:{name}",
                conceptType="Drug",
                name=name,
                extensions=extensions,
            )
        )

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
            doi=source["doi"] or None,
            extensions=[Extension(name="source_type", value=source["type"])],
        )
