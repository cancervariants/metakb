"""A module for the Transformer base class."""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar

from disease.schemas import (
    SYSTEM_URI_TO_NAMESPACE as DISEASE_SYSTEM_URI_TO_NAMESPACE,
)
from disease.schemas import (
    NamespacePrefix as DiseaseNamespacePrefix,
)
from disease.schemas import (
    NormalizationService as NormalizedDisease,
)
from ga4gh.cat_vrs.models import CategoricalVariant
from ga4gh.core import sha512t24u
from ga4gh.core.models import (
    Coding,
    ConceptMapping,
    Extension,
    MappableConcept,
    Relation,
    code,
)
from ga4gh.va_spec.aac_2017 import (
    VariantDiagnosticStudyStatement,
    VariantPrognosticStudyStatement,
    VariantTherapeuticResponseStudyStatement,
)
from ga4gh.va_spec.base import Document, Method, TherapyGroup
from ga4gh.vrs.models import Allele
from gene.schemas import NormalizeService as NormalizedGene
from pydantic import BaseModel, Field, StrictStr, ValidationError
from therapy.schemas import NormalizationService as NormalizedTherapy

from metakb import APP_ROOT, DATE_FMT
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import (
    ViccNormalizers,
)
from metakb.schemas.app import SourceName

logger = logging.getLogger(__name__)

# Normalizer response type to attribute name
NORMALIZER_INSTANCE_TO_ATTR = {
    NormalizedDisease: "disease",
    NormalizedTherapy: "therapy",
    NormalizedGene: "gene",
}

# Normalizer priority extension name
NORMALIZER_PRIORITY_EXT_NAME = "vicc_normalizer_priority"


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


class TherapyType(str, Enum):
    """Define types for supported therapies"""

    THERAPY = "Therapy"
    THERAPEUTIC_SUBSTITUTE_GROUP = "TherapeuticSubstituteGroup"
    COMBINATION_THERAPY = "CombinationTherapy"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: list[StrictStr] = []
    exact_mappings: set[CivicEvidenceLevel | MoaEvidenceLevel | EcoLevel] = set()
    definition: StrictStr


class TransformedData(BaseModel):
    """Define model for transformed data"""

    statements_evidence: list[
        VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = Field([], description="Statement objects for evidence records")
    statements_assertions: list[
        VariantTherapeuticResponseStudyStatement
        | VariantPrognosticStudyStatement
        | VariantDiagnosticStudyStatement
    ] = Field([], description="Statement objects for assertion records")
    categorical_variants: list[CategoricalVariant] = []
    variations: list[Allele] = []
    genes: list[MappableConcept] = []
    therapies: list[MappableConcept | TherapyGroup] = []
    conditions: list[MappableConcept] = []
    methods: list[Method] = []
    documents: list[Document] = []


class Transformer(ABC):
    """A base class for transforming harvester data."""

    _methods: ClassVar[list[Method]] = [
        Method(
            id=MethodId.CIVIC_EID_SOP,
            label="CIViC Curation SOP (2019)",
            reportedIn=Document(
                label="Danos et al., 2019, Genome Med.",
                title="Standard operating procedure for curation and clinical interpretation of variants in cancer",
                doi="10.1186/s13073-019-0687-x",
                pmid=31779674,
            ),
            subtype=MappableConcept(
                primaryCode="variant curation standard operating procedure"
            ),
        ),
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            label="MOAlmanac (2021)",
            reportedIn=Document(
                label="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",
                doi="10.1038/s43018-021-00243-3",
                pmid=35121878,
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
        data_dir: Path = APP_ROOT / "data",
        harvester_path: Path | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize Transformer base class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param ViccNormalizers normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transformer")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

        self.vicc_normalizers = (
            ViccNormalizers() if normalizers is None else normalizers
        )

        self.processed_data = TransformedData()

        # Cache for concepts that were unable to normalize. Set of source concept IDs
        self.able_to_normalize = {}
        self.unable_to_normalize = {
            "conditions": set(),
            "therapies": set(),
        }

        self.evidence_level_to_vicc_concept_mapping = (
            self._evidence_level_to_vicc_concept_mapping()
        )

    @abstractmethod
    async def transform(self, harvested_data: _HarvestedData) -> None:
        """Transform harvested data to the Common Data Model.

        :param harvested_data: Source harvested data
        """

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
    ) -> dict[MoaEvidenceLevel | CivicEvidenceLevel, MappableConcept]:
        """Get mapping of source evidence level to vicc concept vocab

        :return: Dictionary containing mapping from source evidence level (key)
            to corresponding vicc concept vocab (value) represented as MappableConcept
            object
        """

        def _get_concept_mapping(exact_mapping: str) -> ConceptMapping:
            """Get system for an exact mapping

            :param exact_mapping: Exact mapping code
            :raises NotImplementedError: If SourceName not supported yet
            :return: Concept mapping object
            """
            if isinstance(exact_mapping, EcoLevel):
                id_ = exact_mapping.value.lower()
                system = "https://www.evidenceontology.org/term/"
            elif isinstance(exact_mapping, CivicEvidenceLevel):
                system = (
                    "https://civic.readthedocs.io/en/latest/model/evidence/level.html"
                )
                id_ = f"{SourceName.CIVIC.value}.evidence_level:{exact_mapping.value}"
            elif isinstance(exact_mapping, MoaEvidenceLevel):
                system = "https://moalmanac.org/about"
                id_ = f"{SourceName.MOA.value}.assertion_level:{'_'.join(exact_mapping.value.lower().replace('-', '_').split())}"
            else:
                raise NotImplementedError

            return ConceptMapping(
                coding=Coding(id=id_, system=system, code=exact_mapping),
                relation=Relation.EXACT_MATCH,
            )

        mappings = {}
        for item in self._vicc_concept_vocabs:
            primary_code = item.id.split(":")[-1]
            for exact_mapping in item.exact_mappings:
                concept_mappings = [
                    ConceptMapping(
                        coding=Coding(
                            id=item.id,
                            system="https://go.osu.edu/evidence-codes",
                            label=item.term,
                            code=code(primary_code),
                        ),
                        relation=Relation.EXACT_MATCH,
                    )
                ]

                concept_mappings.extend(
                    _get_concept_mapping(exact_mapping_)
                    for exact_mapping_ in item.exact_mappings
                )

                mappings[exact_mapping] = MappableConcept(
                    label=item.term,
                    primaryCode=primary_code,
                    mappings=concept_mappings,
                )

        return mappings

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

    @abstractmethod
    def _get_therapy(self, therapy: dict) -> MappableConcept | None:
        """Get therapy mappable concept for source therapy object

        :param therapy: source therapy object
        :return: If able to normalize therapy, returns therapy mappable concept
        """

    @abstractmethod
    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
        therapy_interaction_type: str,
    ) -> TherapyGroup | None:
        """Get Therapeutic Substitute Group for therapies

        :param therapeutic_sub_group_id: ID for Therapeutic Substitute Group
        :param therapies: List of therapy objects
        :param therapy_interaction_type: Therapy interaction type
        :return: If able to normalize all therapy objects in `therapies`, returns
            Therapeutic Substitute Group
        """

    def _get_combination_therapy(
        self,
        combination_therapy_id: str,
        therapies_in: list[dict],
        therapy_interaction_type: str,
    ) -> TherapyGroup | None:
        """Get Combination Therapy representation for source therapies

        :param combination_therapy_id: ID for Combination Therapy
        :param therapies: List of source therapy objects
        :param therapy_interaction_type: Therapy type provided by source
        :return: If able to normalize all therapy objects in `therapies`, returns
            Combination Therapy
        """
        therapies = []
        source_name = type(self).__name__.lower().replace("transformer", "")

        for therapy in therapies_in:
            if source_name == SourceName.MOA:
                therapy_id = f"moa.therapy:{therapy}"
            else:
                therapy_id = f"civic.tid:{therapy['id']}"
            therapy_mc = self._add_therapy(
                therapy_id,
                [therapy],
                TherapyType.THERAPY,
            )
            if not therapy_mc:
                return None

            therapies.append(therapy_mc)

        extensions = [
            Extension(
                name="moa_therapy_type"
                if source_name == SourceName.MOA
                else "civic_therapy_interaction_type",
                value=therapy_interaction_type,
            )
        ]

        try:
            tg = TherapyGroup(
                id=combination_therapy_id,
                therapies=therapies,
                extensions=extensions,
                groupType=MappableConcept(label=TherapyType.COMBINATION_THERAPY.value),
            )
        except ValidationError as e:
            # if combination validation checks fail
            logger.debug(
                "ValidationError raised when attempting to create CombinationTherapy: %s",
                e,
            )
            tg = None

        return tg

    def _add_therapy(
        self,
        therapy_id: str,
        therapies: list[dict],
        therapy_type: TherapyType,
        therapy_interaction_type: str | None = None,
    ) -> MappableConcept | None:
        """Create or get therapy mappable concept given therapies
        First look in cache for existing therapy, if not found will attempt to
        normalize. Will add `therapy_id` to `therapies` and
        `able_to_normalize['therapies']` if therapy-normalizer is able to normalize all
        `therapies`. Else, will add the `therapy_id` to
        `unable_to_normalize['therapies']`

        :param therapy_id: ID for therapy
        :param therapies: List of therapy objects. If `therapy_type` is
            `TherapyType.THERAPY`, the list will only contain a single therapy.
        :param therapy_type: The type of therapy
        :param therapy_interaction_type: drug interaction type
        :return: Therapy mappable concept, if successful normalization
        """
        therapy = self.able_to_normalize["therapies"].get(therapy_id)
        if therapy:
            return therapy

        if therapy_id not in self.unable_to_normalize["therapies"]:
            if therapy_type == TherapyType.THERAPY:
                therapy = self._get_therapy(therapies[0])
            elif therapy_type == TherapyType.THERAPEUTIC_SUBSTITUTE_GROUP:
                therapy = self._get_therapeutic_substitute_group(
                    therapy_id, therapies, therapy_interaction_type
                )
            elif therapy_type == TherapyType.COMBINATION_THERAPY:
                therapy = self._get_combination_therapy(
                    therapy_id, therapies, therapy_interaction_type
                )
            else:
                # not supported
                return None

            if therapy:
                self.able_to_normalize["therapies"][therapy_id] = therapy
                self.processed_data.therapies.append(therapy)
            else:
                self.unable_to_normalize["therapies"].add(therapy_id)
        return therapy

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

        def _add_merged_id_ext(
            mapping: ConceptMapping,
            is_priority: bool,
            label: str | None = None,
        ) -> Extension:
            """Update ``mapping`` to include extension on whether mapping is from merged identifier

            :param mapping: ConceptMapping from vicc normalizer. This will be mutated.
            :param is_priority: ``True`` if concept mapping contains primaryCode that
                matches merged record primaryCode. ``False`` otherwise (meaning it comes
                from merged record mappings)
            :param label: Merged concept label, if found
            :return: ConceptMapping with normalizer extension added
            """
            merged_id_ext = Extension(
                name=NORMALIZER_PRIORITY_EXT_NAME, value=is_priority
            )
            if mapping.extensions:
                mapping.extensions.append(merged_id_ext)
            else:
                mapping.extensions = [merged_id_ext]

            if label:
                mapping.coding.label = label

            return mapping

        mappings: list[ConceptMapping] = []
        attr_name = NORMALIZER_INSTANCE_TO_ATTR[type(normalizer_resp)]
        normalizer_resp_obj = getattr(normalizer_resp, attr_name)
        normalizer_mappings = normalizer_resp_obj.mappings or []
        if isinstance(normalizer_resp, NormalizedDisease):
            for mapping in normalizer_mappings:
                if (
                    DISEASE_SYSTEM_URI_TO_NAMESPACE.get(mapping.coding.system)
                    == DiseaseNamespacePrefix.MONDO.value
                ):
                    mappings.append(_add_merged_id_ext(mapping, is_priority=False))
                else:
                    if normalized_id == mapping.coding.code.root:
                        mappings.append(
                            _add_merged_id_ext(
                                mapping,
                                label=normalizer_resp_obj.label,
                                is_priority=True,
                            )
                        )
        else:
            mappings.extend(
                _add_merged_id_ext(
                    mapping, label=normalizer_resp_obj.label, is_priority=True
                )
                for mapping in normalizer_mappings
                if normalized_id == mapping.coding.code.root
            )
        return mappings

    def create_json(self, cdm_filepath: Path | None = None) -> None:
        """Create a composite JSON for transformed data.

        :param cdm_filepath: Path to the JSON file where the CDM data will be
            stored. If not provided, will use the default path of
            ``<APP_ROOT>/data/<src_name>/transformers/<src_name>_cdm_YYYYMMDD.json``
        """
        if not cdm_filepath:
            transformers_dir = self.data_dir / "transformers"
            transformers_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.UTC), DATE_FMT
            )
            cdm_filepath = transformers_dir / f"{self.name}_cdm_{today}.json"

        with cdm_filepath.open("w+") as f:
            json.dump(self.processed_data.model_dump(exclude_none=True), f, indent=2)
