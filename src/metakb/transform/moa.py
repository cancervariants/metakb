"""A module to convert MOA resources to common data model"""

import json
import logging
from pathlib import Path
from typing import ClassVar
from typing import Dict, List, Optional
from typing import ClassVar, Dict, List, Optional
from urllib.parse import quote

from ga4gh.core import sha512t24u
from ga4gh.core._internal.models import (
    Coding,
    Disease,
    Extension,
    Gene,
    Mapping,
    Relation,
    TherapeuticAgent,
)
from ga4gh.vrs import models

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
    MethodId,
    MoaEvidenceLevel,
    TherapeuticProcedureType,
    Transform,
)

logger = logging.getLogger(__name__)


class MoaTransform(Transform):
    """A class for transforming MOA resources to common data model."""

    def __init__(
        self,
        data_dir: Path = APP_ROOT / "data",
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize MOAlmanac Transform class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested MOA data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir, harvester_path=harvester_path, normalizers=normalizers
        )

        # Method will always be the same
        self.methods = [self.methods_mapping[MethodId.MOA_ASSERTION_BIORXIV.value]]
        self.able_to_normalize= {
            "variations": {},
            "diseases": {},
            "therapeutics": {},
            "genes": {},
            "documents": {},
        }

    async def transform(self) -> None:
        """Transform MOA harvested JSON to common data model. Will store transformed
        results in instance variables.
        """
        data = self.extract_harvester()

        # Add gene, variant, and source data to instance variables (`genes`,
        # `variations`, and `documents`)
        self._add_genes(data["genes"])
        await self._add_protein_consequences(data["variants"])
        self._add_documents(data["sources"])

        # Add variant therapeutic response study data. Will update `studies`
        await self._add_variant_therapeutic_response_studies(data["assertions"])

    async def _add_variant_therapeutic_response_studies(
        self, assertions: list[dict]
    ) -> None:
        """Create Variant Therapeutic Response Studies from MOA assertions.
        Will add associated values to instances variables (`therapeutics`, `diseases`,
        and `studies`). `able_to_normalize` and `unable_to_normalize` will also be
        mutated for associated therapeutics and diseases.

        :param assertions: A list of MOA assertion records
        """
        for record in assertions:
            assertion_id = f"moa.assertion:{record['id']}"
            variant_id = record["variant"]["id"]

            # Check cache for variation record (which contains gene information)
            variation_gene_map = self.able_to_normalize["variations"].get(variant_id)
            if not variation_gene_map:
                logger.debug(
                    "%s has no variation for variant_id %s", assertion_id, variant_id
                )
                continue

            # Get predicate. We only support therapeutic resistance/sensitivity
            if record["clinical_significance"] == "resistance":
                predicate = (
                    VariantTherapeuticResponseStudyPredicate.PREDICTS_RESISTANCE_TO
                )
            elif record["clinical_significance"] == "sensitivity":
                predicate = (
                    VariantTherapeuticResponseStudyPredicate.PREDICTS_SENSITIVITY_TO
                )
            else:
                logger.debug(
                    "clinical_significance not supported: %s",
                    record["clinical_significance"],
                )
                continue

            # Get strength
            predictive_implication = (
                record["predictive_implication"]
                .strip()
                .replace(" ", "_")
                .replace("-", "_")
                .upper()
            )
            moa_evidence_level = MoaEvidenceLevel[predictive_implication]
            strength = self.evidence_level_to_vicc_concept_mapping[moa_evidence_level]

            # Add therapeutic agent. We only support one therapy, so we will skip others
            therapy_name = record["therapy_name"]
            if not therapy_name:
                logger.debug("%s has no therapy_name", assertion_id)
                continue

            therapy_interaction_type = record["therapy_type"]

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
                    continue

                therapies = [{"label": tn.strip()} for tn in therapy_name.split("+")]
                therapeutic_digest = self._get_digest_for_str_lists(
                    [f"moa.therapy:{tn}" for tn in therapies]
                )
                therapeutic_procedure_id = f"moa.ctid:{therapeutic_digest}"
            else:
                therapeutic_procedure_id = f"moa.therapy:{therapy_name}"
                therapies = [{"label": therapy_name}]
                therapeutic_procedure_type = TherapeuticProcedureType.THERAPEUTIC_AGENT

            moa_therapeutic = self._add_therapeutic_procedure(
                therapeutic_procedure_id,
                therapies,
                therapeutic_procedure_type,
                therapy_interaction_type,
            )

            if not moa_therapeutic:
                logger.debug(
                    "%s has no therapeutic agent for therapy_name %s",
                    assertion_id,
                    therapy_name,
                )
                continue

            # Add disease
            moa_disease = self._add_disease(record["disease"])
            if not moa_disease:
                logger.debug(
                    "%s has no disease for disease %s", assertion_id, record["disease"]
                )
                continue

            # Add document
            document = self.able_to_normalize["documents"].get(record["source_ids"])

            # Get qualifier
            gene = variation_gene_map["moa_gene"]
            qualifiers = self._get_variant_onco_study_qualifier(
                record["variant"]["feature_type"], gene
            )

            statement = VariantTherapeuticResponseStudy(
                direction=Direction.NONE,
                id=assertion_id,
                description=record["description"],
                strength=strength,
                predicate=predicate,
                variant=variation_gene_map["psc"],
                therapeutic=moa_therapeutic,
                tumorType=moa_disease,
                qualifiers=qualifiers,
                specifiedBy=self.methods[0],
                isReportedIn=[document],
            ).model_dump(exclude_none=True)
            self.studies.append(statement)

    def _get_variant_onco_study_qualifier(
        self, feature_type: str, gene: Gene | None = None
    ) -> _VariantOncogenicityStudyQualifier | None:
        """Get Variant Oncogenicity Study Qualifier

        :param feature_type: MOA feature type
        :param gene: MOA gene data
        :return: Variant Oncogenicity Study Qualifier for a Variant Therapeutic Response
            Study, if allele origin or gene exists
        """
        if feature_type == "somatic_variant":
            allele_origin = AlleleOrigin.SOMATIC
        elif feature_type == "germline_variant":
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

    async def _add_protein_consequences(self, variants: list[dict]) -> None:
        """Create Protein Sequence Consequence objects for all MOA variant records.
        Mutates instance variables `able_to_normalize['variations']` and
        `variations`, if the variation-normalizer can successfully normalize the variant

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
                gene = moa_gene["label"]
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
            moa_variation = models.Variation(**params)

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
                Mapping(
                    coding=Coding(
                        code=str(variant_id),
                        system="https://moalmanac.org/api/features/",
                    ),
                    relation=Relation.EXACT_MATCH,
                )
            ]

            if variant["rsid"]:
                mappings.append(
                    Mapping(
                        coding=Coding(
                            code=variant["rsid"],
                            system="https://www.ncbi.nlm.nih.gov/snp/",
                        ),
                        relation=Relation.RELATED_MATCH,
                    )
                )

            psc = ProteinSequenceConsequence(
                id=moa_variant_id,
                label=feature,
                definingContext=moa_variation.root,
                mappings=mappings or None,
                extensions=extensions,
                members=members,
            ).model_dump(exclude_none=True)

            self.able_to_normalize["variations"][variant_id] = {
                "psc": psc,
                "moa_gene": moa_gene,
            }
            self.variations.append(psc)

    async def _get_variation_members(
        self, moa_rep_coord: dict
    ) -> list[models.Variation] | None:
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
                members = [models.Variation(**genomic_params)]
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
        Mutates instance variables `able_to_normalize['genes']` and `genes`, if
        the gene-normalizer can successfully normalize the gene

        :param genes: All genes in MOAlmanac
        """
        for gene in genes:
            _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
            if normalized_gene_id:
                moa_gene = Gene(
                    id=f"moa.normalize.gene:{quote(gene)}",
                    label=gene,
                    extensions=[
                        Extension(name="gene_normalizer_id", value=normalized_gene_id)
                    ],
                ).model_dump(exclude_none=True)
                self.able_to_normalize["genes"][quote(gene)] = moa_gene
                self.genes.append(moa_gene)
            else:
                logger.debug("Gene Normalizer unable to normalize: %s", gene)

    def _add_documents(self, sources: list) -> None:
        """Create document objects for all MOA sources.
        Mutates instance variables `documents` and `self.able_to_normalize["documents"]`

        :param sources: All sources in MOA
        """
        for source in sources:
            source_id = source["id"]

            if source["nct"]:
                mappings = [
                    Mapping(
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
                url=source["url"] if source["url"] else None,
                pmid=source["pmid"] if source["pmid"] else None,
                doi=source["doi"] if source["doi"] else None,
                mappings=mappings,
                extensions=[Extension(name="source_type", value=source["type"])],
            ).model_dump(exclude_none=True)
            self.able_to_normalize["documents"][source_id] = document
            self.documents.append(document)

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
        :return: If able to normalize therapy, returns therapeutic agent represented as
            a dict
        """
        (
            therapy_norm_resp,
            normalized_therapeutic_id,
        ) = self.vicc_normalizers.normalize_therapy([therapy["label"]])

        if not normalized_therapeutic_id:
            logger.debug("Therapy Normalizer unable to normalize: %s", therapy)
            return None

        extensions = [
            self._get_therapy_normalizer_ext_data(
                normalized_therapeutic_id, therapy_norm_resp
            ),
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
        normalize. Will generate a digest from the original MOA disease object. This
        will be used as the key in the caches. Will add the generated digest to
        `diseases` and `able_to_normalize['diseases']` if disease-normalizer is able to
        normalize. Else will add the generated digest to
        `unable_to_normalize['disease']`

        :param disease: MOA disease object
        :return: Disease object if disease-normalizer was able to normalize
        """
        if not all(value for value in disease.values()):
            return None

        # Since MOA disease objects do not have an ID, we will create a digest from
        # the original MOA disease object
        disease_list = sorted([f"{k}:{v}" for k, v in disease.items() if v])
        blob = json.dumps(disease_list, separators=(",", ":"), sort_keys=True).encode(
            "ascii"
        )
        disease_id = sha512t24u(blob)

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
        """Get Disease object for a MOA disease

        :param disease: MOA disease record
        :return: If able to normalize, Disease represented as a dict. Otherwise, `None`
        """
        queries = []
        mappings = []

        ot_code = disease["oncotree_code"]
        ot_term = disease["oncotree_term"]
        if ot_code:
            mappings.append(
                Mapping(
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
                self._get_disease_normalizer_ext_data(
                    normalized_disease_id, disease_norm_resp
                ),
            ],
        ).model_dump(exclude_none=True)
