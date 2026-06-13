"""A module to convert MOA resources to common data model"""

import json
import logging
import re
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
from ga4gh.vrs.models import Allele
from tqdm import tqdm

from metakb.schemas.data import MoaHarvestedData, TransformedData
from metakb.transformers import catvars as build_catvars
from metakb.transformers.base import Transformer
from metakb.transformers.identifiers import compute_combo_id
from metakb.transformers.methodology import (
    VICC_CODE_EXACT_MAPPING_INDEX,
    MoaEvidenceLevel,
    get_evidence_level_coding,
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

    async def transform(self, harvested_data_path: Path) -> TransformedData:
        """Transform MOA harvested JSON to common data model.

        Will store transformed results in ``processed_data`` instance variable.

        For each statement:
        * Build its base GKS equivalent
        * Try to normalize variant, disease, gene(, drug)
        * If they all normalize, also build the aggregate statement, supported by
          an evidence line to the base statement

        :param harvested_data_path: path to MOA harvested data
        """
        with harvested_data_path.open() as f:
            harvested_data = MoaHarvestedData(**json.load(f))
        docs_map = {}
        for source in harvested_data.sources:
            source_doc = self._create_document(source)
            docs_map[source["id"]] = source_doc

        statements: list[Statement] = []
        assertions: dict[str, Statement] = {}
        for ev_item in tqdm(harvested_data.assertions):
            source = docs_map[ev_item["source_id"]]
            transformed_statement = self._create_statement(ev_item, source)
            if not transformed_statement:
                _logger.warning(
                    "Unable to model MOA assertion %s as a GKS statement",
                    ev_item["id"],
                )
                continue
            statements.append(transformed_statement)

            await self._upsert_assertion_from_evidence(
                transformed_statement, assertions
            )
        return TransformedData(
            evidence=statements, assertions=list(assertions.values())
        )

    def _create_statement(self, assertion: dict, source: Document) -> Statement | None:
        """Create a GKS statement from a MOA assertion

        :param assertion:
        :param source:
        :return:
        """
        if moa_gene_value := assertion["variant"].get("gene"):
            gene = MappableConcept(id=f"moa.gene:{moa_gene_value}", name=moa_gene_value)
        else:
            gene = None
        disease = self._create_moa_disease(
            assertion["disease"]["name"],
            assertion["disease"]["oncotree_code"],
            assertion["disease"]["oncotree_term"],
        )
        variant = self._create_moa_variant(assertion["variant"])
        strength = self._create_study_strength(assertion)

        if assertion["variant"]["feature_type"] == "somatic_variant":
            allele_origin_qualifier = MappableConcept(name="somatic")
        elif assertion["variant"]["feature_type"] == "germline_variant":
            allele_origin_qualifier = MappableConcept(name="germline")
        else:
            allele_origin_qualifier = None

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
                return None
            assertion_therapy = assertion["therapy"]
            therapy = self._create_moa_therapy(
                assertion_therapy["name"], assertion_therapy["type"]
            )
            resistance, sensitivity = (
                assertion_therapy["resistance"],
                assertion_therapy["sensitivity"],
            )
            if resistance != "":  # can be either 0, 1, or ""
                predicate = TherapeuticResponsePredicate.RESISTANCE
                direction = Direction.SUPPORTS if resistance else Direction.DISPUTES
            else:
                predicate = TherapeuticResponsePredicate.SENSITIVITY
                direction = Direction.SUPPORTS if sensitivity else Direction.DISPUTES
            proposition = VariantTherapeuticResponseProposition(
                geneContextQualifier=gene,
                subjectVariant=variant,
                conditionQualifier=disease,
                objectTherapeutic=therapy,
                predicate=predicate,
                alleleOriginQualifier=allele_origin_qualifier,
            )
        else:
            if assertion["favorable_prognosis"]:
                predicate = PrognosticPredicate.BETTER_OUTCOME
                direction = Direction.SUPPORTS
            else:
                predicate = PrognosticPredicate.WORSE_OUTCOME
                direction = Direction.DISPUTES

            proposition = VariantPrognosticProposition(
                geneContextQualifier=gene,
                subjectVariant=variant,
                objectCondition=disease,
                predicate=predicate,
                alleleOriginQualifier=allele_origin_qualifier,
            )
        return Statement(
            id=f"moa.assertion:{assertion['id']}",
            description=assertion["description"],
            proposition=proposition,
            direction=direction,
            reportedIn=[source],
            specifiedBy=self._create_method(),
            strength=strength,
        )

    def _create_study_strength(self, assertion: dict) -> MappableConcept:
        """Get Strength classification for a MOA study

        :param assertion: original MOA assertion object
        :return:
        """
        predictive_implication = (
            assertion["predictive_implication"]
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
            .upper()
        )
        evidence_level = MoaEvidenceLevel[predictive_implication]
        vicc_code = VICC_CODE_EXACT_MAPPING_INDEX[evidence_level]
        return MappableConcept(
            id=f"moa.strength:{evidence_level.value}",
            primaryCoding=get_evidence_level_coding(evidence_level),
            extensions=[
                Extension(
                    name="metakb_display_value",
                    value=vicc_code.display_value,
                )
            ],
        )

    def _create_moa_disease(
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
            extensions = [Extension(name="aliases", value=[oncotree_term])]
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

    def _create_moa_variant(self, variant: dict) -> CategoricalVariant:
        """Transform MOA variant to CatVar

        TODO: some open questions here about how much to build out --
        * should we make a basic gene mappableconcept as the constraint for the feature catvar?
        * use extensions to bring in more info on a per-variant-type basis (e.g. for tougher constraints)

        :param variant: entire MOA variant object. The object keys are sort of unreliable
            so we just pass through the whole thing and work it out within the method
        :return: original MOA variant as a text catvar
        """
        variant_id = f"moa.variant:{variant['id']}"
        moa_feature_name = variant["feature"]
        moa_primary_gene = variant.get("gene") or variant.get("gene1")
        protein_change = variant.get("protein_change")

        if variant.get("gene2"):
            # it's a fusion!
            # once we know how to normalize them, we may want to bring in some
            # fusion-specific variant attributes as Extensions to help inform
            # reconstruction of the adjacency constraint(s)
            _logger.debug(
                "Unsupported MOA fusion variant ID %s: %s",
                variant_id,
                variant,
            )
            name = moa_feature_name
        elif (
            variant["feature_type"] == "somatic_variant"
            and variant["alternate_allele"] is None
            and moa_feature_name == moa_primary_gene
            and protein_change is None
            # no slam-dunk catvar solution exists for defining specific exons as features --
            # see https://github.com/ga4gh/cat-vrs/discussions/161
            and variant["exon"] is None
        ):
            # it's a feature context constraint-based catvar!
            # for now, just use the "<gene name> Mutation" pattern
            name = f"{moa_feature_name} Mutation"
        elif (
            "rearrangement_type" not in variant and protein_change and moa_primary_gene
        ):
            # it's a defining allele constraint-based catvar!
            name = f"{moa_primary_gene} {protein_change[2:]}"
        else:
            # it's some other unsupported stuff. Log it and circle back later
            name = moa_feature_name
            _logger.debug(
                "Unsupported MOA variant ID %s: %s",
                variant_id,
                moa_feature_name,
            )

        extensions, mappings = self._get_variant_extras(variant)
        return CategoricalVariant(
            id=variant_id,
            name=name,
            extensions=extensions,
            mappings=mappings or None,
        )

    def _get_variant_extras(
        self, variant: dict
    ) -> tuple[list[Extension], list[ConceptMapping]]:
        """Add extensions/mappings to MOA CatVar

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
                Extension(name="moa_representative_coordinate", value=moa_rep_coord)
            )
        if locus := variant.get("locus"):
            extensions.append(Extension(name="moa_locus", value=locus))
        mappings = []
        if rsid := variant.get("rsid"):
            mappings.append(
                ConceptMapping(
                    coding=Coding(
                        id=f"dbsnp:{rsid}",
                        code=code(rsid),
                        system="https://www.ncbi.nlm.nih.gov/snp/",
                    ),
                    relation=Relation.RELATED_MATCH,
                )
            )
        if feature_type := variant.get("feature_type"):
            extensions.append(Extension(name="moa_feature_type", value=feature_type))
        if annotation := variant.get("variant_annotation"):
            extensions.append(
                Extension(name="moa_variant_annotation", value=annotation)
            )
        return extensions, mappings

    def _create_moa_combo_therapy(self, name: str, therapy_type: str) -> Therapeutic:
        """Convert MOA combo therapy into GKS Therapeutic

        :param name: name of therapy (should include a " + " in the middle)
        :param therapy_type: MOA therapy type value (probably reflective of combo therapy)
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
        operator = MembershipOperator.AND
        return Therapeutic(
            root=TherapyGroup(
                id=compute_combo_id(
                    self.src_data_store.src_name,
                    TherapyGroup,
                    operator,
                    [d.id for d in moa_drugs],
                ),
                membershipOperator=operator,
                therapies=moa_drugs,
                extensions=[Extension(name="moa_therapy_type", value=therapy_type)],
            )
        )

    def _create_moa_therapy(self, name: str, therapy_type: str) -> Therapeutic:
        """Convert MOA Therapy into GKS Therapeutic

        :param name: name of therapy (might be a combo of names)
        :param therapy_type: MOA therapy type (currently just used to check if combination)
        :return: original MOA concept as GKS therapeutic
        :raise ValueError: if therapy name is empty (probably indicates misclassification
            of the MOA assertion)
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
            return self._create_moa_combo_therapy(name, therapy_type)

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

    def _create_document(self, source: dict) -> Document:
        """Create document object for MOA source

        Mutates instance variable ``processed_data.documents``

        :param sources: All sources in MOA
        """
        return Document(
            id=f"moa.source:{source['id']}",
            title=source["citation"],
            urls=[source["url"]] if source["url"] else None,
            pmid=str(source["pmid"]) if source["pmid"] else None,
            doi=source["doi"] or None,
            extensions=[Extension(name="source_type", value=source["type"])],
        )

    async def _normalize_variant(
        self, variant: CategoricalVariant
    ) -> CategoricalVariant | None:
        queries = [variant.name]
        result = None
        for query in queries:
            if match := re.match(r"(.*) (Mutation|MUTATION)", query):
                gene_name = match.groups()[0]
                normalized_gene = self._normalize_gene(MappableConcept(name=gene_name))
                if normalized_gene:
                    return build_catvars.build_featurecontext_catvar(normalized_gene)
            result = await self.vicc_normalizers.normalize_variation(query)
            if result and isinstance(result, Allele):
                return build_catvars.build_proteinsequenceconsequence_catvar(
                    self.vicc_normalizers.seqrepo_access,
                    self.vicc_normalizers.transcript_mappings,
                    result,
                )
        _logger.debug(
            "Failed to normalize variant: %s", variant.model_dump(exclude_none=True)
        )
        return None
