"""A module for the Transform base class."""
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path
from datetime import datetime as dt

from ga4gh.core import sha512t24u

from metakb import APP_ROOT, DATE_FMT
from metakb.schemas import CivicEvidenceLevel, Document, EcoLevel, Method, MethodId, \
    MoaEvidenceLevel, TargetPropositionType, DiagnosticPredicate, \
    PrognosticPredicate, PredictivePredicate, FunctionalPredicate, \
    PathogenicPredicate, ViccConceptVocab
from metakb.normalizers import VICCNormalizers

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class Transform:
    """A base class for transforming harvester data."""

    _methods: List[Method] = [
        Method(
            id=MethodId.CIVIC_EID_SOP.value,
            is_reported_in=Document(
                xrefs=["pmid:31779674"],
                label="Danos AM, Krysiak K, Barnell EK, et al., 2019, Genome Medicine",
                title="Standard operating procedure for curation and clinical "
                      "interpretation of variants in cancer",
            ).dict(exclude_none=True),
            label="CIViC Curation SOP (2019)").dict(exclude_none=True),
        Method(
            id=MethodId.MOA_ASSERTION_BIORXIV.value,
            is_reported_in=Document(
                xrefs=["doi:10.1101/2020.09.22.308833"],
                # TODO: Check label
                label="Reardon, B., Moore, N.D., Moore, N. et al., 2020, bioRxiv",
                title="Clinical interpretation of integrative molecular profiles to "
                      "guide precision cancer medicine"
            ).dict(exclude_none=True)).dict(exclude_none=True)
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

        self.statements = list()
        self.propositions = list()
        self.variation_descriptors = list()
        self.gene_descriptors = list()
        self.therapeutic_descriptors = list()
        self.therapeutic_collection_descriptors = list()
        self.disease_descriptors = list()
        self.documents = list()
        self.methods = list()
        self.next_node_id = {}
        self.evidence_level_vicc_concept_mapping = self._evidence_level_to_vicc_concept_mapping()  # noqa: E501
        self.methods_mappping = {m["id"]: m for m in self._methods}

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
                    f"{default_path.absolute().as_uri()}")
            self.harvester_path = default_path
        else:
            if not self.harvester_path.exists():
                raise FileNotFoundError(
                    f"Unable to open harvester file: {self.harvester_path}")
        with open(self.harvester_path, "r") as f:
            return json.load(f)

    predicate_validation = {
        TargetPropositionType.VARIATION_NEOPLASM_THERAPEUTIC_RESPONSE: PredictivePredicate.__members__.values(),  # noqa: E501
        TargetPropositionType.PREDICTIVE: PredictivePredicate.__members__.values(),
        TargetPropositionType.DIAGNOSTIC: DiagnosticPredicate.__members__.values(),
        TargetPropositionType.PROGNOSTIC: PrognosticPredicate.__members__.values(),
        TargetPropositionType.PATHOGENIC: PathogenicPredicate.__members__.values(),
        TargetPropositionType.FUNCTIONAL: FunctionalPredicate.__members__.values()
    }

    def _sort_dict(self, params: Dict) -> Optional[Dict]:
        """Recursively sort original dictionary
        Assumes only dicts with values that are strings or lists

        :param any params: params to be sorted
        :return: At the end will return sorted dictionary
        """
        if params is None:
            return None

        if isinstance(params, str):
            return params

        if isinstance(params, dict):
            d = {k: self._sort_dict(params[k])
                 for k in params if not params[k] is None}
            return dict(sorted(d.items()))

        if isinstance(params, list):
            return sorted([self._sort_dict(o) for o in params], key=lambda x: x["id"])

    def _get_proposition_id(self, proposition_params: Dict) -> Optional[str]:
        """Retrieve stable ID for a proposition

        :param Dict proposition_params: Paramaters for proposition
        :return: proposition ID, or None if prop_type and pred conflict or
            if provided parameters cannot determine correct proposition ID
        """
        predicate = proposition_params["predicate"]
        proposition_type = proposition_params["type"]
        if predicate not in self.predicate_validation[proposition_type]:
            msg = f"{proposition_type} in query conflicts with {predicate}"
            logger.error(msg)
            raise ValueError(msg)

        sorted_params = self._sort_dict(proposition_params)
        blob = json.dumps(sorted_params, sort_keys=True,
                          separators=(",", ":")).encode("ascii")
        digest = sha512t24u(blob)
        return f"proposition:{digest}"

    def _evidence_level_to_vicc_concept_mapping(self) -> Dict:
        """Return source evidence level to vicc concept vocab mapping

        :return: Dictionary of evidence level to coding concept
        """
        mappings = dict()
        for item in self._vicc_evidence_vocabs:
            for exact_mapping in item.exact_mappings:
                mappings[exact_mapping] = {"id": item.id, "label": item.term,
                                           "type": "Coding"}
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
    def _get_digest_for_str_lists(l: List[str]) -> str:  # noqa: E741
        """Create digest for a list of strings

        :param List[str] l: List of strings to get digest for
        :return: Digest
        """
        l.sort()
        blob = json.dumps(l, separators=(",", ":")).encode("ascii")
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
            'propositions': self.propositions,
            'variation_descriptors': self.variation_descriptors,
            'gene_descriptors': self.gene_descriptors,
            'therapeutic_descriptors': self.therapeutic_descriptors,
            'therapeutic_collection_descriptors': self.therapeutic_collection_descriptors,  # noqa: E501
            'disease_descriptors': self.disease_descriptors,
            'methods': self.methods,
            'documents': self.documents
        }

        today = dt.strftime(dt.today(), DATE_FMT)
        if filename is None:
            filename = f"{self.name}_cdm_{today}.json"
        out = transform_dir / filename
        with open(out, 'w+') as f:
            json.dump(composite_dict, f, indent=4)
