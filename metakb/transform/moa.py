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
from metakb.transform.base import Transform
from metakb.schemas.app import MethodId, MoaEvidenceLevel
from metakb.schemas.annotation import Document
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
        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param Optional[VICCNormalizers] normalizers: normalizer collection instance
        """
        super().__init__(data_dir=data_dir,
                         harvester_path=harvester_path,
                         normalizers=normalizers)
        # Able to normalize these IDs
        self.able_to_normalize = {
            "variations": {},
            "diseases": {},
            "therapeutics": {},
            "genes": {},
            "documents": {}
        }

        # Unable to normalize these IDs
        self.unable_to_normalize = {
            "diseases": set(),
            "therapeutics": set()
        }

    async def transform(self) -> None:
        """Transform MOA harvested JSON to common data model. Will store transformed
        results in instance variables.
        """
        data = self.extract_harvester()

        assertions = data["assertions"]
        sources = data["sources"]
        variants = data["variants"]
        genes = data["genes"]

        self._add_genes(genes)
        await self._add_variations(variants)
        self._add_documents(sources)

        # Transform MOA assertions
        await self._transform_assertions(assertions)

    async def _transform_assertions(self, assertions: List[Dict]) -> None:
        """Transform MOAlmanac assertions. Will add associated values to instance
        variables.

        :param: A list of MOA assertion records
        """
        for record in assertions:
            assertion_id = f"moa.assertion:{record['id']}"
            variant_id = record["variant"]["id"]
            variation_gene_map = self.able_to_normalize["variations"].get(variant_id)
            if not variation_gene_map:
                logger.debug(f"{assertion_id} has no variation for variant_id {variant_id}")
                continue

            therapy_name = record["therapy_name"]
            if not therapy_name:
                logger.debug(f"{assertion_id} has no therapy_name")
                continue

            if "+" in therapy_name:
                # Indicates multiple therapies
                continue
            else:
                moa_therapeutic = self._add_therapeutic(therapy_name)

            if not moa_therapeutic:
                logger.debug(f"{assertion_id} has no therapeutic agent for therapy_name {therapy_name}")
                continue

            moa_disease = self._add_disease(record["disease"])
            if not moa_disease:
                logger.debug(f"{assertion_id} has no disease for disease "
                             f"{record['disease']}")
                continue

            document = self.able_to_normalize["documents"].get(record["source_ids"])
            if document not in self.documents:
                self.documents.append(document)

            method = self.methods_mapping[MethodId.MOA_ASSERTION_BIORXIV.value]
            if method not in self.methods:
                self.methods.append(method)

            if record["clinical_significance"] == "resistance":
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_RESISTANCE_TO
            elif record["clinical_significance"] == "sensitivity":
                predicate = VariantTherapeuticResponseStudyPredicate.PREDICTS_SENSITIVITY_TO
            else:
                logger.debug(f"clinical_significance not supported: {record['clinical_significance']}")
                continue

            predictive_implication = record["predictive_implication"].strip().replace(" ", "_").replace("-", "_").upper()  # noqa: E501
            moa_evidence_level = MoaEvidenceLevel[predictive_implication]
            strength = self.evidence_level_vicc_concept_mapping[moa_evidence_level]

            gene = variation_gene_map["moa_gene"]
            qualifiers = self._get_qualifiers(record["variant"]["feature_type"], gene)

            statement = VariantTherapeuticResponseStudy(
                id=assertion_id,
                description=record["description"],
                strength=strength,
                predicate=predicate,
                variant=variation_gene_map["psc"],
                therapeutic=moa_therapeutic,
                tumorType=moa_disease,
                qualifiers=qualifiers,
                specifiedBy=method,
                isReportedIn=[document]
            ).model_dump(exclude_none=True)
            self.statements.append(statement)

    def _get_qualifiers(
        self, feature_type: str, gene: str
    ) -> Optional[VariantOncogenicityStudyQualifier]:
        """Get qualifiers for a Statement

        :param feature_type: MOA feature type
        :param gene: Gene name
        :return: VariantOncogenicityStudyQualifier for a Statement
        """
        if feature_type == "somatic_variant":
            allele_origin = AlleleOrigin.SOMATIC
        elif feature_type == "germline_variant":
            allele_origin = AlleleOrigin.GERMLINE
        else:
            allele_origin = None

        if allele_origin or gene:
            qualifiers = VariantOncogenicityStudyQualifier(
                alleleOrigin=allele_origin,
                geneContext=gene
            )
        else:
            qualifiers = None
        return qualifiers

    async def _add_variations(self, variants: List[Dict]) -> None:
        """Add variations to instance variables `able_to_normalize['variations']` and
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

            vrs_variation = None
            # For now, the normalizer only support a.a substitution
            if variant.get("protein_change"):
                gene = moa_gene["label"]
                query = f"{gene} {variant['protein_change'][2:]}"
                vrs_variation = await self.vicc_normalizers.normalize_variation([query])

                if not vrs_variation:
                    logger.debug(f"Variation Normalizer unable to normalize: "
                                   f"moa.variant:{variant_id} using query: {query}")
                    continue
            else:
                logger.debug(f"Variation Normalizer does not support "
                               f"{moa_variant_id}: {feature}")
                continue

            params = vrs_variation.model_dump(exclude_none=True)
            moa_variant_id = f"moa.variant:{variant_id}"
            params["id"] = vrs_variation.id
            params["digest"] = vrs_variation.id.split(".")[-1]
            moa_variation = models.Variation(**params)

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
        """Add genes to instance variables `able_to_normalize['genes']` and `genes`, if
        the gene-normalizer can successfully normalize the gene

        :param List[Dict] genes: All genes in MOAlmanac
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
        """Add documents to instance variable. Will also cache valid documents to
        `self.able_to_normalize["documents"]`

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

    def _add_therapeutic(self, label: str) -> Optional[Dict]:
        """Get Therapeutic Agent given a therapy name. Will add `label` to
        valid or invalid cache if able to return therapeutic agent or not. Will
        add valid therapeutics to instance variable.

        :param str label: Therapy name to get therapeutic for
        :return: Therapeutic Agent represented as a dict
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
        """Return a therapeutic agent for a given `label`

        :param label: Therapy name to get therapeutic agent for
        :return: If able to normalize therapy, returns therapeutic agent represented as
            a dict. Otherwise, `None`
        """
        if not label:
            return None

        therapy_norm_resp, normalized_therapeutic_id = \
            self.vicc_normalizers.normalize_therapy([label])

        if not normalized_therapeutic_id:
            logger.debug(f"Therapy Normalizer unable to normalize: {label}")
            return None
        else:
            extensions = [
                core_models.Extension(
                    name="therapy_normalizer_id",
                    value=normalized_therapeutic_id
                )
            ]

            regulatory_approval_extension = \
                self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)  # noqa: E501

            if regulatory_approval_extension:
                extensions.append(regulatory_approval_extension)

            return core_models.TherapeuticAgent(
                id=f"moa.{therapy_norm_resp.therapeutic_agent.id}",
                label=label,
                extensions=extensions
            ).model_dump(exclude_none=True)

    def _add_disease(self, disease: Dict) -> Optional[Dict]:
        """Get Disease given disease. Will add `disease_id`
        (generated digest) to valid or invalid cache if able to return disease or not.
        Will add valid disease to instance variable.

        :param disease: MOA Disease
        :return: If able to normalize, disease represented as a dict. Otherwise, `None`
        """
        if not all(value for value in disease.values()):
            return None

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
        """Return a Disease

        :param disease: an MOA disease record
        :return: If able to normalize, disease represented as a dict. Otherwise, `None`
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
