"""A module for the Transform base class."""

import datetime
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar

from disease.schemas import (
    NamespacePrefix as DiseaseNamespacePrefix,
)
from disease.schemas import (
    NormalizationService as NormalizedDisease,
)
from ga4gh.core import sha512t24u
from ga4gh.core.domain_models import (
    CombinationTherapy,
    Disease,
    Gene,
    TherapeuticAgent,
    TherapeuticSubstituteGroup,
)
from ga4gh.core.entity_models import Coding, Extension
from ga4gh.vrs.models import Allele
from pydantic import BaseModel, StrictStr, ValidationError
from therapy.schemas import NormalizationService as NormalizedTherapy

from metakb import APP_ROOT, DATE_FMT
from metakb.harvesters.base import _HarvestedData
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Document, Method
from metakb.schemas.app import SourceName
from metakb.schemas.categorical_variation import (
    ProteinSequenceConsequence,
)
from metakb.schemas.variation_statement import (
    VariantTherapeuticResponseStudy,
)

logger = logging.getLogger(__name__)


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

    A = "civic.evidence_level:A"
    B = "civic.evidence_level:B"
    C = "civic.evidence_level:C"
    D = "civic.evidence_level:D"
    E = "civic.evidence_level:E"


class MoaEvidenceLevel(str, Enum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "moa.evidence_level:fda_approved"
    GUIDELINE = "moa.evidence_level:guideline"
    CLINICAL_TRIAL = "moa.evidence_level:clinical_trial"
    CLINICAL_EVIDENCE = "moa.evidence_level:clinical_evidence"
    PRECLINICAL = "moa.evidence_level:preclinical_evidence"
    INFERENTIAL = "moa.evidence_level:inferential_evidence"


class TherapeuticProcedureType(str, Enum):
    """Define types for supported Therapeutic Procedures"""

    THERAPEUTIC_AGENT = "TherapeuticAgent"
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

    studies: list[VariantTherapeuticResponseStudy] = []
    categorical_variations: list[ProteinSequenceConsequence] = []
    variations: list[Allele] = []
    genes: list[Gene] = []
    therapeutic_procedures: list[
        TherapeuticAgent | TherapeuticSubstituteGroup | CombinationTherapy
    ] = []
    conditions: list[Disease] = []
    methods: list[Method] = []
    documents: list[Document] = []


class Transform(ABC):
    """A base class for transforming harvester data."""

    _methods: ClassVar[list[Method]] = [
        Method(
            id=MethodId.CIVIC_EID_SOP,
            label="CIViC Curation SOP (2019)",
            isReportedIn=Document(
                label="Danos et al., 2019, Genome Med.",
                title="Standard operating procedure for curation and clinical interpretation of variants in cancer",
                doi="10.1186/s13073-019-0687-x",
                pmid=31779674,
            ),
        ),
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            label="MOAlmanac (2021)",
            isReportedIn=Document(
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
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param ViccNormalizers normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
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
            "therapeutic_procedures": set(),
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
                datetime.datetime.now(tz=datetime.timezone.utc), DATE_FMT
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
    ) -> dict[MoaEvidenceLevel | CivicEvidenceLevel, Coding]:
        """Get mapping of source evidence level to vicc concept vocab

        :return: Dictionary containing mapping from source evidence level (key)
            to corresponding vicc concept vocab (value) represented as Coding object
        """
        mappings = {}
        for item in self._vicc_concept_vocabs:
            for exact_mapping in item.exact_mappings:
                mappings[exact_mapping] = Coding(
                    code=item.id.split(":")[-1],
                    label=item.term,
                    system="https://go.osu.edu/evidence-codes",
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
    def _get_therapeutic_agent(self, therapy: dict) -> TherapeuticAgent | None:
        """Get Therapeutic Agent representation for source therapy object

        :param therapy: source therapy object
        :return: If able to normalize therapy, returns therapeutic agent
        """

    @abstractmethod
    def _get_therapeutic_substitute_group(
        self,
        therapeutic_sub_group_id: str,
        therapies: list[dict],
        therapy_interaction_type: str,
    ) -> TherapeuticSubstituteGroup | None:
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
        therapies: list[dict],
        therapy_interaction_type: str,
    ) -> CombinationTherapy | None:
        """Get Combination Therapy representation for source therapies

        :param combination_therapy_id: ID for Combination Therapy
        :param therapies: List of source therapy objects
        :param therapy_interaction_type: Therapy type provided by source
        :return: If able to normalize all therapy objects in `therapies`, returns
            Combination Therapy
        """
        components = []
        source_name = type(self).__name__.lower().replace("transform", "")

        for therapy in therapies:
            if source_name == SourceName.MOA:
                therapeutic_procedure_id = f"moa.therapy:{therapy}"
            else:
                therapeutic_procedure_id = f"civic.tid:{therapy['id']}"
            ta = self._add_therapeutic_procedure(
                therapeutic_procedure_id,
                [therapy],
                TherapeuticProcedureType.THERAPEUTIC_AGENT,
            )
            if not ta:
                return None

            components.append(ta)

        extensions = [
            Extension(
                name="moa_therapy_type"
                if source_name == SourceName.MOA
                else "civic_therapy_interaction_type",
                value=therapy_interaction_type,
            )
        ]

        try:
            ct = CombinationTherapy(
                id=combination_therapy_id, components=components, extensions=extensions
            )
        except ValidationError as e:
            # if combination validation checks fail
            logger.debug(
                "ValidationError raised when attempting to create CombinationTherapy: %s",
                e,
            )
            ct = None

        return ct

    def _add_therapeutic_procedure(
        self,
        therapeutic_procedure_id: str,
        therapies: list[dict],
        therapeutic_procedure_type: TherapeuticProcedureType,
        therapy_interaction_type: str | None = None,
    ) -> TherapeuticAgent | TherapeuticSubstituteGroup | CombinationTherapy | None:
        """Create or get Therapeutic Procedure given therapies
        First look in cache for existing Therapeutic Procedure, if not found will
        attempt to normalize. Will add `therapeutic_procedure_id` to
        `therapeutic_procedures` and `able_to_normalize['therapeutic_procedures']` if
        therapy-normalizer is able to normalize all `therapies`. Else, will add the
        `therapeutic_procedure_id` to `unable_to_normalize['therapeutic_procedures']`

        :param therapeutic_procedure_id: ID for therapeutic procedure
        :param therapies: List of therapy objects. If `therapeutic_procedure_type`
            is `TherapeuticProcedureType.THERAPEUTIC_AGENT`, the list will only contain
            a single therapy.
        :param therapeutic_procedure_type: The type of therapeutic procedure
        :param therapy_interaction_type: drug interaction type
        :return: Therapeutic procedure, if successful normalization
        """
        tp = self.able_to_normalize["therapeutic_procedures"].get(
            therapeutic_procedure_id
        )
        if tp:
            return tp

        if (
            therapeutic_procedure_id
            not in self.unable_to_normalize["therapeutic_procedures"]
        ):
            if therapeutic_procedure_type == TherapeuticProcedureType.THERAPEUTIC_AGENT:
                tp = self._get_therapeutic_agent(therapies[0])
            elif (
                therapeutic_procedure_type
                == TherapeuticProcedureType.THERAPEUTIC_SUBSTITUTE_GROUP
            ):
                tp = self._get_therapeutic_substitute_group(
                    therapeutic_procedure_id, therapies, therapy_interaction_type
                )
            elif (
                therapeutic_procedure_type
                == TherapeuticProcedureType.COMBINATION_THERAPY
            ):
                tp = self._get_combination_therapy(
                    therapeutic_procedure_id, therapies, therapy_interaction_type
                )
            else:
                # not supported
                return None

            if tp:
                self.able_to_normalize["therapeutic_procedures"][
                    therapeutic_procedure_id
                ] = tp
                self.processed_data.therapeutic_procedures.append(tp)
            else:
                self.unable_to_normalize["therapeutic_procedures"].add(
                    therapeutic_procedure_id
                )
        return tp

    @staticmethod
    def _get_therapy_normalizer_ext_data(
        normalized_therapeutic_id: str, therapy_norm_resp: NormalizedTherapy
    ) -> Extension:
        """Create extension containing relevant therapy-normalizer data

        :param normalized_therapeutic_id: Concept ID from therapy-normalizer
        :param therapy_norm_resp: Matched response from therapy-normalizer
        :return: Extension containing therapy-normalizer data. Additional information,
            such as the label, is provided for VarCat.
        """
        return Extension(
            name="therapy_normalizer_data",
            value={
                "normalized_id": normalized_therapeutic_id,
                "label": therapy_norm_resp.therapeutic_agent.label,
            },
        )

    @staticmethod
    def _get_disease_normalizer_ext_data(
        normalized_disease_id: str, disease_norm_resp: NormalizedDisease
    ) -> Extension:
        """Create extension containing relevant disease-normalizer data

        :param normalized_disease_id: Concept ID from disease-normalizer
        :param disease_norm_resp: Matched response from disease-normalizer
        :return: Extension containing disease-normalizer data. Additional information,
            such as the label and mondo_id, is provided for VarCat.
        """
        mappings = disease_norm_resp.disease.mappings or []
        mondo_id = None
        for mapping in mappings:
            if mapping.coding.system == DiseaseNamespacePrefix.MONDO.value:
                mondo_id = mapping.coding.code
                break

        return Extension(
            name="disease_normalizer_data",
            value={
                "normalized_id": normalized_disease_id,
                "label": disease_norm_resp.disease.label,
                "mondo_id": mondo_id,
            },
        )

    def create_json(self, cdm_filepath: Path | None = None) -> None:
        """Create a composite JSON for transformed data.

        :param cdm_filepath: Path to the JSON file where the CDM data will be
            stored. If not provided, will use the default path of
            ``<APP_ROOT>/data/<src_name>/transform/<src_name>_cdm_YYYYMMDD.json``
        """
        if not cdm_filepath:
            transform_dir = self.data_dir / "transform"
            transform_dir.mkdir(exist_ok=True, parents=True)
            today = datetime.datetime.strftime(
                datetime.datetime.now(tz=datetime.timezone.utc), DATE_FMT
            )
            cdm_filepath = transform_dir / f"{self.name}_cdm_{today}.json"

        with cdm_filepath.open("w+") as f:
            json.dump(self.processed_data.model_dump(exclude_none=True), f, indent=2)
