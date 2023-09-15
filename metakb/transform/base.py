"""A module for the Transform base class."""
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from ga4gh.core import sha512t24u, core_models
from pydantic import StrictStr

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas.annotation import Method, Document
from metakb.schemas.app import ViccConceptVocab, MethodId, CivicEvidenceLevel, MoaEvidenceLevel, EcoLevel
from metakb.normalizers import  VICCNormalizers

logger = logging.getLogger(__name__)


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
            label="MOAlmanac (2021)",  # FIXME: Should this be something else?
            isReportedIn=Document(
                label="Reardon, B., Moore, N.D., Moore, N.S. et al.",
                title="Integrating molecular profiles into clinical frameworks through the Molecular Oncology Almanac to prospectively guide precision oncology",  # noqa: E501
                doi="10.1038/s43018-021-00243-3",
                pmid=35121878
            )
        ).model_dump(exclude_none=True),
    ]

    _vicc_evidence_vocabs: List[ViccConceptVocab] = [
        ViccConceptVocab(
            id="vicc:e00000",
            domain="Evidence",
            term="evidence",
            parents=[],
            exact_mappings={EcoLevel.EVIDENCE},
            definition="A type of information that is used to support statements."),
        ViccConceptVocab(
            id="vicc:e00001",
            domain="Evidence",
            term="authoritative evidence",
            parents=["e00000"],
            exact_mappings={CivicEvidenceLevel.A},
            definition="Evidence derived from an authoritative source describing a proven or consensus statement."),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00002",
            domain="Evidence",
            term="FDA recognized evidence",
            parents=["e00001"],
            exact_mappings={MoaEvidenceLevel.FDA_APPROVED},
            definition="Evidence derived from statements recognized by the US Food and Drug Administration."),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00003",
            domain="Evidence",
            term="professional guideline evidence",
            parents=["e00001"],
            exact_mappings={MoaEvidenceLevel.GUIDELINE},
            definition="Evidence derived from statements by professional society guidelines"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00004",
            domain="Evidence",
            term="clinical evidence",
            parents=["e00000"],
            exact_mappings={EcoLevel.CLINICAL_STUDY_EVIDENCE},
            definition="Evidence derived from clinical research studies"),
        ViccConceptVocab(
            id="vicc:e00005",
            domain="Evidence",
            term="clinical cohort evidence",
            parents=["e00004"],
            exact_mappings={CivicEvidenceLevel.B},
            definition="Evidence derived from the clinical study of a participant cohort"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00006",
            domain="Evidence",
            term="interventional study evidence",
            parents=["e00005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_TRIAL},
            definition="Evidence derived from interventional studies of clinical cohorts (clinical trials)"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00007",
            domain="Evidence",
            term="observational study evidence",
            parents=["e00005"],
            exact_mappings={MoaEvidenceLevel.CLINICAL_EVIDENCE},
            definition="Evidence derived from observational studies of clinical cohorts"),  # noqa: E501
        ViccConceptVocab(
            id="vicc:e00008",
            domain="Evidence",
            term="case study evidence",
            parents=["e00004"],
            exact_mappings={CivicEvidenceLevel.C},
            definition="Evidence derived from clinical study of a single participant"),
        ViccConceptVocab(
            id="vicc:e00009",
            domain="Evidence",
            term="preclinical evidence",
            parents=["e00000"],
            exact_mappings={CivicEvidenceLevel.D, MoaEvidenceLevel.PRECLINICAL},
            definition="Evidence derived from the study of model organisms"),
        ViccConceptVocab(
            id="vicc:e00010",
            domain="Evidence",
            term="inferential evidence",
            parents=["e00000"],
            exact_mappings={CivicEvidenceLevel.E, MoaEvidenceLevel.INFERENTIAL},
            definition="Evidence derived by inference")
    ]

    def __init__(self,
                 data_dir: Path = APP_ROOT / "data",
                 harvester_path: Optional[Path] = None,
                 normalizers: Optional[VICCNormalizers] = None) -> None:
        """Initialize Transform base class.

        :param Path data_dir: Path to source data directory
        :param Optional[Path] harvester_path: Path to previously harvested data
        :param VICCNormalizers normalizers: normalizer collection instance
        """
        self.name = self.__class__.__name__.lower().split("transform")[0]
        self.data_dir = data_dir / self.name
        self.harvester_path = harvester_path

        if normalizers is None:
            self.vicc_normalizers = VICCNormalizers()
        else:
            self.vicc_normalizers = normalizers

        self.statements = []
        self.molecular_profiles = []
        self.variations = []
        self.genes = []
        self.therapeutics = []
        self.diseases = []
        self.methods = []
        self.documents = []
        self.next_node_id = {}
        self.evidence_level_vicc_concept_mapping = self._evidence_level_to_vicc_concept_mapping()  # noqa: E501
        self.methods_mapping = {m["id"]: m for m in self._methods}

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
        """Return source evidence level to vicc concept vocab mapping

        :return: Dictionary of evidence level to coding concept
        """
        mappings = dict()
        for item in self._vicc_evidence_vocabs:
            for exact_mapping in item.exact_mappings:
                mappings[exact_mapping] = core_models.Coding(
                    code=item.id.split(":")[-1],
                    label=item.term,
                    system="https://go.osu.edu/evidence-codes"
                )
        return mappings

    @staticmethod
    def _get_document_id(**parameters) -> str:
        """Retrieve stable ID for a document.
        :parameters: property names and values to get ID for. Assumes values
            are strings.
        :return: identifying document ID value
        """
        params_sorted = {
            key.lower(): parameters[key].lower() for key in sorted(parameters)
        }
        blob = json.dumps(params_sorted).encode("ascii")
        return f"document:{sha512t24u(blob=blob)}"

    @staticmethod
    def _get_digest_for_str_lists(str_list: List[str]) -> str:  # noqa: E741
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
            'statements': self.statements,
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
