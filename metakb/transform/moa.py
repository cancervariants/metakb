"""A module to convert MOA resources to common data model"""
from pathlib import Path
from typing import Optional, List, Dict
import logging
from urllib.parse import quote
import json

from ga4gh.core import core_models, sha512t24u
from ga4gh.vrs import models

from metakb import APP_ROOT   # noqa: I202
from metakb.normalizers import VICCNormalizers
from metakb.transform.base import Transform, MethodId, MoaEvidenceLevel
from metakb.schemas.annotation import Document, Direction
from metakb.schemas.variation_statement import (
    AlleleOrigin,
    VariantTherapeuticResponseStudy,
    VariantTherapeuticResponseStudyPredicate,
    VariantOncogenicityStudyQualifier
)
from metakb.schemas.categorical_variation import ProteinSequenceConsequence

logger = logging.getLogger(__name__)


class MOATransform(Transform):
    """A class for transforming MOA resources to common data model."""

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[VICCNormalizers] = None) -> None:
        """Initialize MOAlmanac Transform class.

        :param data_dir: Path to source data directory
        :param harvester_path: Path to previously harvested MOA data
        :param normalizers: normalizer collection instance
        """
        super().__init__(
            data_dir=data_dir,
            harvester_path=harvester_path,
            normalizers=normalizers
        )

        # Method will always be the same
        self.methods = [self.methods_mapping[MethodId.MOA_ASSERTION_BIORXIV.value]]

        # Cache for normalized concepts. The key is the concept type and value is a
        # dictionary of mappings from MOA ID or label if no ID exists (key) to
        # transformed concept (value)
        self.able_to_normalize = {
            "variations": {},
            "diseases": {},
            "therapeutics": {},
            "genes": {},
            "documents": {}
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

        # Add variant therapeutic response study data
        await self._add_variant_therapeutic_response_studies(data["assertions"])

    async def _add_variant_therapeutic_response_studies(
        self,
        assertions: List[Dict]
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
                    f"{assertion_id} has no variation for variant_id {variant_id}"
                )
                continue

            # Get predicate. We only support therapeutic resistance/sensitivity
            if record["clinical_significance"] == "resistance":
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_RESISTANCE_TO  # noqa: E501
            elif record["clinical_significance"] == "sensitivity":
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_SENSITIVITY_TO  # noqa: E501
            else:
                logger.debug(
                    "clinical_significance not supported: "
                    f"{record['clinical_significance']}"
                )
                continue

            # Get strength
            predictive_implication = record["predictive_implication"].strip().replace(" ", "_").replace("-", "_").upper()  # noqa: E501
            moa_evidence_level = MoaEvidenceLevel[predictive_implication]
            strength = self.evidence_level_to_vicc_concept_mapping[moa_evidence_level]

            # Add therapeutic agent. We only support one therapy, so we will skip others
            therapy_name = record["therapy_name"]
            if not therapy_name:
                logger.debug(f"{assertion_id} has no therapy_name")
                continue

            if "+" in therapy_name:
                # Indicates multiple therapies (will be supported later)
                continue
            else:
                moa_therapeutic = self._add_therapeutic(therapy_name)

            if not moa_therapeutic:
                logger.debug(
                    f"{assertion_id} has no therapeutic agent for therapy_name "
                    f"{therapy_name}"
                )
                continue

            # Add disease
            moa_disease = self._add_disease(record["disease"])
            if not moa_disease:
                logger.debug(f"{assertion_id} has no disease for disease "
                             f"{record['disease']}")
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
                isReportedIn=[document]
            ).model_dump(exclude_none=True)
            self.studies.append(statement)

    def _get_variant_onco_study_qualifier(
        self, feature_type: str, gene: Optional[core_models.Gene] = None
    ) -> Optional[VariantOncogenicityStudyQualifier]:
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
            qualifier = VariantOncogenicityStudyQualifier(
                alleleOrigin=allele_origin,
                geneContext=gene
            )
        else:
            qualifier = None
        return qualifier

    async def _add_protein_consequences(self, variants: List[Dict]) -> None:
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
                logger.debug(f"Variation Normalizer does not support {moa_variant_id}:"
                             f" {feature}")
                continue

            # Gene is required to form query
            gene = variant.get("gene")
            if not gene:
                logger.debug(f"Variation Normalizer does not support {moa_variant_id}: "
                             f"{feature} (no gene provided)")
                continue

            moa_gene = self.able_to_normalize["genes"].get(quote(gene))
            if not moa_gene:
                logger.debug(f"moa.variant:{variant_id} has no gene for "
                             f"gene, {gene}")
                continue

            # Form query and run through variation-normalizer
            # For now, the normalizer only support amino acid substitution
            vrs_variation = None
            if variant.get("protein_change"):
                gene = moa_gene["label"]
                query = f"{gene} {variant['protein_change'][2:]}"
                vrs_variation = await self.vicc_normalizers.normalize_variation([query])

                if not vrs_variation:
                    logger.debug("Variation Normalizer unable to normalize: "
                                 f"moa.variant:{variant_id} using query: {query}")
                    continue
            else:
                logger.debug("Variation Normalizer does not support "
                             f"{moa_variant_id}: {feature}")
                continue

            # Create VRS Variation object
            params = vrs_variation.model_dump(exclude_none=True)
            moa_variant_id = f"moa.variant:{variant_id}"
            params["id"] = vrs_variation.id
            params["digest"] = vrs_variation.id.split(".")[-1]
            moa_variation = models.Variation(**params)

            # Add MOA representative coordinate data to extensions
            coordinates_keys = [
                "chromosome", "start_position", "end_position", "reference_allele",
                "alternate_allele", "cdna_change", "protein_change", "exon"
            ]
            extensions = [
                core_models.Extension(
                    name="MOA representative coordinate",
                    value={k: variant[k] for k in coordinates_keys}
                )
            ]

            # Add mappings data
            mappings = [
                core_models.Mapping(
                    coding=core_models.Coding(
                        code=str(variant_id),
                        system="https://moalmanac.org/api/features/",
                    ),
                    relation=core_models.Relation.EXACT_MATCH
                )
            ]

            if variant["rsid"]:
                mappings.append(core_models.Mapping(
                    coding=core_models.Coding(
                        code=variant["rsid"],
                        system="https://www.ncbi.nlm.nih.gov/snp/"
                    ),
                    relation=core_models.Relation.RELATED_MATCH
                ))

            psc = ProteinSequenceConsequence(
                id=moa_variant_id,
                label=feature,
                definingContext=moa_variation.root,
                mappings=mappings or None,
                extensions=extensions
            ).model_dump(exclude_none=True)

            self.able_to_normalize["variations"][variant_id] = {
                "psc": psc,
                "moa_gene": moa_gene
            }
            self.variations.append(psc)

    def _add_genes(self, genes: List[str]) -> None:
        """Create gene objects for all MOA gene records.
        Mutates instance variables `able_to_normalize['genes']` and `genes`, if
        the gene-normalizer can successfully normalize the gene

        :param genes: All genes in MOAlmanac
        """
        for gene in genes:
            _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
            if normalized_gene_id:
                moa_gene = core_models.Gene(
                    id=f"moa.normalize.gene:{quote(gene)}",
                    label=gene,
                    extensions=[core_models.Extension(
                        name="gene_normalizer_id",
                        value=normalized_gene_id
                    )]
                ).model_dump(exclude_none=True)
                self.able_to_normalize["genes"][quote(gene)] = moa_gene
                self.genes.append(moa_gene)
            else:
                logger.debug(f"Gene Normalizer unable to normalize: {gene}")

    def _add_documents(self, sources: List) -> None:
        """Create document objects for all MOA sources.
        Mutates instance variables `documents` and `self.able_to_normalize["documents"]`

        :param sources: All sources in MOA
        """
        for source in sources:
            source_id = source["id"]

            if source["nct"]:
                mappings = [
                    core_models.Mapping(
                        coding=core_models.Coding(
                            code=source["nct"],
                            system="https://clinicaltrials.gov/search?term="
                        ),
                        relation=core_models.Relation.EXACT_MATCH
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
                extensions=[core_models.Extension(
                    name="source_type", value=source["type"]
                )]
            ).model_dump(exclude_none=True)
            self.able_to_normalize["documents"][source_id] = document
            self.documents.append(document)

    def _add_therapeutic(self, label: str) -> Optional[Dict]:
        """Create or get Therapeutic Agent given a therapy name.
        First looks in cache for existing therapeutic agent, if not found will attempt
        to normalize. Will add `label` to `therapeutics` and
        `able_to_normalize['therapeutics']` if therapy-normalizer is able to normalize.
        Else will add `label` to `unable_to_normalize['therapeutics']`.

        :param label: MOA therapy name
        :return: Therapeutic Agent if therapy-normalizer was able to normalize `label`
        """
        vrs_therapeutic = self.able_to_normalize["therapeutics"].get(label)
        if vrs_therapeutic:
            return vrs_therapeutic
        else:
            vrs_therapeutic = None
            if label not in self.unable_to_normalize["therapeutics"]:
                vrs_therapeutic = self._get_therapeutic(label)
                if vrs_therapeutic:
                    self.able_to_normalize["therapeutics"][label] = vrs_therapeutic
                    self.therapeutics.append(vrs_therapeutic)
                else:
                    self.unable_to_normalize["therapeutics"].add(label)
        return vrs_therapeutic

    def _get_therapeutic(self, label: str) -> Optional[Dict]:
        """Get Therapeutic Agent for a MOA therapy name.
        Will run `label` through therapy-normalizer.

        :param label: MOA therapy name
        :return: If able to normalize therapy, returns therapeutic agent represented as
            a dict
        """
        therapy_norm_resp, normalized_therapeutic_id = \
            self.vicc_normalizers.normalize_therapy([label])

        if not normalized_therapeutic_id:
            logger.debug(f"Therapy Normalizer unable to normalize: {label}")
            return None

        extensions = [
            core_models.Extension(
                name="therapy_normalizer_id",
                value=normalized_therapeutic_id
            )
        ]

        regulatory_approval_extension = \
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)

        if regulatory_approval_extension:
            extensions.append(regulatory_approval_extension)

        return core_models.TherapeuticAgent(
            id=f"moa.{therapy_norm_resp.therapeutic_agent.id}",
            label=label,
            extensions=extensions
        ).model_dump(exclude_none=True)

    def _add_disease(self, disease: Dict) -> Optional[Dict]:
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
        blob = json.dumps(disease_list, separators=(",", ":")).encode("ascii")
        disease_id = sha512t24u(blob)

        vrs_disease = self.able_to_normalize["diseases"].get(disease_id)
        if vrs_disease:
            return vrs_disease
        else:
            vrs_disease = None
            if disease_id not in self.unable_to_normalize["diseases"]:
                vrs_disease = self._get_disease(disease)
                if vrs_disease:
                    self.able_to_normalize["diseases"][disease_id] = vrs_disease
                    self.diseases.append(vrs_disease)
                else:
                    self.unable_to_normalize["diseases"].add(disease_id)
            return vrs_disease

    def _get_disease(self, disease: Dict) -> Optional[Dict]:
        """Get core_models.Disease object for a MOA disease

        :param disease: MOA disease record
        :return: If able to normalize, core_models.Disease represented as a dict.
            Otherwise, `None`
        """
        queries = []
        mappings = []

        ot_code = disease["oncotree_code"]
        ot_term = disease["oncotree_term"]
        if ot_code:
            mappings.append(core_models.Mapping(
                coding=core_models.Coding(
                    code=ot_code,
                    system="https://oncotree.mskcc.org/",
                    label=ot_term
                ),
                relation=core_models.Relation.EXACT_MATCH
            ))
            queries.append(f"oncotree:{disease['oncotree_code']}")

        disease_name = disease["name"]
        if ot_term:
            queries.append(ot_term)

        if disease_name:
            queries.append(disease_name)

        disease_norm_resp, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.debug(f"Disease Normalizer unable to normalize: {queries}")
            return None

        return core_models.Disease(
            id=f"moa.{disease_norm_resp.disease.id}",
            label=disease_name,
            mappings=mappings if mappings else None,
            extensions=[
                core_models.Extension(
                    name="disease_normalizer_id",
                    value=normalized_disease_id
                )
            ]
        ).model_dump(exclude_none=True)
