"""A module for to transform CIViC."""
import logging
import re
from enum import Enum
from pathlib import Path

from ga4gh.core._internal.models import (
    Coding,
    Disease,
    Extension,
    Gene,
    Mapping,
    Relation,
    TherapeuticAgent,
    TherapeuticSubstituteGroup,
)
from ga4gh.vrs import models
from ga4gh.vrs._internal.models import Variation
from pydantic import BaseModel, ValidationError

from metakb import APP_ROOT
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Direction, Document
from metakb.schemas.categorical_variation import ProteinSequenceConsequence
from metakb.schemas.variation_statement import (
    AlleleOrigin,
    VariantTherapeuticResponseStudy,
    VariantTherapeuticResponseStudyPredicate,
    _VariantOncogenicityStudyQualifier,
)
from metakb.transform.base import (
    CivicEvidenceLevel,
    MethodId,
    TherapeuticProcedureType,
    Transform,
)

_logger = logging.getLogger(__name__)

# SNP pattern
SNP_RE = re.compile(r"RS\d+")

# Variant names that are known to not be supported in the variation-normalizer
UNABLE_TO_NORMALIZE_VAR_NAMES = {
    "mutation",
    "exon",
    "overexpression",
    "frameshift",
    "promoter",
    "deletion",
    "type",
    "insertion",
    "expression",
    "duplication",
    "copy",
    "underexpression",
    "number",
    "variation",
    "repeat",
    "rearrangement",
    "activation",
    "mislocalization",
    "translocation",
    "wild",
    "polymorphism",
    "frame",
    "shift",
    "loss",
    "function",
    "levels",
    "inactivation",
    "snp",
    "fusion",
    "dup",
    "truncation",
    "homozygosity",
    "gain",
    "phosphorylation",
}


class _VariationCache(BaseModel):
    """Create model for caching CIViC Variation data that will be accessed when
    transforming MP data
    """

    vrs_variation: dict
    civic_gene_id: str
    variant_types: list[Coding] | None = None
    mappings: list[Mapping] | None = None
    aliases: list[str] | None = None
    coordinates: dict | None
    members: list[Variation] | None = None


class SourcePrefix(str, Enum):
    """Define constraints for source prefixes."""

    PUBMED = "PUBMED"
    ASCO = "ASCO"
    ASH = "ASH"


class CivicTransform(Transform):
    """A class for transforming CIViC to the common data model."""

    def __init__(
        self,
        data_dir: Path = APP_ROOT / "data",
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize CIViC Transform class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested CIViC data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        # Method will always be the same
        self.methods = [self.methods_mapping[MethodId.CIVIC_EID_SOP.value]]
        self.able_to_normalize = {
            "variations": {},  # will store _VariationCache data
            "molecular_profiles": {},
            "diseases": {},
            "therapeutics": {},
            "genes": {},
        }

    @staticmethod
    def _mp_to_variant_mapping(molecular_profiles: list[dict]) -> tuple[list, dict]:
        """Get mapping from Molecular Profile ID to Variant ID.
        We currently do not handle complex molecular profiles (> 1 variant associated).

        :param molecular_profiles: List of civic molecular profiles represented as
            dictionaries
        :return: Tuple containing list of supported molecular profiles and mapping from
            Molecular Profile ID to Variant ID {mp_id: v_id}
        """
        mp_id_to_v_id: dict = {}
        supported_mps = []
        not_supported_mp_ids = set()
        for mp in molecular_profiles:
            mp_id = mp["id"]
            mp_variant_ids = mp["variant_ids"]
            if len(mp_variant_ids) != 1:
                mp_id_to_v_id[mp_id] = None
                not_supported_mp_ids.add(mp_id)
            else:
                supported_mps.append(mp)
                mp_id_to_v_id[mp_id] = mp_variant_ids[0]

        _logger.debug(
            "%s Molecular Profiles not supported: %s",
            len(not_supported_mp_ids),
            not_supported_mp_ids,
        )
        return supported_mps, mp_id_to_v_id

    async def transform(self) -> None:
        """Transform CIViC harvested json to common data model. Will store transformed
        results in instance variables.
        """
        data = self.extract_harvester()
        evidence_items = data["evidence"]

        # Get list of supported molecular profiles and mapping to variant id
        molecular_profiles, mp_id_to_v_id_mapping = self._mp_to_variant_mapping(
            data["molecular_profiles"]
        )

        # Only want evidence with approved status and predictive evidence type
        evidence_items = [
            e
            for e in evidence_items
            if e["status"] == "accepted" and e["evidence_type"].upper() == "PREDICTIVE"
        ]

        # Get all variant IDs from supported molecular profiles
        vids = {
            mp_id_to_v_id_mapping[e["molecular_profile_id"]]
            for e in evidence_items
            if e["molecular_profile_id"]
        }

        # Add variant (only supported) and gene (all) data
        # (mutates `variations` and `genes`)
        variants = data["variants"]
        variants = [v for v in variants if v["id"] in vids]
        await self._add_variations(variants)
        self._add_genes(data["genes"])

        # Only want to add MPs where variation-normalizer succeeded for the related
        # variant. Will update `molecular_profiles`
        able_to_normalize_vids = self.able_to_normalize["variations"].keys()
        mps = [
            mp
            for mp in molecular_profiles
            if f"civic.vid:{mp['variant_ids'][0]}" in able_to_normalize_vids
        ]
        self._add_protein_consequences(mps, mp_id_to_v_id_mapping)

        # Add variant therapeutic response study data. Will update `studies`
        self._add_variant_therapeutic_response_studies(
            evidence_items, mp_id_to_v_id_mapping
        )

    def _add_variant_therapeutic_response_studies(
        self, records: list[dict], mp_id_to_v_id_mapping: dict
    ) -> None:
        """Create Variant Therapeutic Response Studies from CIViC Evidence Items.
        Will add associated values to instance variables (`therapeutics`, `diseases`,
        and `documents`). `able_to_normalize` and `unable_to_normalize` will also be
        mutated for associated therapeutics and diseases.

        :param records: List of CIViC Evidence Items
        :param mp_id_to_v_id_mapping: Molecular Profile ID to Variant ID mapping
            {mp_id: v_id}
        """
        for r in records:
            # Check cache for molecular profile, variation and gene data
            mp_id = f"civic.mpid:{r['molecular_profile_id']}"
            mp = self.able_to_normalize["molecular_profiles"].get(mp_id)
            if not mp:
                _logger.debug("mp_id not supported: %s", mp_id)
                continue

            variant_id = f"civic.vid:{mp_id_to_v_id_mapping[r['molecular_profile_id']]}"
            variation_gene_map = self.able_to_normalize["variations"].get(variant_id)
            if not variation_gene_map:
                _logger.debug("variant_id not supported: %s", variant_id)
                continue

            # Get predicate
            predicate = self._get_predicate(r["evidence_type"], r["significance"])

            # Don't support TR that has  `None`, "N/A", or "Unknown" predicate
            if not predicate:
                continue

            # Add disease
            if not r["disease"]:
                continue

            civic_disease = self._add_disease(r["disease"])
            if not civic_disease:
                continue

            therapies = r["therapies"]
            if len(therapies) == 1:
                # Add TherapeuticAgent
                therapeutic_procedure_id = f"civic.tid:{therapies[0]['id']}"
                therapy_interaction_type = None
                therapeutic_procedure_type = TherapeuticProcedureType.THERAPEUTIC_AGENT
            else:
                # Add TherapeuticSubstituteGroup
                therapy_interaction_type = r["therapy_interaction_type"]
                therapeutic_ids = [f"civic.tid:{t['id']}" for t in therapies]
                therapeutic_digest = self._get_digest_for_str_lists(therapeutic_ids)

                if therapy_interaction_type == "SUBSTITUTES":
                    therapeutic_procedure_id = f"civic.tsgid:{therapeutic_digest}"
                    therapeutic_procedure_type = (
                        TherapeuticProcedureType.THERAPEUTIC_SUBSTITUTE_GROUP
                    )
                elif therapy_interaction_type == "COMBINATION":
                    therapeutic_procedure_id = f"civic.ctid:{therapeutic_digest}"
                    therapeutic_procedure_type = (
                        TherapeuticProcedureType.COMBINATION_THERAPY
                    )
                else:
                    _logger.debug(
                        "civic therapy_interaction_type not supported: %s",
                        therapy_interaction_type,
                    )
                    continue

            civic_therapeutic = self._add_therapeutic_procedure(
                therapeutic_procedure_id,
                therapies,
                therapeutic_procedure_type,
                therapy_interaction_type,
            )
            if not civic_therapeutic:
                continue

            # Add document
            document = self._add_eid_document(r["source"])
            if not document:
                continue

            # Get strength
            direction = self._get_evidence_direction(r["evidence_direction"])
            evidence_level = CivicEvidenceLevel[r["evidence_level"]]
            strength = self.evidence_level_to_vicc_concept_mapping[evidence_level]

            # Get qualifier
            civic_gene = self.able_to_normalize["genes"].get(
                variation_gene_map["civic_gene_id"]
            )
            qualifiers = self._get_variant_onco_study_qualifier(
                r["variant_origin"], civic_gene
            )

            _logger.debug("line 308")
            statement = VariantTherapeuticResponseStudy(
                id=r["name"].lower().replace("eid", "civic.eid:"),
                description=r["description"] if r["description"] else None,
                direction=direction,
                strength=strength,
                predicate=predicate,
                variant=mp,
                therapeutic=civic_therapeutic,
                tumorType=civic_disease,
                qualifiers=qualifiers,
                specifiedBy=self.methods[0],
                isReportedIn=[document],
            ).model_dump(exclude_none=True)
            self.studies.append(statement)

    def _get_variant_onco_study_qualifier(
        self, variant_origin: str, gene: Gene | None = None
    ) -> _VariantOncogenicityStudyQualifier | None:
        """Get Variant Oncogenicity Study Qualifier

        :param variant_origin: CIViC evidence item's variant origin
        :param gene: CIViC gene data
        :return: Variant Oncogenicity Study Qualifier for a Variant Therapeutic Response
            Study, if allele origin or gene exists
        """
        variant_origin = variant_origin.upper()
        if variant_origin == "SOMATIC":
            allele_origin = AlleleOrigin.SOMATIC
        elif variant_origin in {"RARE_GERMLINE", "COMMON_GERMLINE"}:
            allele_origin = AlleleOrigin.GERMLINE
        else:
            allele_origin = None

        if allele_origin or gene:
            qualifier = _VariantOncogenicityStudyQualifier(
                alleleOrigin=allele_origin, geneContext=gene
            )
        else:
            qualifier = None
        return qualifier

    def _get_evidence_direction(self, direction: str) -> Direction | None:
        """Get the normalized evidence direction

        :param direction: CIViC evidence item's direction
        :return: Normalized evidence direction
        """
        direction_upper = direction.upper()
        if direction_upper == "SUPPORTS":
            return Direction.SUPPORTS
        if direction_upper == "DOES_NOT_SUPPORT":
            return Direction.REFUTES
        return Direction.NONE

    def _get_predicate(
        self, record_type: str, clin_sig: str
    ) -> VariantTherapeuticResponseStudyPredicate | None:
        """Return predicate for an evidence item.

        :param record_type: The evidence type
        :param clin_sig: The evidence item's clinical significance
        :return: Predicate for proposition
        """
        predicate = None

        if record_type == "PREDICTIVE":
            if clin_sig == "SENSITIVITYRESPONSE":
                predicate = (
                    VariantTherapeuticResponseStudyPredicate.PREDICTS_SENSITIVITY_TO
                )
            elif clin_sig == "RESISTANCE":
                predicate = (
                    VariantTherapeuticResponseStudyPredicate.PREDICTS_RESISTANCE_TO
                )
        return predicate

    def _add_protein_consequences(
        self, molecular_profiles: list[dict], mp_id_to_v_id_mapping: dict
    ) -> None:
        """Create Protein Sequence Consequence objects for all supported MP records.
        Mutates instance variables `able_to_normalize['molecular_profiles']` and
        `molecular_profiles`.

        :param molecular_profiles: List of supported Molecular Profiles in CIViC.
            The associated, single variant record for each MP was successfully
            normalized
        :param mp_id_to_v_id_mapping: Mapping from Molecular Profile ID to Variant ID
            {mp_id: v_id}
        """
        for mp in molecular_profiles:
            mp_id = f"civic.mpid:{mp['id']}"
            vid = f"civic.vid:{mp_id_to_v_id_mapping[mp['id']]}"
            civic_variation_data = self.able_to_normalize["variations"][vid]

            # Only support Alleles for now
            if civic_variation_data["vrs_variation"]["type"] != "Allele":
                continue

            # Get aliases from MP and Variant record
            aliases = civic_variation_data["aliases"] or []
            for a in mp["aliases"] or []:
                if not SNP_RE.match(a):
                    aliases.append(a)

            # Get molecular profile score data
            mp_score = mp["molecular_profile_score"]
            if mp_score:
                extensions = [
                    Extension(name="CIViC Molecular Profile Score", value=mp_score)
                ]
            else:
                extensions = []

            # Get CIViC representative coordinate and Variant types data
            for ext_key, var_key in [
                ("CIViC representative coordinate", "coordinates"),
                ("Variant types", "variant_types"),
            ]:
                if civic_variation_data[var_key]:
                    extensions.append(
                        Extension(name=ext_key, value=civic_variation_data[var_key])
                    )

            _logger.debug("line 432")
            psc = ProteinSequenceConsequence(
                id=mp_id,
                description=mp["description"],
                label=mp["name"],
                definingContext=civic_variation_data["vrs_variation"],
                aliases=list(set(aliases)) or None,
                mappings=civic_variation_data["mappings"],
                extensions=extensions or None,
                members=civic_variation_data["members"],
            ).model_dump(exclude_none=True)
            self.molecular_profiles.append(psc)
            self.able_to_normalize["molecular_profiles"][mp_id] = psc

    @staticmethod
    def _get_variant_name(variant: dict) -> str:
        """Get variant name from CIViC Variant record.
        If 'c.' in name, use the cDNA name

        :param variant: CIViC Variant record
        :return: Variant name to use for query
        """
        if "c." in variant["name"]:
            variant_name = variant["name"]
            if "(" in variant_name:
                variant_name = variant_name.replace("(", "").replace(")", "")
            variant_name = variant_name.split()[-1]
        else:
            variant_name = variant["name"]
        return variant_name

    @staticmethod
    def _is_supported_variant_query(variant_name: str, variant_id: int) -> bool:
        """Determine if a variant name is supported by the variation-normalizer.
        This is used to skip normalization on variants that the variation-normalizer
        is known not to support

        :param variant_name: Variant name in CIViC
        :param variant_id: CIViC Variant ID
        :return: `True` if the variant_name is supported in the variation-normalizer.
            `False` otherwise
        """
        # Will remove as more get implemented in variation normalizer
        # Filtering to speed up transformation
        vname_lower = variant_name.lower()

        if vname_lower.endswith("fs") or "-" in vname_lower or "/" in vname_lower:
            _logger.debug(
                "Variation Normalizer does not support %s: %s", variant_id, variant_name
            )
            return False

        if set(vname_lower.split()) & UNABLE_TO_NORMALIZE_VAR_NAMES:
            _logger.debug(
                "Variation Normalizer does not support %s: %s", variant_id, variant_name
            )
            return False

        return True

    async def _get_variation_members(
        self, variant: dict
    ) -> list[models.Variation] | None:
        """Get members field for variation object. This is the related variant concepts.
        For now, we will only do genomic HGVS expressions

        :param variant: CIViC Variant record
        :return: List containing one VRS variation record for associated genomic HGVS
            expression, if variation-normalizer was able to normalize
        """
        members = None
        genomic_hgvs = (
            [expr for expr in variant["hgvs_expressions"] if "g." in expr] or [None]
        )[0]
        if genomic_hgvs:
            vrs_genomic_variation = await self.vicc_normalizers.normalize_variation(
                [genomic_hgvs]
            )

            if vrs_genomic_variation:
                _logger.debug("line 512")
                genomic_params = vrs_genomic_variation.model_dump(exclude_none=True)
                genomic_params["label"] = genomic_hgvs
                members = [models.Variation(**genomic_params)]
        return members

    async def _add_variations(self, variants: list[dict]) -> None:
        """Normalize supported CIViC variant records.
        Mutates instance variables `able_to_normalize['variations']` and `variations`,
        if the variation-normalizer can successfully normalize the variant

        :param variants: List of all CIViC variant records
        """
        for variant in variants:
            variant_id = f"civic.vid:{variant['id']}"
            variant_name = self._get_variant_name(variant)
            variant_query = f"{variant['entrez_name']} {variant_name}"

            if not self._is_supported_variant_query(variant_name, variant_id):
                continue

            vrs_variation = await self.vicc_normalizers.normalize_variation(
                [variant_query]
            )

            # Couldn't find normalized concept
            if not vrs_variation:
                _logger.debug(
                    "Variation Normalizer unable to normalize %s using query %s",
                    variant_id,
                    variant_query,
                )
                continue

            # Create VRS Variation object
            _logger.debug("line 547")
            params = vrs_variation.model_dump(exclude_none=True)
            params["label"] = variant["name"]
            civic_variation = models.Variation(**params)

            # Get expressions
            hgvs_exprs = self._get_expressions(variant)
            if hgvs_exprs:
                civic_variation.root.expressions = hgvs_exprs

            # Get members
            members = await self._get_variation_members(variant)

            # Get variant types
            variant_types_value = []
            for vt in variant["variant_types"]:
                variant_types_value.append(
                    Coding(
                        code=vt["so_id"],
                        system=f"{vt['url'].rsplit('/', 1)[0]}/",
                        label="_".join(vt["name"].lower().split()),
                    )
                )

            # Get mappings
            mappings = [
                Mapping(
                    coding=Coding(
                        code=str(variant["id"]),
                        system="https://civicdb.org/variants/",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            ]

            if variant["allele_registry_id"]:
                mappings.append(
                    Mapping(
                        coding=Coding(
                            code=variant["allele_registry_id"],
                            system="https://reg.clinicalgenome.org/",
                        ),
                        relation=Relation.RELATED_MATCH,
                    )
                )

            for ce in variant["clinvar_entries"]:
                mappings.append(
                    Mapping(
                        coding=Coding(
                            code=ce,
                            system="https://www.ncbi.nlm.nih.gov/clinvar/variation/",
                        ),
                        relation=Relation.RELATED_MATCH,
                    )
                )

            aliases = []
            for a in variant["variant_aliases"]:
                if SNP_RE.match(a):
                    a = a.lower()
                    mappings.append(
                        Mapping(
                            coding=Coding(
                                code=a,
                                system="https://www.ncbi.nlm.nih.gov/snp/",
                            ),
                            relation=Relation.RELATED_MATCH,
                        )
                    )
                else:
                    aliases.append(a)

            if variant["coordinates"]:
                coordinates = {
                    k: v for k, v in variant["coordinates"].items() if v is not None
                }
            else:
                coordinates = None

            _logger.debug("line 627")
            civic_variation_dict = civic_variation.model_dump(exclude_none=True)
            self.variations.append(civic_variation_dict)
            _logger.debug("line 630")
            self.able_to_normalize["variations"][variant_id] = _VariationCache(
                vrs_variation=civic_variation_dict,
                civic_gene_id=f"civic.gid:{variant['gene_id']}",
                variant_types=variant_types_value or None,
                mappings=mappings or None,
                aliases=aliases or None,
                coordinates=coordinates or None,
                members=members,
            ).model_dump()

    def _get_expressions(self, variant: dict) -> list[models.Expression]:
        """Get expressions for a given variant

        :param variant: A CIViC variant record
        :return: A list of expressions
        """
        expressions = []
        for hgvs_expr in variant["hgvs_expressions"]:
            if ":g." in hgvs_expr:
                syntax = models.Syntax.HGVS_G
            elif ":c." in hgvs_expr:
                syntax = models.Syntax.HGVS_C
            else:
                syntax = models.Syntax.HGVS_P

            if hgvs_expr != "N/A":
                expressions.append(models.Expression(syntax=syntax, value=hgvs_expr))
        return expressions

    def _add_genes(self, genes: list[dict]) -> None:
        """Create gene objects for all CIViC gene records.
        Mutates instance variables `able_to_normalize['genes']` and `genes`, if the
        gene-normalizer can successfully normalize the gene

        :param genes: All genes in CIViC
        """
        for gene in genes:
            gene_id = f"civic.gid:{gene['id']}"
            ncbigene = f"ncbigene:{gene['entrez_id']}"
            queries = [ncbigene, gene["name"]] + gene["aliases"]

            _, normalized_gene_id = self.vicc_normalizers.normalize_gene(queries)

            if normalized_gene_id:
                _logger.debug("line 18")
                civic_gene = Gene(
                    id=gene_id,
                    label=gene["name"],
                    description=gene["description"] if gene["description"] else None,
                    mappings=[
                        Mapping(
                            coding=Coding(
                                code=f"ncbigene:{gene['entrez_id']}",
                                system="https://www.ncbi.nlm.nih.gov/gene/",
                            ),
                            relation=Relation.EXACT_MATCH,
                        )
                    ],
                    aliases=gene["aliases"] if gene["aliases"] else None,
                    extensions=[
                        Extension(name="gene_normalizer_id", value=normalized_gene_id)
                    ],
                ).model_dump(exclude_none=True)
                self.able_to_normalize["genes"][gene_id] = civic_gene
                self.genes.append(civic_gene)
            else:
                _logger.debug(
                    "Gene Normalizer unable to normalize %s using queries: %s",
                    gene_id,
                    queries,
                )

    def _add_disease(self, disease: dict) -> Disease | None:
        """Create or get disease given CIViC disease.
        First looks in cache for existing disease, if not found will attempt to
        normalize. Will add CIViC disease ID to `diseases` and
        `able_to_normalize['diseases']` if disease-normalizer is able to normalize. Else
        will add the CIViC disease ID to `unable_to_normalize['disease']`

        :param disease: CIViC Disease object
        :return: Disease object if disease-normalizer was able to normalize
        """
        disease_id = f"civic.did:{disease['id']}"
        vrs_disease = self.able_to_normalize["diseases"].get(disease_id)
        if vrs_disease:
            return vrs_disease
        vrs_disease = None
        if disease_id not in self.unable_to_normalize["diseases"]:
            vrs_disease = self._get_disease(disease)
            if vrs_disease:
                self.able_to_normalize["diseases"][disease_id] = vrs_disease
                self.diseases.append(vrs_disease)
            else:
                self.unable_to_normalize["diseases"].add(disease_id)
        return vrs_disease

    def _get_disease(self, disease: dict) -> dict | None:
        """Get Disease object for a CIViC disease

        :param disease: CIViC disease record
        :return: If able to normalize, Disease represented as a dict. Otherwise, `None`
        """
        disease_id = f"civic.did:{disease['id']}"
        display_name = disease["display_name"]
        doid = disease["doid"]
        mappings = []

        if not doid:
            _logger.debug("%s (%s) has null DOID", disease_id, display_name)
            queries = [display_name]
        else:
            doid = f"DOID:{doid}"
            queries = [doid, display_name]
            mappings.append(
                Mapping(
                    coding=Coding(
                        code=doid,
                        system="https://www.disease-ontology.org/",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            )

        (
            disease_norm_resp,
            normalized_disease_id,
        ) = self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            _logger.debug(
                "Disease Normalizer unable to normalize: %s using queries %s",
                disease_id,
                queries,
            )
            return None

        _logger.debug("Line 767")
        return Disease(
            id=disease_id,
            label=display_name,
            mappings=mappings if mappings else None,
            extensions=[
                self._get_disease_normalizer_ext_data(
                    normalized_disease_id, disease_norm_resp
                ),
            ],
        ).model_dump(exclude_none=True)

    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
        therapy_interaction_type: str,
    ) -> TherapeuticSubstituteGroup | None:
        """Get Therapeutic Substitute Group for CIViC therapies

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies: List of CIViC therapy objects
        :param therapy_interaction_type: Therapy interaction type provided by CIViC
        :return: If able to normalize all therapy objects in `therapies`, returns
            Therapeutic Substitute Group represented as a dict
        """
        substitutes = []

        for therapy in therapies:
            therapeutic_procedure_id = f"civic.tid:{therapy['id']}"
            ta = self._add_therapeutic_procedure(
                therapeutic_procedure_id,
                [therapy],
                TherapeuticProcedureType.THERAPEUTIC_AGENT,
            )
            if not ta:
                return None

            substitutes.append(ta)

        _logger.debug("line 807")
        extensions = [
            Extension(
                name="civic_therapy_interaction_type", value=therapy_interaction_type
            ).model_dump(exclude_none=True)
        ]

        try:
            tsg = TherapeuticSubstituteGroup(
                id=therapeutic_sub_group_id,
                substitutes=substitutes,
                extensions=extensions,
            )
        except ValidationError as e:
            # If substitutes validation checks fail
            _logger.debug(
                "ValidationError raised when attempting to create TherapeuticSubstituteGroup: %s",
                {e},
            )
            tsg = None

        return tsg

    def _get_therapeutic_agent(self, therapy: dict) -> TherapeuticAgent | None:
        """Get Therapeutic Agent for CIViC therapy

        :param therapy: CIViC therapy object
        :return: If able to normalize therapy, returns therapeutic agent represented as
            a dict
        """
        therapy_id = f"civic.tid:{therapy['id']}"
        label = therapy["name"]
        ncit_id = therapy["ncit_id"]
        mappings = []
        if ncit_id:
            queries = [f"ncit:{ncit_id}", label]
            mappings.append(
                Mapping(
                    coding=Coding(
                        code=ncit_id,
                        system="https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            )
        else:
            queries = [label]

        (
            therapy_norm_resp,
            normalized_therapeutic_id,
        ) = self.vicc_normalizers.normalize_therapy(queries)

        if not normalized_therapeutic_id:
            _logger.debug(
                "Therapy Normalizer unable to normalize: using queries ncit:%s and %s",
                ncit_id,
                label,
            )
            return None

        regulatory_approval_extension = (
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)
        )

        extensions = [
            self._get_therapy_normalizer_ext_data(
                normalized_therapeutic_id, therapy_norm_resp
            ),
        ]

        if regulatory_approval_extension:
            extensions.append(regulatory_approval_extension)

        return TherapeuticAgent(
            id=therapy_id,
            label=label,
            mappings=mappings if mappings else None,
            aliases=therapy["aliases"] if therapy["aliases"] else None,
            extensions=extensions,
        )

    def _add_eid_document(self, source: dict) -> dict | None:
        """Create document object for CIViC source
        Mutates instance variable `documents`

        :param source: An evidence item's source
        :return: Document for Evidence Item if source type is supported
        """
        source_type = source["source_type"].upper()
        source_id = source["id"]
        if source_type in SourcePrefix.__members__:
            _logger.debug("Line 899")
            document = Document(
                id=f"civic.source:{source_id}",
                label=source["citation"],
                title=source["title"],
            ).model_dump(exclude_none=True)

            if source["source_type"] == SourcePrefix.PUBMED:
                document["pmid"] = int(source["citation_id"])

            if document not in self.documents:
                self.documents.append(document)
        else:
            _logger.warning(
                "Document, %s, not supported. %s not in SourcePrefix",
                source_id,
                source_type,
            )
            document = None

        return document
