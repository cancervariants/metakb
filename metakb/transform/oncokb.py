"""A module for transforming OncoKB to common data model (CDM)"""
from typing import Optional, Dict, List
from pathlib import Path
from urllib.parse import quote
from copy import deepcopy
import logging

from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, \
    Extension, GeneDescriptor, ValueObjectDescriptor

from metakb import APP_ROOT
from metakb.normalizers import VICCNormalizers
from metakb.transform.base import Transform
from metakb.schemas import Date, DiagnosticPredicate, Document, Method, MethodID, \
    Predicate, PredictivePredicate, PropositionType, Statement


logger = logging.getLogger("metakb.transform.oncokb")
logger.setLevel(logging.DEBUG)


# OncoKB gene fields (oncokb_label, ext_label)
GENE_EXT_CONVERSIONS = [
    ("grch37Isoform", "ensembl_transcript_GRCh37"),
    ("grch37RefSeq", "refseq_transcript_GRCh37"),
    ("grch38Isoform", "ensembl_transcript_GRCh38"),
    ("grch38RefSeq", "refseq_transcript_GRCh38"),
    ("oncogene", "oncogene"),
    ("highestSensitiveLevel", "oncokb_highest_sensitive_level"),
    ("highestResistanceLevel", "oncokb_highest_resistance_level"),
    ("background", "oncokb_background"),
    ("tsg", "tumor_suppressor_gene")
]


# OncoKB variation fields (oncokb_label, ext_label)
VARIATION_EXT_CONVERSIONS = [
    ("oncogenic", "oncogenic"),
    ("mutationEffect", "mutation_effect"),
    ("hotspot", "hotspot"),
    ("vus", "vus"),
    ("highestSensitiveLevel", "oncokb_highest_sensitive_level"),
    ("highestResistanceLevel", "oncokb_highest_resistance_level"),
    ("highestDiagnosticImplicationLevel", "oncokb_highest_diagnostic_implication_level"),  # noqa: E501
    ("highestPrognosticImplicationLevel", "oncokb_highest_prognostic_implication_level"),  # noqa: E501
    ("highestFdaLevel", "oncokb_highest_fda_level"),
    ("alleleExist", "allele_exist")
]


# OncoKB disease fields (oncokb_label, ext_label)
DISEASE_EXT_CONVERSIONS = [
    ("mainType", "oncotree_main_type"),
    ("tissue", "tissue"),
    ("children", "children"),
    ("parent", "parent"),
    ("level", "level"),
    ("tumorForm", "tumor_form")
]


class OncoKBTransform(Transform):
    """A class for transforming OncoKB to the common data model."""

    method = f"method:{MethodID.ONCOKB_SOP}"

    def __init__(
        self, data_dir: Path = APP_ROOT / "data", harvester_path: Optional[Path] = None,
        normalizers: Optional[VICCNormalizers] = None
    ) -> None:
        """Initialize OncoKB Transform class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param VICCNormalizers normalizers: normalizer collection instance
        """
        super().__init__(data_dir, harvester_path, normalizers)
        # Able to normalize these IDSs
        self.valid_ids = {
            "disease_descriptors": dict(),
            "therapy_descriptors": dict()
        }
        # Unable to normalize these IDs
        self.invalid_ids = {
            "therapy_descriptors": set(),
            "disease_descriptors": set()
        }

        self.methods = [
            Method(id=f"method:{MethodID.ONCOKB_SOP}",
                   label="OncoKB Curation Standard Operating Procedure",
                   url="https://sop.oncokb.org/",
                   version=Date(year=2021, month=11).dict(),
                   authors="OncoKB").dict(exclude_none=True)
        ]

    async def transform(self) -> None:
        """Transform OncoKB harvested JSON to common data model. Will update instance
        variables (statements, propositions, variation_descriptors, gene_descriptors,
        therapy_descriptors, disease_descriptors, documents) with transformed data from
        OncoKB.
        """
        data = self.extract_harvester()
        variants_data = data["variants"]
        genes_data = data["genes"]
        levels = data["levels"]

        self.sensitive_levels = levels["sensitive"]
        self.resistance_levels = levels["resistance"]
        self.fda_levels = levels["fda"]

        self._add_gene_descriptors(genes_data)
        await self._transform_evidence(variants_data)

    async def _transform_evidence(self, variants_data: List[Dict]) -> None:
        """Transform OncoKB evidence to common data model. Will update instance
        variables (statements, propositions, variation_descriptors, gene_descriptors,
        therapy_descriptors, disease_descriptors, documents) with transformed data from
        OncoKB.

        :param List[Dict] variants_data: Variants data from OncoKB. Contains variant
            and associated evidence data.
        """
        for data in variants_data:
            # Exclude trying on variants we know we can't normalize
            unable_to_normalize_variant = {
                "fusion", "fusions", "mutation", "mutations", "tandem", "domain",
                "splice", "deletion", "hypermethylation", "silencing", "overexpression"
            }

            alt = data["query"]["alteration"]
            if set(alt.lower().split()) & unable_to_normalize_variant:
                logger.debug(f"Variation Normalizer does not support: {alt}")
                continue

            variation_descriptor = await self._add_variation_descriptor(data)
            if not variation_descriptor:
                continue

            # We skip prognostic evidence (prognosticImplications) since there is not
            # enough information

            for diagnostic_imp in data["diagnosticImplications"]:
                # Diagnostic evidence is all inclusive
                self._add_diagnostic_evidence(diagnostic_imp, variation_descriptor)

            for treatment in data["treatments"]:
                # Therapeutic evidence
                # Only support where only one drug
                if len(treatment["drugs"]) != 1:
                    continue

                self._add_therapeutic_evidence(treatment, variation_descriptor)

    def _add_evidence(
        self, evidence_data: Dict, proposition_type: PropositionType, level: str,
        predicate: Predicate, disease_data: Dict, variation_descriptor: Dict,
        extensions: Optional[List] = None, therapy_descriptor: Optional[Dict] = None
    ) -> None:
        """Add transformed oncokb evidence as statements
        Will update instance variables (disease_descriptors, proposition, documents,
        statements)

        :param Dict evidence_data: OncoKB evidence data
        :param PropositionType proposition_type: Proposition type of `evidence_data`
        :param str level: OncoKB level of `evidence_data`
        :param Predicate predicate: Predicate of `evidence_data`
        :param Dict disease_data: Disease data for `evidence_data`
        :param Dict variation_descriptor: Variation descriptor associated to
            `evidence_data`
        :param Optional[List] extensions: List of extensions for `evidence_data`
        :param Optional[Dict] therapy_descriptor: Therapy descriptor associated to
            `evidence_data`. Only for therapeutic evidence.
        """
        disease_descriptor = self._add_disease_descriptor(disease_data)
        if not disease_descriptor:
            return None

        proposition = self._get_proposition(
            proposition_type, predicate, variation_descriptor["variation_id"],
            disease_descriptor["disease_id"],
            therapy_descriptor["therapy_id"] if therapy_descriptor else None)
        if proposition:
            documents = self._get_documents(evidence_data["pmids"])
            description = evidence_data["description"]

            statement_params = {
                "description": description if description else None,
                "evidence_level": f"oncokb.evidence_level:{level}",
                "proposition": proposition["id"],
                "variation_descriptor": variation_descriptor["id"],
                "disease_descriptor": disease_descriptor["id"],
                "therapy_descriptor": therapy_descriptor["id"] if therapy_descriptor else None,  # noqa: E501
                "method": self.methods[0]["id"],
                "supported_by": [d["id"] for d in documents],
                "extensions": extensions
            }
            digest = self._generate_digest(statement_params)
            statement_params["id"] = f"oncokb.evidence:{digest}"
            statement = Statement(
                **statement_params).dict(by_alias=True, exclude_none=True)
            self.statements.append(statement)

    def _add_diagnostic_evidence(self, diagnostic_implication: Dict,
                                 variation_descriptor: Dict) -> None:
        """Transform OncoKB Diagnostic Evidence to common data model. Will update
        instance variables (statements, propositions, variation_descriptors,
        gene_descriptors, therapy_descriptors, disease_descriptors, documents) with
        transformed data from OncoKB.

        :param Dict diagnostic_implication: Diagnostic evidence
        :param Dict variation_descriptor: Variation Descriptor associated to diagnostic
            evidence
        """
        predicate = DiagnosticPredicate.POSITIVE
        proposition_type = PropositionType.DIAGNOSTIC
        level = diagnostic_implication["levelOfEvidence"]
        disease_data = diagnostic_implication["tumorType"]
        self._add_evidence(diagnostic_implication, proposition_type, level, predicate,
                           disease_data, variation_descriptor)

    def _add_therapeutic_evidence(self, treatment: Dict,
                                  variation_descriptor: Dict) -> None:
        """Transform OncoKB Therapeutic Evidence to common data model. Will update
        instance variables (statements, propositions, variation_descriptors,
        gene_descriptors, therapy_descriptors, disease_descriptors, documents) with
        transformed data from OncoKB.

        :param Dict treatment: Therapeutic evidence
        :param Dict variation_descriptor: Variation Descriptor associated to therapeutic
            evidence
        """
        level = treatment["level"]
        proposition_type = PropositionType.PREDICTIVE
        predicate = None
        if level in self.sensitive_levels:
            predicate = PredictivePredicate.SENSITIVITY
        elif level in self.resistance_levels:
            predicate = PredictivePredicate.RESISTANCE
        else:
            # This shouldn't happen, but adding a check just in case
            logger.warning(f"Level {level} not in Sensitive or Resistance level")
            return None

        therapy_descriptor = self._add_therapy_descriptor(treatment["drugs"])
        if not therapy_descriptor:
            return None

        disease_data = treatment["levelAssociatedCancerType"]

        extensions = list()
        fda_level = treatment["fdaLevel"]
        if fda_level:
            ext_value = {
                "level": fda_level,
                "description": self.fda_levels[fda_level]

            }
            extensions.append(Extension(name="onckb_fda_level", value=ext_value).dict())

        self._add_evidence(treatment, proposition_type, level, predicate, disease_data,
                           variation_descriptor, extensions, therapy_descriptor)

    def _add_therapy_descriptor(self, drugs_data: List[Dict]) -> Optional[Dict]:
        """Get therapy descriptor
        The `therapy_descriptor` instance variable will be updated if therapy normalizer
        was able to normalize the drug and if the drug does not already have a therapy
        descriptor.

        :param List[Dict] drugs_data: List of drugs. For now, `drugs_data` will always
            have a length of one.
        :return: Therapy descriptor represented as a dictionary if therapy normalizer
            was able to normalize the drug
        """
        # Since we only support 1 therapeutic we can get the first element
        drug = drugs_data[0]
        ncit_code = drug["ncitCode"]
        if ncit_code in self.valid_ids["therapy_descriptors"]:
            therapy_descriptor = self.valid_ids["therapy_descriptors"][ncit_code]
        else:
            therapy_descriptor = None
            if ncit_code not in self.invalid_ids["therapy_descriptors"]:
                therapy_descriptor = self._get_therapy_descriptor(drugs_data)
                if therapy_descriptor:
                    self.valid_ids["therapy_descriptors"][ncit_code] = therapy_descriptor  # noqa: E501
                    self.therapy_descriptors.append(therapy_descriptor)
                else:
                    self.invalid_ids["therapy_descriptors"].add(ncit_code)
        return therapy_descriptor

    def _get_therapy_descriptor(self, drugs_data: List[Dict]) -> Optional[Dict]:
        """Get therapy descriptor for drug

        :param List[Dict] drugs_data: List of drugs. For now, `drugs_data` will always
            have a length of one.
        :return: Therapy descriptor represented as a dictionary if therapy normalizer
            was able to normalize the drug
        """
        # Since we only support 1 therapeutic we can get the first element
        drug = drugs_data[0]
        ncit_id = f"ncit:{drug['ncitCode']}"
        label = drug["drugName"]

        queries = [ncit_id, label]
        therapy_norm_resp, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy(queries)
        if not normalized_therapy_id:
            logger.warning(f"Therapy Normalizer unable to normalize using queries: {queries}")  # noqa: E501
            return None

        regulatory_approval_extension = \
            self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)

        return ValueObjectDescriptor(
            type="TherapyDescriptor",
            id=f"oncokb.normalize.therapy:{quote(label)}",
            label=label,
            therapy_id=normalized_therapy_id,
            alternate_labels=drug["synonyms"] if drug["synonyms"] else None,
            xrefs=[ncit_id],
            extensions=[regulatory_approval_extension] if regulatory_approval_extension else None  # noqa: E501
        ).dict(exclude_none=True)

    def _add_disease_descriptor(self, disease_data: Dict) -> Optional[Dict]:
        """Get disease descriptor
        The `disease_descriptor` instance variable will be updated if disease normalizer
        was able to normalize the disease and if the disease does not already have a
        disease descriptor.

        :param Dict disease_data: Disease data
        :return: Disease descriptor represented as a dictionary if disease normalizer
            was able to normalize the disease
        """
        disease_id = str(disease_data["id"])
        if disease_id in self.valid_ids["disease_descriptors"]:
            disease_descriptor = self.valid_ids["disease_descriptors"][disease_id]
        else:
            disease_descriptor = None
            if disease_id not in self.invalid_ids["disease_descriptors"]:
                disease_descriptor = self._get_disease_descriptor(disease_data)
                if disease_descriptor:
                    self.valid_ids["disease_descriptors"][disease_id] = \
                        disease_descriptor
                    self.disease_descriptors.append(disease_descriptor)
                else:
                    self.invalid_ids["disease_descriptors"].add(disease_id)
        return disease_descriptor

    def _get_disease_descriptor(self, disease_data: Dict) -> Optional[Dict]:
        """Get disease descriptor for disease

        :param Dict disease_data: Disease data
        :return: Disease descriptor represented as a dictionary if disease normalizer
            was able to normalize the disease
        """
        oncokb_disease_id = f"oncokb.disease:{disease_data['id']}"
        oncotree_code = f"oncotree:{disease_data['code']}"
        label = disease_data["name"]
        queries = [oncotree_code, label]
        _, normalized_disease_id = self.vicc_normalizers.normalize_disease(queries)
        if not normalized_disease_id:
            logger.warning(f"Disease Normalizer unable to normalize: "
                           f"{oncokb_disease_id} using queries {queries}")
            return None

        extensions = list()
        for key, ext_label in DISEASE_EXT_CONVERSIONS:
            if disease_data[key] or disease_data[key] is False:
                if key == "mainType":
                    value = deepcopy(disease_data[key])
                    value["tumor_form"] = value.pop("tumorForm")
                else:
                    value = disease_data[key]
                extensions.append(Extension(name=ext_label, value=value))

        disease_descriptor = ValueObjectDescriptor(
            id=oncokb_disease_id,
            type="DiseaseDescriptor",
            label=label,
            disease_id=normalized_disease_id,
            xrefs=[oncotree_code],
            extensions=extensions if extensions else None
        ).dict(exclude_none=True)
        return disease_descriptor

    def _add_gene_descriptors(self, genes: List[Dict]) -> None:
        """Add gene descriptors represented as a dict to the `gene_descriptors` instance
            variable

        :param List[Dict] genes: List of genes in OncoKB
        """
        for gene in genes:
            gene_queries = list()
            xrefs = list()

            entrez_id = gene["entrezGeneId"]
            if entrez_id:
                entrez_id = f"ncbigene:{entrez_id}"
                gene_queries.append(entrez_id)
                xrefs.append(entrez_id)

            symbol = gene["hugoSymbol"]
            if symbol:
                gene_queries.append(symbol)

            _, normalized_gene_id = self.vicc_normalizers.normalize_gene(gene_queries)
            if normalized_gene_id:
                extensions = list()

                for key, ext_label in GENE_EXT_CONVERSIONS:
                    if gene[key] or gene[key] is False:
                        extensions.append(Extension(name=ext_label, value=gene[key]))

                gene_descriptor = GeneDescriptor(
                    id=f"oncokb.normalize.gene:{symbol}",
                    label=symbol,
                    gene_id=normalized_gene_id,
                    description=gene["summary"] if gene["summary"] else None,
                    extensions=extensions if extensions else None,
                    xrefs=xrefs if xrefs else None
                ).dict(exclude_none=True)
                self.gene_descriptors.append(gene_descriptor)
            else:
                logger.warning(f"Gene Normalizer unable to normalize: {gene_queries}")

    async def _add_variation_descriptor(self, data: Dict) -> Optional[Dict]:
        """Get variation descriptor
        The `variation_descriptors` instance variable will be updated if variation
        normalize was able to normalize the variant.

        :param Dict data: OncoKB data
        :return: Variation Descriptor represented as a dictionary if variation
            normalizer was able to normalize the variant
        """
        query = data["query"]
        gene = query["hugoSymbol"]
        alteration = query["alteration"]
        if not all((gene, alteration)):
            return None

        variant = f"{gene} {alteration}"
        variation_descriptor = await self.vicc_normalizers.normalize_variation(
            [variant])

        if not variation_descriptor:
            logger.warning(f"Variation Normalizer unable to normalize: {variant}")
            return None

        extensions = list()
        for key, ext_label in VARIATION_EXT_CONVERSIONS:
            if data[key] or data[key] is False:
                extensions.append(Extension(name=ext_label, value=data[key]).dict())

        vd = VariationDescriptor(
            id=f"oncokb.variant:{quote(variant)}",
            label=variant,
            description=data["variantSummary"] if data["variantSummary"] else None,
            variation_id=variation_descriptor.variation_id,
            variation=variation_descriptor.variation,
            gene_context=f"oncokb.normalize.gene:{query['hugoSymbol']}",
            extensions=extensions if extensions else None
        ).dict(by_alias=True, exclude_none=True)
        self.variation_descriptors.append(vd)
        return vd

    def _get_documents(self, pmids: List[str]) -> List[dict]:
        """Get documents from PMIDs.

        :param List[str] pmids: List of PubMed IDs
        :return: List of documents represented as dictionaries
        """
        documents = list()
        for pmid in pmids:
            document = Document(
                id=f"pmid:{pmid}",
                label=f"PubMed {pmid}"
            ).dict(exclude_none=True)
            documents.append(document)
            if document not in self.documents:
                self.documents.append(document)

        # TODO: Do abstracts in issue-204
        return documents
