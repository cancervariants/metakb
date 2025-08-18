"""A module for the Transformer base class."""

import datetime
import json
import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar, TypeVar

from disease.schemas import (
    NamespacePrefix as DiseaseNamespacePrefix,
)
from disease.schemas import (
    NormalizationService as NormalizedDisease,
)
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.cat_vrs.recipes import ProteinSequenceConsequence
from ga4gh.core import sha512t24u
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    iriReference,
)
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import (
    Document,
    Method,
    Statement,
    TherapyGroup,
)
from ga4gh.vrs.models import Allele, CopyNumberChange, CopyNumberCount
from gene.schemas import (
    NamespacePrefix as GeneNamespacePrefix,
)
from gene.schemas import (
    NormalizeService as NormalizedGene,
)
from pydantic import BaseModel, Field, StrictStr
from therapy.schemas import (
    NamespacePrefix as TherapyNamespacePrefix,
)
from therapy.schemas import (
    NormalizationService as NormalizedTherapy,
)

from metakb import DATE_FMT
from metakb.config import get_config
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import (
    ViccNormalizers,
)

logger = logging.getLogger(__name__)

# Normalizer response type to attribute name
NORMALIZER_INSTANCE_TO_ATTR = {
    NormalizedDisease: "disease",
    NormalizedTherapy: "therapy",
    NormalizedGene: "gene",
}

_CacheType = TypeVar("_CacheType", bound="_TransformedRecordsCache")


def _sanitize_name(name: str) -> str:
    """Trim leading and trailing whitespace and replace whitespace characters with
    underscores

    :param name: Name to sanitize
    :return: Sanitized string with whitespace characters replaced by underscores
    """
    return re.sub(r"\s+", "_", name.strip())


class NormalizerExtensionName(str, Enum):
    """Define constraints for normalizer extension names"""

    PRIORITY = "vicc_normalizer_priority"  # concept mapping is merged concept ID
    FAILURE = "vicc_normalizer_failure"  # normalizer failed or is not supported


class EcoLevel(str, Enum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class MethodId(str, Enum):
    """Create method id constants"""

    CIVIC_EID_SOP = "civic.method:2019"
    MOA_ASSERTION_BIORXIV = "moa.method:2021"


class CivicEvidenceLevel(str, Enum):
    """Define constraints for CIViC evidence levels"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class MoaEvidenceLevel(str, Enum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "FDA-Approved"
    GUIDELINE = "Guideline"
    CLINICAL_TRIAL = "Clinical trial"
    CLINICAL_EVIDENCE = "Clinical evidence"
    PRECLINICAL = "Preclinical evidence"
    INFERENTIAL = "Inferential evidence"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: list[StrictStr] = []
    exact_mappings: set[CivicEvidenceLevel | MoaEvidenceLevel | EcoLevel] = set()
    definition: StrictStr


class _TransformedRecordsCache(BaseModel):
    """Define model for caching transformed records"""

    therapies: ClassVar[dict[str, MappableConcept]] = {}
    conditions: ClassVar[dict[str, MappableConcept]] = {}
    genes: ClassVar[dict[str, MappableConcept]] = {}


class TransformedData(BaseModel):
    """Define model for transformed data"""

    statements_evidence: list[Statement] = Field(
        [], description="Statement objects for evidence records"
    )
    statements_assertions: list[
        VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = Field([], description="Statement objects for assertion records")
    categorical_variants: list[CategoricalVariant] = []
    variations: list[CopyNumberChange | CopyNumberCount | Allele] = []
    genes: list[MappableConcept] = []
    therapies: list[MappableConcept | TherapyGroup] = []
    conditions: list[MappableConcept] = []
    methods: list[Method] = []
    documents: list[Document | iriReference] = []


class Transformer(ABC):
    """A base class for transforming harvester data."""

    _methods: ClassVar[list[Method]] = [
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            name="MOAlmanac (2021)",
            reportedIn=Document(
                name="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
                doi="10.1038/s43018-021-00243-3",
                pmid="35121878",
            ),
        ),
    ]
    methods_mapping: ClassVar[dict[MethodId, Method]] = {m.id: m for m in _methods}
    _vicc_concept_vocabs: ClassVar[list[ViccConceptVocab]] = [
        ViccConceptVocab(
            id="vicc:e000000",
            domain="EvidenceStrength",
            term="evidence",
            parents=[],
            exact_mappings={EcoLevel.EVIDENCE},
            definition="A type of information that is used to support statements.",
        ),
        ViccConceptVocab(
            id="vicc:e000001",
            domain="EvidenceStrength",
            term="authoritative evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.A},
            definition="Evidence derived from an authoritative source describing a proven or consensus statement.",
        ),
        ViccConceptVocab(
            id="vicc:e000002",
            domain="EvidenceStrength",
            term="FDA recognized evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.FDA_APPROVED},
            definition="Evidence derived from statements recognized by the US Food and Drug Administration.",
        ),
        ViccConceptVocab(
            id="vicc:e000003",
            domain="EvidenceStrength",
            term="professional guideline evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.GUIDELINE},
            definition="Evidence derived from statements by professional society guidelines",
        ),
        ViccConceptVocab(
            id="vicc:e000004",
            domain="EvidenceStrength",
            term="clinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
            definition="Evidence derived from clinical research studies",
        ),
        ViccConceptVocab(
            id="vicc:e000005",
            domain="EvidenceStrength",
            term="clinical cohort evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.B},
            definition="Evidence derived from the clinical study of a participant cohort",
        ),
        ViccConceptVocab(
            id="vicc:e000006",
            domain="EvidenceStrength",
            term="interventional study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
            definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)",
        ),
        ViccConceptVocab(
            id="vicc:e000007",
            domain="EvidenceStrength",
            term="observational study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
            definition="Evidence derived from observational studies of clinical cohorts",
        ),
        ViccConceptVocab(
            id="vicc:e000008",
            domain="EvidenceStrength",
            term="case study evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.C},
            definition="Evidence derived from clinical study of a single participant",
        ),
        ViccConceptVocab(
            id="vicc:e000009",
            domain="EvidenceStrength",
            term="preclinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
            definition="Evidence derived from the study of model organisms",
        ),
        ViccConceptVocab(
            id="vicc:e000010",
            domain="EvidenceStrength",
            term="inferential evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
            definition="Evidence derived by inference",
        ),
    ]

    def __init__(
        self,
        data_dir: Path | None = None,
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize Transformer base class.

        :param data_dir: Path to source data directory. If not given, use a subdirectory
            off of the MetaKB data directory as configured in the ``metakb.config`` module.
        :param harvester_path: Path to previously harvested data
        :param normalizers: normalizer collection instance
        """
        self._cache = self._create_cache()
        self.name = self.__class__.__name__.lower().split("transformer")[0]
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = get_config().data_dir / self.name
        self.harvester_path = harvester_path
        self.vicc_normalizers = (
            ViccNormalizers() if normalizers is None else normalizers
        )
        self.processed_data = TransformedData()
        self.evidence_level_to_vicc_concept_mapping = (
            self._evidence_level_to_vicc_concept_mapping()
        )

    @abstractmethod
    async def transform(self, *args, **kwargs) -> None:  # noqa: ANN002
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """

    @abstractmethod
    def _create_cache() -> _CacheType:
        """Create cache for transformed records"""

    def extract_harvested_data(self) -> _HarvestedData:
        """Get harvested data from file.

        :return: Harvested data
        """
        if self.harvester_path is None:
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            default_fname = f"{self.name}_harvester_{today}.json"
            default_path = self.data_dir / "harvester" / default_fname
            if not default_path.exists():
                msg = f"Unable to open harvest file under default filename: {default_path.absolute().as_uri()}"
                raise FileNotFoundError(msg)
            self.harvester_path = default_path
        else:
            if not self.harvester_path.exists():
                msg = f"Unable to open harvester file: {self.harvester_path}"
                raise FileNotFoundError(msg)

        with self.harvester_path.open() as f:
            _harvested_data_child = _HarvestedData.get_subclass_by_prefix(self.name)
            return _harvested_data_child(**json.load(f))

    def _evidence_level_to_vicc_concept_mapping(
        self,
    ) -> dict[MoaEvidenceLevel | CivicEvidenceLevel, list[ConceptMapping]]:
        """Get mapping of source evidence level to vicc concept vocab

        :return: Dictionary containing mapping from source evidence level (key)
            to corresponding vicc concept vocab (value) represented as a list of
            ConceptMapping
        """
        concept_mappings: dict[str, list[ConceptMapping]] = {}
        for item in self._vicc_concept_vocabs:
            for exact_mapping in item.exact_mappings:
                concept_mappings[exact_mapping] = [
                    ConceptMapping(
                        coding=Coding(
                            system="https://go.osu.edu/evidence-codes",
                            code=item.id.split("vicc:")[-1],
                            name=item.term,
                        ),
                        relation=Relation.EXACT_MATCH,
                    )
                ]
        return concept_mappings

    @staticmethod
    def _get_digest_for_str_lists(str_list: list[str]) -> str:
        """Create digest for a list of strings

        :param str_list: List of strings to get digest for
        :return: Digest
        """
        str_list.sort()
        blob = json.dumps(str_list, separators=(",", ":"), sort_keys=True).encode(
            "ascii"
        )
        return sha512t24u(blob)

    @staticmethod
    def _get_vicc_normalizer_failure_ext() -> Extension:
        """Return extension for a VICC normalizer failure

        :return: Extension for VICC normalizer failure
        """
        return Extension(name=NormalizerExtensionName.FAILURE.value, value=True)

    @staticmethod
    def _get_vicc_normalizer_mappings(
        normalized_id: str,
        normalizer_resp: NormalizedDisease | NormalizedTherapy | NormalizedGene,
    ) -> list[ConceptMapping]:
        """Get VICC Normalizer mappable concept

        :param normalized_id: Normalized ID from VICC normalizer
        :param normalizer_resp: Response from VICC normalizer
        :return: List of VICC Normalizer data represented as mappable concept
        """

        def _update_mapping(
            mapping: ConceptMapping,
            normalized_id: str,
            normalizer_label: str,
            match_on_coding_id: bool = True,
        ) -> Extension:
            """Update ``mapping`` to include extension on whether ``mapping`` contains
            code that matches the merged record's primary identifier.

            :param mapping: ConceptMapping from vicc normalizer. This will be mutated.
                Extensions will be added. Label will be added if mapping identifier
                matches normalized merged identifier.
            :param normalized_id: Concept ID from normalized record
            :param normalizer_label: Label from normalized record
            :param match_on_coding_id: Whether to match on ``coding.id`` or
                ``coding.code`` (MONDO is represented differently)
            :return: ConceptMapping with normalizer extension added as well as name (
                if mapping id matches normalized merged id)
            """
            is_priority = (
                normalized_id == mapping.coding.id
                if match_on_coding_id
                else normalized_id == mapping.coding.code.root.lower()
            )

            merged_id_ext = Extension(
                name=NormalizerExtensionName.PRIORITY.value, value=is_priority
            )
            if mapping.extensions:
                mapping.extensions.append(merged_id_ext)
            else:
                mapping.extensions = [merged_id_ext]

            if is_priority:
                mapping.coding.name = normalizer_label

            return mapping

        mappings: list[ConceptMapping] = []
        attr_name = NORMALIZER_INSTANCE_TO_ATTR[type(normalizer_resp)]
        normalizer_resp_obj = getattr(normalizer_resp, attr_name)
        normalizer_label = normalizer_resp_obj.name
        is_disease = isinstance(normalizer_resp, NormalizedDisease)
        is_gene = isinstance(normalizer_resp, NormalizedGene)
        is_therapy = isinstance(normalizer_resp, NormalizedTherapy)

        normalizer_mappings = [
            ConceptMapping(
                coding=normalizer_resp_obj.primaryCoding,
                relation=Relation.EXACT_MATCH,
            ),
        ]
        if normalizer_resp_obj.mappings:
            normalizer_mappings.extend(normalizer_resp_obj.mappings)

        for mapping in normalizer_mappings:
            if normalized_id == mapping.coding.id:
                mappings.append(
                    _update_mapping(
                        mapping,
                        normalized_id,
                        normalizer_label,
                        match_on_coding_id=True,
                    )
                )
            else:
                if is_disease and mapping.coding.code.root.lower().startswith(
                    DiseaseNamespacePrefix.MONDO.value
                ):
                    mappings.append(
                        _update_mapping(
                            mapping,
                            normalized_id,
                            normalizer_label,
                            match_on_coding_id=False,
                        )
                    )
                else:
                    if (
                        (
                            is_gene
                            and mapping.coding.id.startswith(
                                (
                                    GeneNamespacePrefix.NCBI.value,
                                    GeneNamespacePrefix.HGNC.value,
                                )
                            )
                        )
                        or (
                            is_disease
                            and mapping.coding.id.startswith(
                                DiseaseNamespacePrefix.DOID.value
                            )
                        )
                        or (
                            is_therapy
                            and mapping.coding.id.startswith(
                                TherapyNamespacePrefix.NCIT.value
                            )
                        )
                    ):
                        mappings.append(
                            _update_mapping(
                                mapping,
                                normalized_id,
                                normalizer_label,
                                match_on_coding_id=True,
                            )
                        )
        return mappings

    def _merge_mappings(
        self,
        source_mappings: list[ConceptMapping],
        normalizer_mappings: list[ConceptMapping],
    ) -> list[ConceptMapping]:
        """Merge source and normalizer concept mappings

        Source mappings will be annotated with source annotation extension to retain
        provenance of original source mapping.

        :param source_mappings: List of concept mappings directly from a source
        :param normalizer_mappings: List of concept mappings from VICC normalizer
        :return: A list of merged concept mappings
        """
        merged_mappings = normalizer_mappings.copy()
        code_to_idx = {m.coding.code.root: idx for idx, m in enumerate(merged_mappings)}
        source_anno_exts = [Extension(name=f"{self.name}_annotation", value=True)]

        for source_mapping in source_mappings:
            code = source_mapping.coding.code.root
            idx = code_to_idx.get(code)

            base_mapping = merged_mappings[idx] if idx is not None else source_mapping
            extensions = (base_mapping.extensions or []) + source_anno_exts

            updated_mapping = base_mapping.model_copy(update={"extensions": extensions})

            if idx is not None:
                merged_mappings[idx] = updated_mapping
            else:
                code_to_idx[code] = len(merged_mappings)
                merged_mappings.append(updated_mapping)
        return merged_mappings

    def create_json(self, cdm_filepath: Path | None = None) -> None:
        """Create a composite JSON for transformed data.

        :param cdm_filepath: Path to the JSON file locatio at which the CDM output will be
            saved. If not provided, will use the default path of
            ``<METAKB_DATA_DIR>/<src_name>/transformers/<src_name>_cdm_YYYYMMDD.json``,
            where ``<METAKB_DATA_DIR>`` is the configurable data root directory.
            See the :ref:`configuration <config-data-directory>` entry in the docs for more information.
        """
        if not cdm_filepath:
            transformers_dir = self.data_dir / "transformers"
            transformers_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            cdm_filepath = transformers_dir / f"{self.name}_cdm_{today}.json"

        cdm_filepath.parent.mkdir(parents=True, exist_ok=True)

        with cdm_filepath.open("w+") as f:
            json.dump(self.processed_data.model_dump(exclude_none=True), f, indent=2)
