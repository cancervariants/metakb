"""A module to convert MOA resources to common data model"""
from pathlib import Path
from typing import Optional, List, Dict
import logging
from urllib.parse import quote

from ga4gh.vrsatile.pydantic.core_models import Extension, Disease, Therapeutic, \
    CombinationTherapeuticCollection, Coding
from ga4gh.vrsatile.pydantic.vrsatile_models import VariationDescriptor, \
    GeneDescriptor, DiseaseDescriptor, TherapeuticDescriptor, \
    TherapeuticCollectionDescriptor

from metakb import APP_ROOT
from metakb.normalizers import VICCNormalizers
from metakb.transform.base import Transform
from metakb.schemas import MoaEvidenceLevel, PredictivePredicate, VariationOrigin, \
    TargetPropositionType, SourceName, NormalizerPrefix, Document, MethodId, \
    VariationNeoplasmTherapeuticResponseProposition, \
    VariationNeoplasmTherapeuticResponseStatement

logger = logging.getLogger('metakb.transform.moa')
logger.setLevel(logging.DEBUG)


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
        self.valid_ids = {
            "variation_descriptors": dict(),
            "disease_descriptors": dict(),
            "therapeutic_descriptors": dict(),
            "gene_descriptors": dict(),
            "therapeutic_collection_descriptors": dict(),
            "documents": dict()
        }

        # Unable to normalize these IDs
        self.invalid_ids = {
            "disease_descriptors": set(),
            "therapeutic_descriptors": set(),
            "therapeutic_collection_descriptors": set()
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

        self._add_gene_descriptors(genes)
        await self._add_variation_descriptors(variants)
        self._add_documents(sources)

        # Transform MOA assertions
        await self._transform_assertions(assertions)

    async def _transform_assertions(self, assertions: List[Dict]) -> None:
        """Transform MOAlmanac assertions. Will add associated values to instance
        variables.

        :param: A list of MOA assertion records
        """
        for record in assertions:
            variant_id = record["variant"]["id"]
            variation_descriptor = self.valid_ids["variation_descriptors"].get(
                variant_id)
            if not variation_descriptor:
                continue

            therapy_name = record["therapy_name"]
            if not therapy_name:
                continue

            if "+" in therapy_name:
                # Multiple therapies --> Therapeutic Collection
                therapy_names = [tn.strip() for tn in therapy_name.split("+")]
                therapy_type = record["therapy_type"]
                therapeutic_digest = self._get_digest_for_str_lists(therapy_names)
                therapeutic_descriptor_id = f"moa.tcd:{therapeutic_digest}"
                therapeutic_descriptor = self._add_therapeutic_collection_descriptor(
                    therapeutic_descriptor_id, therapy_names, therapy_type)
            else:
                therapeutic_descriptor = self._add_therapeutic_descriptor(therapy_name)

            if not therapeutic_descriptor:
                continue

            disease_descriptor = self._add_disease_descriptor(record["disease"])
            if not disease_descriptor:
                continue

            proposition = self._get_proposition(
                record, variation_descriptor, disease_descriptor,
                therapeutic_descriptor)
            if not proposition:
                continue

            document = self.valid_ids["documents"].get(record["source_ids"])
            if document not in self.documents:
                self.documents.append(document)

            method = self.methods_mappping[MethodId.MOA_ASSERTION_BIORXIV.value]
            if method not in self.methods:
                self.methods.append(method)

            predictive_implication = record["predictive_implication"].strip().replace(" ", "_").replace("-", "_").upper()  # noqa: E501
            moa_evidence_level = MoaEvidenceLevel[predictive_implication]
            evidence_level_params = \
                self.evidence_level_vicc_concept_mapping[moa_evidence_level]
            evidence_level = Coding(**evidence_level_params).dict(exclude_none=True)
            variation_origin = self._get_variation_origin(record["variant"])

            statement = VariationNeoplasmTherapeuticResponseStatement(
                id=f"{SourceName.MOA.value}.assertion:{record['id']}",
                description=record["description"],
                evidence_level=evidence_level,
                variation_origin=variation_origin,
                target_proposition=proposition["id"],
                subject_descriptor=variation_descriptor["id"],
                neoplasm_type_descriptor=disease_descriptor["id"],
                object_descriptor=therapeutic_descriptor["id"],
                method=method,
                is_reported_in=[document]
            ).dict(exclude_none=True)
            self.statements.append(statement)

    def _get_proposition(
        self, record: Dict, variation_descriptor: Dict, disease_descriptor: Dict,
        therapeutic_descriptor: Dict
    ) -> Optional[Dict]:
        """Return a list of propositions.

        :param Dict record: MOA assertion
        :param Dict variation_descriptor: Variation Descriptor for assertion's variant
        :param Dict disease_descriptor: Disease Descriptor for assertion's disease
        :param Dict therapeutic_descriptor: Therapeutic (or Collection) Descriptor
            for assertion's therapy/therapies
        :return: Variation Neoplasm Therapeutic Response Proposition represented as a
            dict
        """
        predicate = self._get_predicate(record["clinical_significance"])

        # Don't support TR that has  `None`, 'N/A', or 'Unknown' predicate
        if not predicate:
            return None

        params = {
            "type": TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE.value,
            "predicate": predicate,
            "subject": variation_descriptor["variation"]["id"],
            "neoplasm_type_qualifier": Disease(id=disease_descriptor["disease"]).dict(exclude_none=True),  # noqa: E501
        }

        td_type = therapeutic_descriptor["type"]
        if td_type == "TherapeuticDescriptor":
            params["object"] = Therapeutic(id=therapeutic_descriptor["therapeutic"]).dict(exclude_none=True)  # noqa: E501
        elif td_type == "TherapeuticsCollectionDescriptor":
            params["object"] = therapeutic_descriptor["therapeutic_collection"]

        # Get corresponding id for proposition
        params["id"] = self._get_proposition_id(params)
        if not params["id"]:
            return None

        proposition = VariationNeoplasmTherapeuticResponseProposition(**params).dict(exclude_none=True)  # noqa: E501
        if proposition not in self.propositions:
            self.propositions.append(proposition)
        return proposition

    def _get_predicate(self, clin_sig: str) -> Optional[str]:
        """Get the predicate of this record

        :param str clin_sig: clinical significance of the assertion
        :return: predicate if valid, None otherwise
        """
        if not clin_sig:
            return None
        try:
            return PredictivePredicate[clin_sig.upper()].value
        except KeyError:
            return None

    def _get_variation_origin(self, variant: Dict) -> Optional[str]:
        """Return variant origin.

        :param Dict variant: A MOA variant record
        :return: A str representation of variation origin
        """
        if variant["feature_type"] == "somatic_variant":
            origin = VariationOrigin.SOMATIC.value
        elif variant["feature_type"] == "germline_variant":
            origin = VariationOrigin.GERMLINE.value
        else:
            origin = None
        return origin

    async def _add_variation_descriptors(self, variants: List[Dict]):
        """Add variation descriptors to instance variable. Will also cache valid
        Variation Descriptors to `self.valid_ids["variation_descriptors"]`

        :param List[Dict] variants: All variants in MOAlmanac
        """
        for variant in variants:
            # Skipping Fusion + Translocation + rearrangements that variation normalizer
            # does not support
            if "rearrangement_type" in variant:
                continue

            gene = variant.get("gene")
            if not gene:
                continue

            gene_descriptor = self.valid_ids["gene_descriptors"].get(gene)
            if not gene_descriptor:
                continue

            vrs_ref_allele_seq = variant["protein_change"][2] \
                if "protein_change" in variant and variant["protein_change"] else None

            v_norm_resp = None
            variant_id = variant["id"]
            # For now, the normalizer only support a.a substitution
            if gene_descriptor and variant.get("protein_change"):
                gene = gene_descriptor["label"]
                query = f"{gene} {variant['protein_change'][2:]}"
                v_norm_resp = await self.vicc_normalizers.normalize_variation([query])

                if not v_norm_resp:
                    logger.warning(f"Variant Normalizer unable to normalize: "
                                   f"moa.variant:{variant_id}.")
                    continue
            else:
                logger.warning(f"Variation Normalizer does not support "
                               f"moa.variant:{variant_id}: {variant}")
                continue

            extensions = self._get_variant_extensions(variant)

            variation_descriptor = VariationDescriptor(
                id=f"moa.variant:{variant_id}",
                label=variant["feature"],
                variation=v_norm_resp.variation_descriptor.variation,
                gene_context=gene_descriptor["id"],
                vrs_ref_allele_seq=vrs_ref_allele_seq,
                extensions=extensions if extensions else None
            ).dict(by_alias=True, exclude_none=True)
            self.valid_ids["variation_descriptors"][variant_id] = variation_descriptor
            self.variation_descriptors.append(variation_descriptor)

    def _get_variant_extensions(self, variant: Dict) -> List[Dict]:
        """Return a list of extensions for a variant.

        :param Dict variant: A MOA variant record
        :return: A list of extensions
        """
        coordinate = ["chromosome", "start_position", "end_position",
                      "reference_allele", "alternate_allele", "cdna_change",
                      "protein_change", "exon"]

        extensions = [
            Extension(
                name="moa_representative_coordinate",
                value={c: variant[c] for c in coordinate}
            ).dict(exclude_none=True)
        ]

        if variant["rsid"]:
            extensions.append(
                Extension(
                    name="moa_rsid",
                    value=variant["rsid"]
                ).dict(exclude_none=True))
        return extensions

    def _add_gene_descriptors(self, genes: List[str]) -> None:
        """Add gene descriptors to instance variable. Will also cache valid
        Gene Descriptors to `self.valid_ids["gene_descriptors"]`

        :param List[Dict] genes: All genes in MOAlmanac
        """
        for gene in genes:
            _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
            if normalized_gene_id:
                gene_descriptor = GeneDescriptor(
                    id=f"{SourceName.MOA.value}.normalize."
                       f"{NormalizerPrefix.GENE.value}:{quote(gene)}",
                    label=gene,
                    gene=normalized_gene_id,
                ).dict(exclude_none=True)
                self.valid_ids["gene_descriptors"][gene] = gene_descriptor
                self.gene_descriptors.append(gene_descriptor)
            else:
                logger.warning(f"Gene Normalizer unable to normalize: {gene}")

    def _add_documents(self, sources: List) -> None:
        """Add documents to instance variable. Will also cache valid documents to
        `self.valid_ids["documents"]`
        """
        for source in sources:
            xrefs = list()
            if source["pmid"] != "None":
                xrefs.append(f"pmid:{source['pmid']}")
            if source["doi"]:
                xrefs.append(f"doi:{source['doi']}")
            if source["nct"] != "None":
                xrefs.append(f"nct:{source['nct']}")

            extensions = [
                Extension(
                    name="source_url",
                    value=source["url"]
                ).dict(exclude_none=True),
                Extension(
                    name="source_type",
                    value=source["type"]
                ).dict(exclude_none=True)
            ]
            source_id = source["id"]

            document = Document(
                id=f"moa.source:{source_id}",
                title=source["citation"],  # TODO: Should this be label?
                xrefs=xrefs if xrefs else None,
                extensions=extensions
            ).dict(exclude_none=True)
            self.valid_ids["documents"][source_id] = document

    def _add_therapeutic_descriptor(self, label: str) -> Optional[Dict]:
        """Get Therapeutic Descriptor given a therapy name. Will add `label` to
        valid or invalid cache if able to return therapeutic descriptor or not. Will
        add valid therapeutic descriptors to instance variable.

        :param str label: Therapy name to get therapeutic descriptor for
        :return: Therapeutic Descriptor represented as a dict
        """
        therapeutic_descriptor = self.valid_ids["therapeutic_descriptors"].get(label)
        if therapeutic_descriptor:
            return therapeutic_descriptor
        else:
            therapeutic_descriptor = None
            if label not in self.invalid_ids["therapeutic_descriptors"]:
                therapeutic_descriptor = self._get_therapeutic_descriptor(label)
                if therapeutic_descriptor:
                    self.valid_ids["therapeutic_descriptors"][label] = \
                        therapeutic_descriptor
                else:
                    self.invalid_ids["therapeutic_descriptors"].add(label)
        return therapeutic_descriptor

    def _get_therapeutic_descriptor(self, label: str) -> Optional[Dict]:
        """Return a therapeutic descriptor for a given `label`

        :param str label: Therapy name to get therapeutic descriptor for
        :return: A Therapeutic Descriptor represented as a dict
        """
        if not label:
            return None

        therapy_norm_resp, normalized_therapeutic_id = \
            self.vicc_normalizers.normalize_therapy([label])

        if not normalized_therapeutic_id:
            logger.warning(f"Therapy Normalizer unable to normalize: {label}")
            return None

        if normalized_therapeutic_id:
            regulatory_approval_extension = \
                self.vicc_normalizers.get_regulatory_approval_extension(therapy_norm_resp)  # noqa: E501
            therapeutic_descriptor = TherapeuticDescriptor(
                id=f"{SourceName.MOA.value}."
                   f"{therapy_norm_resp.therapeutic_descriptor.id}",
                label=label,
                therapeutic=normalized_therapeutic_id,
                extensions=[regulatory_approval_extension] if regulatory_approval_extension else None  # noqa: E501
            ).dict(exclude_none=True)
            self.therapeutic_descriptors.append(therapeutic_descriptor)
            return therapeutic_descriptor
        else:
            return None

    def _add_therapeutic_collection_descriptor(
        self, therapeutic_descriptor_id: str, therapy_names: List[str],
        therapy_type: str
    ) -> Optional[Dict]:
        """Get Therapeutic Collection Descriptor given multiple therapy names. Will add
        `therapeutic_descriptor_id` to valid or invalid cache if able to return
        therapeutic collection descriptor or not. Will add valid therapeutic collection
        descriptors to instance variable.

        :param str therapeutic_descriptor_id: Digest for therapeutic collection
            descriptor ID
        :param List[str] therapy_names: List of therapy names
        :param str therapy_type: Therapeutic type for `therapy_names`
        :return: Therapeutic Collection Descriptor represented as a dict
        """
        tcd = self.valid_ids["therapeutic_collection_descriptors"].get(
            therapeutic_descriptor_id)
        if tcd:
            return tcd
        else:
            tcd = None
            if therapeutic_descriptor_id not in self.invalid_ids["therapeutic_collection_descriptors"]:  # noqa: E501
                tcd = self._get_therapeutic_collection_descriptor(
                    therapeutic_descriptor_id, therapy_names, therapy_type
                )
                if tcd:
                    self.valid_ids["therapeutic_collection_descriptors"][therapeutic_descriptor_id] = tcd  # noqa: E501
                else:
                    self.invalid_ids["therapeutic_collection_descriptors"].add(therapeutic_descriptor_id)  # noqa: E501
            return tcd

    def _get_therapeutic_collection_descriptor(
        self, therapeutic_descriptor_id: str, therapy_names: List[str],
        therapy_type: str
    ) -> Optional[TherapeuticCollectionDescriptor]:
        """Return a therapeutic collection descriptor for given `therapy_names`

        :param str therapeutic_descriptor_id: Digest for therapeutic collection
            descriptor ID
        :param List[str] therapy_names: List of therapy names
        :param str therapy_type: Therapeutic type for `therapy_names`
        :return: A Therapeutic Collection Descriptor represented as a dict
        """
        member_descriptors = list()
        members = list()

        for therapy in therapy_names:
            therapy_descriptor = self._add_therapeutic_descriptor(therapy)
            if therapy_descriptor:
                member_descriptors.append(therapy_descriptor)
                therapeutic = Therapeutic(id=therapy_descriptor["therapeutic"]).dict(exclude_none=True)  # noqa: E501
                members.append(therapeutic)
            else:
                return None

        therapeutic_collection = None
        if therapy_type.upper() in {"COMBINATION THERAPY", "IMMUNOTHERAPY",
                                    "RADIATION THERAPY", "TARGETED THERAPY"}:
            therapeutic_collection = CombinationTherapeuticCollection(
                members=members).dict(exclude_none=True)  # noqa: E501
        else:
            logger.debug(f"therapy typ, {therapy_type}, is not supported")

        if not therapeutic_collection:
            return None

        extensions = [Extension(name="moa_therapy_type",
                                value=therapy_type).dict(exclude_none=True)]

        tcd = TherapeuticCollectionDescriptor(
            id=therapeutic_descriptor_id,
            therapeutic_collection=therapeutic_collection,
            member_descriptors=member_descriptors,
            extensions=extensions
        ).dict(exclude_none=True)
        self.therapeutic_collection_descriptors.append(tcd)
        return tcd

    def _add_disease_descriptor(self, disease: Dict) -> Optional[Dict]:
        """Get Disease Descriptor given disease. Will add `disease_descriptor_id``
        (generated digest) to valid or invalid cache if able to return disease
        descriptor or not. Will add valid disease descriptor to instance variable.

        :param Dict disease: MOA Disease
        :return: Disease Descriptor represented as a dict
        """
        if not all(value for value in disease.values()):
            return None

        disease_list = [f"{k}:{v}" for k, v in disease.items() if v]
        disease_descriptor_id = self._get_digest_for_str_lists(disease_list)

        disease_descriptor = self.valid_ids["disease_descriptors"].get(disease_descriptor_id)  # noqa: E501
        if disease_descriptor:
            return disease_descriptor
        else:
            disease_descriptor = None
            if disease_descriptor_id not in self.invalid_ids["disease_descriptors"]:
                disease_descriptor = self._get_disease_descriptor(disease)
                if disease_descriptor:
                    self.valid_ids["disease_descriptors"][disease_descriptor_id] = \
                        disease_descriptor
                else:
                    self.invalid_ids["disease_descriptors"].add(disease_descriptor_id)
            return disease_descriptor

    def _get_disease_descriptor(self, disease: Dict) -> Optional[Dict]:
        """Return a Disease Descriptor

        :param Dict disease: an MOA disease record
        :return: A Disease Descriptor
        """
        queries = list()
        xrefs = list()
        alternate_labels = list()

        ot_code = disease["oncotree_code"]
        if ot_code:
            ot_code = f"oncotree:{ot_code}"
            queries.append(ot_code)
            xrefs.append(ot_code)

        ot_term = disease["oncotree_term"]
        disease_name = disease["name"]
        if ot_term:
            queries.append(ot_term)
            if ot_term != ot_code and ot_term != disease_name:
                alternate_labels.append(ot_term)

        if disease_name:
            queries.append(disease_name)

        disease_norm_resp, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease(queries)

        if not normalized_disease_id:
            logger.warning(f"Disease Normalize unable to normalize: {queries}")
            return None

        disease_descriptor = DiseaseDescriptor(
            id=f"{SourceName.MOA.value}.{disease_norm_resp.disease_descriptor.id}",
            label=disease_name,
            disease=normalized_disease_id,
            xrefs=xrefs if xrefs else None,
            alternate_labels=alternate_labels if alternate_labels else None
        ).dict(exclude_none=True)
        self.disease_descriptors.append(disease_descriptor)
        return disease_descriptor
