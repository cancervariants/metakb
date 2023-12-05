"""A module for the Transform base class."""
from typing import Dict, Optional, List, Set, Union
import json
import logging
from pathlib import Path
from datetime import datetime as dt
from enum import StrEnum

from ga4gh.core import core_models, sha512t24u
from pydantic import BaseModel, StrictStr

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas.annotation import Method, Document
from metakb.normalizers import ViccNormalizers

logger = logging.getLogger(__name__)


class EcoLevel(StrEnum):
    """Define constraints for Evidence Ontology levels"""

    EVIDENCE = "ECO:0000000"
    CLINICAL_STUDY_EVIDENCE = "ECO:0000180"


class MethodId(StrEnum):
    """Create method id constants"""

    CIVIC_EID_SOP = "civic.method:2019"
    MOA_ASSERTION_BIORXIV = "moa.method:2021"


class CivicEvidenceLevel(StrEnum):
    """Define constraints for CIViC evidence levels"""

    A = "civic.evidence_level:A"
    B = "civic.evidence_level:B"
    C = "civic.evidence_level:C"
    D = "civic.evidence_level:D"
    E = "civic.evidence_level:E"


class MoaEvidenceLevel(StrEnum):
    """Define constraints MOAlmanac evidence levels"""

    FDA_APPROVED = "moa.evidence_level:fda_approved"
    GUIDELINE = "moa.evidence_level:guideline"
    CLINICAL_TRIAL = "moa.evidence_level:clinical_trial"
    CLINICAL_EVIDENCE = "moa.evidence_level:clinical_evidence"
    PRECLINICAL = "moa.evidence_level:preclinical_evidence"
    INFERENTIAL = "moa.evidence_level:inferential_evidence"


class ViccConceptVocab(BaseModel):
    """Define VICC Concept Vocab model"""

    id: StrictStr
    domain: StrictStr
    term: StrictStr
    parents: List[StrictStr] = []
    exact_mappings: Set[Union[CivicEvidenceLevel, MoaEvidenceLevel, EcoLevel]] = {}
    definition: StrictStr


class Transform:
    """A base class for transforming harvester data."""

    _methods: List[Method] = [
        Method(
            id=MethodId.CIVIC_EID_SOP,
            label="CIViC Curation SOP (2019)",
            isReportedIn=Document(
                label="Danos et al., 2019, Genome Med.",
                title="Standard operating procedure for curation and clinical interpretation of variants in cancer",  # noqa: E501
                doi="10.1186/s13073-019-0687-x",
                pmid=31779674
            )
        ).model_dump(exclude_none=True),
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV,
            label="MOAlmanac (2021)",
            isReportedIn=Document(
                label="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",  # noqa: E501
                doi="10.1038/s43018-021-00243-3",
                pmid=35121878
            )
        ).model_dump(exclude_none=True),
    ]
    methods_mapping = {m["id"]: m for m in _methods}

    _vicc_concept_vocabs: List[ViccConceptVocab] = [
        ViccConceptVocab(
            id="vicc:e000000",
            domain="EvidenceStrength",
            term="evidence",
            parents=[],
            exact_mappings={EcoLevel.EVIDENCE},
            definition="A type of information that is used to support statements."),
        ViccConceptVocab(
            id="vicc:e000001",
            domain="EvidenceStrength",
            term="authoritative evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.A},
            definition="Evidence derived from an authoritative source describing a proven or consensus statement."),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000002",
            domain="EvidenceStrength",
            term="FDA recognized evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.FDA_APPROVED},
            definition="Evidence derived from statements recognized by the US Food and Drug Administration."),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000003",
            domain="EvidenceStrength",
            term="professional guideline evidence",
            parents=["vicc:e000001"],
            exact_mappings={MoaEvidenceLevel.GUIDELINE},
            definition="Evidence derived from statements by professional society guidelines"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000004",
            domain="EvidenceStrength",
            term="clinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
            definition="Evidence derived from clinical research studies"),
        ViccConceptVocab(
            id="vicc:e000005",
            domain="EvidenceStrength",
            term="clinical cohort evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.B},
            definition="Evidence derived from the clinical study of a participant cohort"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000006",
            domain="EvidenceStrength",
            term="interventional study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
            definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000007",
            domain="EvidenceStrength",
            term="observational study evidence",
            parents=["vicc:e000005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
            definition="Evidence derived from observational studies of clinical cohorts"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e000008",
            domain="EvidenceStrength",
            term="case study evidence",
            parents=["vicc:e000004"],
            exact_mappings={CivicEvidenceLevel.C},
            definition="Evidence derived from clinical study of a single participant"),
        ViccConceptVocab(
            id="vicc:e000009",
            domain="EvidenceStrength",
            term="preclinical evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
            definition="Evidence derived from the study of model organisms"),
        ViccConceptVocab(
            id="vicc:e000010",
            domain="EvidenceStrength",
            term="inferential evidence",
            parents=["vicc:e000000"],
            exact_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
            definition="Evidence derived by inference")
    ]

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[ViccNormalizers] = None) -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param ViccNormalizers normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

        if normalizers is None:
            self.vicc_normalizers = ViccNormalizers()
        else:
            self.vicc_normalizers = normalizers

        self.studies = []
        self.molecular_profiles = []
        self.variations = []
        self.genes = []
        self.therapeutics = []
        self.diseases = []
        self.methods = []
        self.documents = []

        # Cache for concepts that were unable to normalize. Set of source concept IDs
        self.unable_to_normalize = {
            "diseases": set(),
            "therapeutics": set()
        }

        self.next_node_id = {}
        self.evidence_level_to_vicc_concept_mapping = self._evidence_level_to_vicc_concept_mapping()  # noqa: E501

    async def transform(self, *args, **kwargs):
        """Transform harvested data to the Common Data Model."""
        raise NotImplementedError

    def extract_harvester(self) -> Dict[str, List]:
        """Get harvested data from file.

        :return: Dict containing Lists of entries for each object type
        """
        if self.harvester_path is None:
            today = dt.strftime(dt.today(), DATE_FMT)
            default_fname = f"{self.name}_harvester_{today}.json"
            default_path = self.data_dir / "harvester" / default_fname
            if not default_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvest file under default filename: "
                    f"{default_path.absolute().as_uri()}"
                )
            self.harvester_path = default_path
        else:
            if not self.harvester_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvester file: {self.harvester_path}"
                )
        with open(self.harvester_path, "r") as f:
            return json.load(f)

    def _evidence_level_to_vicc_concept_mapping(self) -> Dict:
        """Get mapping of source evidence level to vicc concept vocab

        :return: Dictionary containing mapping from source evidence level (key)
            to corresponding vicc concept vocab (value) represented as Coding object
        """
        mappings = {}
        for item in self._vicc_concept_vocabs:
            for exact_mapping in item.exact_mappings:
                mappings[exact_mapping] = core_models.Coding(
                    code=item.id.split(":")[-1],
                    label=item.term,
                    system="https://go.osu.edu/evidence-codes"
                )
        return mappings

    @staticmethod
    def _get_digest_for_str_lists(str_list: List[str]) -> str:
        """Create digest for a list of strings

        :param List[str] str_list: List of strings to get digest for
        :return: Digest
        """
        str_list.sort()
        blob = json.dumps(str_list, separators=(",", ":")).encode("ascii")
        return sha512t24u(blob)

    def create_json(self, transform_dir: Optional[Path] = None,
                    filename: Optional[str] = None) -> None:
        """Create a composite JSON for transformed data.

        :param Optional[Path] transform_dir: Path to data directory for
            transformed data
        :param Optional[str] filename: Name of transformed file
        """
        if transform_dir is None:
            transform_dir = self.data_dir / "transform"
        transform_dir.mkdir(exist_ok=True, parents=True)

        composite_dict = {
            'studies': self.studies,
            'variations': self.variations,
            'molecular_profiles': self.molecular_profiles,
            'genes': self.genes,
            'therapeutics': self.therapeutics,
            'diseases': self.diseases,
            'methods': self.methods,
            'documents': self.documents
        }

        today = dt.strftime(dt.today(), DATE_FMT)
        if filename is None:
            filename = f"{self.name}_cdm_{today}.json"
        out = transform_dir / filename
        with open(out, 'w+') as f:
            json.dump(composite_dict, f, indent=4)
