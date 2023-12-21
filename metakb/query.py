"""Module for queries."""
import json
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

from ga4gh.core import core_models
from ga4gh.vrs import models
from neo4j import Transaction
from neo4j.graph import Node

from metakb.database import Graph
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Document, Method
from metakb.schemas.api import SearchIdService, SearchStudiesService, ServiceMeta
from metakb.schemas.categorical_variation import CategoricalVariation
from metakb.schemas.variation_statement import (
    VariantTherapeuticResponseStudy,
    _VariantOncogenicityStudyQualifier,
)

logger = logging.getLogger(__name__)


class QueryHandler:
    """Class for handling queries."""

    def __init__(self, uri: str = "",
                 creds: Tuple[str, str] = ("", ""),
                 normalizers: ViccNormalizers = ViccNormalizers()) -> None:
        """Initialize neo4j driver and the VICC normalizers.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        :param ViccNormalizers normalizers: normalizer collection instance
        """
        self.driver = Graph(uri, creds).driver
        self.vicc_normalizers = normalizers

    def get_normalized_therapy(self, therapy: str,
                               warnings: List[str]) -> Optional[str]:
        """Get normalized therapy concept.

        :param str therapy: Therapy query
        :param List[str] warnings: A list of warnings for the search query
        :return: A normalized therapy concept if it exists
        """
        _, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy([therapy])

        if not normalized_therapy_id:
            warnings.append(f"Therapy Normalizer unable to normalize: "
                            f"{therapy}")
        return normalized_therapy_id

    def get_normalized_disease(self, disease: str,
                               warnings: List[str]) -> Optional[str]:
        """Get normalized disease concept.

        :param str disease: Disease query
        :param List[str] warnings: A list of warnings for the search query
        :return: A normalized disease concept if it exists
        """
        _, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease([disease])

        if not normalized_disease_id:
            warnings.append(f"Disease Normalizer unable to normalize: "
                            f"{disease}")
        return normalized_disease_id

    async def get_normalized_variation(self, variation: str,
                                       warnings: List[str]) -> Optional[str]:
        """Get normalized variation concept.

        :param str variation: Variation query
        :param List[str] warnings: A list of warnings for the search query
        :return: A normalized variant concept if it exists
        """
        variant_norm_resp = \
            await self.vicc_normalizers.normalize_variation([variation])
        normalized_variation = variant_norm_resp.id if variant_norm_resp else None

        if not normalized_variation:
            # Check if VRS variation (allele, copy number change, copy number count)
            if variation.startswith(("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")):
                normalized_variation = variation
            else:
                warnings.append(f"Variation Normalizer unable to normalize: "
                                f"{variation}")
        return normalized_variation

    def get_normalized_gene(self, gene: str,
                            warnings: List[str]) -> Optional[str]:
        """Get normalized gene concept.

        :param str gene: Gene query
        :param List[str] warnings: A list of warnings for the search query.
        :return: A normalized gene concept if it exists
        """
        _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
        if not normalized_gene_id:
            warnings.append(f"Gene Normalizer unable to normalize: {gene}")
        return normalized_gene_id

    async def get_normalized_terms(
        self, variation: Optional[str], disease: Optional[str],
        therapy: Optional[str], gene: Optional[str],
        study_id: Optional[str], response: Dict
    ) -> Optional[Tuple]:
        """Find normalized terms for queried concepts.

        :param Optional[str] variation: Variation (subject) query
        :param Optional[str] disease: Disease (object_qualifier) query
        :param Optional[str] therapy: Therapy (object) query
        :param Optional[str] gene: Gene query
        :param Optional[str] study_id: Study ID query
        :param Dict response: The response for the query
        :return: A tuple containing the normalized concepts
        """
        if not (variation or disease or therapy or gene or study_id):
            response["warnings"].append("No parameters were entered.")
            return None

        # Find normalized terms using VICC normalizers
        if therapy:
            response["query"]["therapy"] = therapy
            normalized_therapy = \
                self.get_normalized_therapy(therapy.strip(),
                                            response["warnings"])
        else:
            normalized_therapy = None
        if disease:
            response["query"]["disease"] = disease
            normalized_disease = \
                self.get_normalized_disease(disease.strip(),
                                            response["warnings"])
        else:
            normalized_disease = None
        if variation:
            response["query"]["variation"] = variation
            normalized_variation = \
                await self.get_normalized_variation(variation, response["warnings"])
        else:
            normalized_variation = None
        if gene:
            response["query"]["gene"] = gene
            normalized_gene = self.get_normalized_gene(gene,
                                                       response["warnings"])
        else:
            normalized_gene = None

        # Check that queried study_id is valid
        valid_study_id = None
        study = None
        if study_id:
            response["query"]["study_id"] = study_id
            with self.driver.session() as session:
                study = session.read_transaction(
                    self._get_study_by_id, study_id
                )
                if study:
                    valid_study_id = study.get("id")
                else:
                    response["warnings"].append(
                        f"Study: {study_id} does not exist.")

        # If queried concept is given check that it is normalized / valid
        if (variation and not normalized_variation) or \
                (therapy and not normalized_therapy) or \
                (disease and not normalized_disease) or \
                (gene and not normalized_gene) or \
                (study_id and not valid_study_id):
            return None

        return (normalized_variation, normalized_disease, normalized_therapy,
                normalized_gene, study, valid_study_id)

    async def search_studies(
        self, variation: Optional[str] = None, disease: Optional[str] = None,
        therapy: Optional[str] = None, gene: Optional[str] = None,
        study_id: Optional[str] = None, detail: bool = False
    ) -> SearchStudiesService:
        """Get studies from queried concepts.

        :param variation: Variation query
        :param disease: Disease query
        :param therapy: Therapy query
        :param gene: Gene query
        :param study_id: Study ID query
        :param detail: Whether or not to display all genes, variations, therapeutic
            procedures, conditions, methods, and documents
        :return: SearchStudiesService response
        """
        response: Dict = {
            "query": {
                "variation": None,
                "disease": None,
                "therapy": None,
                "gene": None,
                "study_id": None,
                "detail": detail
            },
            "warnings": [],
            "matches": {
                "study_ids": []
            },
            "studies": [],
            "service_meta_": ServiceMeta()
        }

        normalized_terms = await self.get_normalized_terms(
            variation, disease, therapy, gene, study_id, response)

        if normalized_terms is None:
            return SearchStudiesService(**response)

        (normalized_variation, normalized_disease,
         normalized_therapy, normalized_gene, study,
         valid_study_id) = normalized_terms

        with self.driver.session() as session:
            if valid_study_id:
                study_nodes = [study]
                response["matches"]["study_ids"].append(study["id"])
            else:
                study_nodes = self._get_related_studies(
                    session,
                    normalized_variation,
                    normalized_therapy,
                    normalized_disease,
                    normalized_gene
                )

            response["studies"] = self._get_studies_response(session, study_nodes)

        return SearchStudiesService(**response)

    def search_by_id(self, node_id: str) -> SearchIdService:
        """Get node information given id query

        :param node_id: Node's ID query
        :return: SearchIdService response
        """
        valid_node_id = None
        response = {
            "query": node_id,
            "warnings": [],
            "service_meta_": ServiceMeta().dict()
        }

        node_id = node_id.strip()

        if not node_id:
            response["warnings"].append("Cannot enter empty string.")
        else:
            if "%" not in node_id and ":" in node_id:
                concept_name = quote(node_id.split(":", 1)[1])
                node_id = \
                    f"{node_id.split(':', 1)[0]}" \
                    f":{concept_name}"
            with self.driver.session() as session:
                node = session.read_transaction(
                    self._find_node_by_id, node_id
                )
                if node:
                    valid_node_id = node.get("id")
                else:
                    response["warnings"].append(f"Node: {node_id} "
                                                f"does not exist.")
        if (not node_id and not valid_node_id) or \
                (node_id and not valid_node_id):
            return SearchIdService(**response)

        response["node"] = node
        response["node_labels"] = node.labels
        return SearchIdService(**response)

    @staticmethod
    def _find_node_by_id(tx: Transaction, node_id: str) -> Optional[Node]:
        """Find a node by its ID.

        :param tx: Neo4j session transaction object
        :param node_id: ID of node to retrieve
        :return: Node object if successful
        """
        query = (
            "MATCH (n) "
            f"WHERE toLower(n.id) = toLower('{node_id}') "
            "RETURN n"
        )
        return (tx.run(query).single() or [None])[0]

    @staticmethod
    def _get_study_by_id(tx: Transaction, study_id: str) -> Optional[Node]:
        """Get a Study node by ID.

        :param tx: Neo4j session transaction object
        :param statement_id: Study ID to retrieve
        :return: Study node if successful
        """
        query = (
            "MATCH (s:Study) "
            f"WHERE toLower(s.id) = toLower('{study_id}') "
            "RETURN s"
        )
        return (tx.run(query).single() or [None])[0]

    def _get_studies_response(
        self,
        tx: Transaction,
        study_nodes: List[Node]
    ) -> List[Dict]:
        """Return a list of studies.

        :param study_nodes: A list of Study Nodes
        :return: A list of dicts containing study response output
        """
        studies_response = []
        added_studies = set()
        for s in study_nodes:
            s_id = s.get("id")
            if s_id not in added_studies:
                study_dict = self._get_study(tx, s)
                if study_dict:
                    studies_response.append(study_dict)
                    added_studies.add(s_id)

        return studies_response

    def _get_study(self, tx: Transaction, s: Node) -> Dict:
        """Return a study.

        :param Node s: Study Node
        :return: Dict containing values from `s`
        """
        # Only support VariantTherapeuticResponseStudy for now
        if "VariantTherapeuticResponseStudy" != s["type"]:
            return {}

        params = {
            "tumorType": None,
            "variant": None,
            "strength": None,
            "isReportedIn": [],
            "specifiedBy": None
        }
        params.update(s)
        study_id = s["id"]

        query = f"""
        MATCH (s:Study {{ id:'{study_id}' }})
        OPTIONAL MATCH (s)-[r]-(n)
        RETURN type(r) as r_type, n;
        """
        nodes_and_rels = tx.run(query).data()

        for item in nodes_and_rels:
            rel_type = item["r_type"]
            node = item["n"]
            if rel_type == "HAS_TUMOR_TYPE":
                node["mappings"] = json.loads(node["mappings"])
                node["extensions"] = [
                    core_models.Extension(
                        name="disease_normalizer_id",
                        value=node["disease_normalizer_id"]
                    )
                ]
                params["tumorType"] = core_models.Disease(**node)
            elif rel_type == "HAS_VARIANT":
                node["mappings"] = json.loads(node["mappings"])
                node["definingContext"] = self._get_defining_context(
                    tx, node["id"]
                ).model_dump()
                params["members"] = self._get_variation_members(tx, node["id"])
                params["variant"] = CategoricalVariation(**node)
            elif rel_type == "HAS_GENE_CONTEXT":
                params["qualifiers"] = _VariantOncogenicityStudyQualifier(
                    alleleOrigin=s.get("alleleOrigin"),
                    geneContext=self._get_gene_context(tx, study_id)
                )
            elif rel_type == "IS_SPECIFIED_BY":
                node["isReportedIn"] = self._get_method_document(tx, node["id"])
                params["method"] = Method(**node)
            elif rel_type == "IS_REPORTED_IN":
                params["isReportedIn"].append(Document(**node))
            elif rel_type == "HAS_STRENGTH":
                params["strength"] = core_models.Coding(**node)
            elif rel_type == "HAS_THERAPEUTIC":
                node_type = node["type"]
                if node_type == "CombinationTherapy":
                    node["components"] = self._get_components(tx, node["id"])
                    params["therapeutic"] = core_models.TherapeuticProcedure(**node)
                elif node_type == "TherapeuticSubstituteGroup":
                    node["substitutes"] = self._get_substitutes(tx, node["id"])
                    params["therapeutic"] = core_models.TherapeuticProcedure(**node)
                elif node_type == "TherapeuticAgent":
                    params["therapeutic"] = self._get_ta(node)

        return VariantTherapeuticResponseStudy(**params).model_dump()

    @staticmethod
    def _get_ta(ta_params: Dict):
        mappings = ta_params.get("mappings")
        if mappings:
            ta_params["mappings"] = json.loads(mappings)
        extensions = [
            core_models.Extension(
                name="therapy_normalizer_id",
                value=ta_params["therapy_normalizer_id"]
            )
        ]
        regulatory_approval = ta_params.get("regulatory_approval")
        if regulatory_approval:
            regulatory_approval = json.loads(regulatory_approval)
            extensions.append(
                core_models.Extension(
                    name="regulatory_approval",
                    value=regulatory_approval
                )
            )

        ta_params["extensions"] = extensions
        return core_models.TherapeuticAgent(**ta_params)

    def _get_components(self, tx: Transaction, combination_id: str):
        components = []
        query = f"""
        MATCH (tp:CombinationTherapy {{ id: '{combination_id}' }}) -[:HAS_COMPONENTS]
            -> (ta:TherapeuticAgent)
        RETURN ta
        """
        results = tx.run(query)
        for r in results:
            r_params = r.data()
            ta_params = r_params["ta"]
            ta = self._get_ta(ta_params)
            components.append(ta)
        return components

    def _get_substitutes(self, tx: Transaction, substitutes_id: str):
        substitutes = []
        query = f"""
        MATCH (tp: TherapeuticSubstituteGroup {{ id: '{substitutes_id}' }})
            -[:HAS_SUBSTITUTES] -> (ta:TherapeuticAgent)
        RETURN ta
        """
        results = tx.run(query)
        for r in results:
            r_params = r.data()
            ta_params = r_params["ta"]
            ta = self._get_ta(ta_params)
            substitutes.append(ta)
        return substitutes

    @staticmethod
    def _get_variation_members(tx: Transaction, cv_id: str) -> models.Variation:
        query = f"""
        MATCH (v:Variation) <- [:HAS_MEMBERS] - (cv:CategoricalVariation
            {{ id: '{cv_id}' }})
        MATCH (loc:Location) <- [:HAS_LOCATION] - (v)
        RETURN v, loc
        """
        results = tx.run(query)
        members = []
        for r in results:
            r_params = r.data()
            v_params = r_params["v"]
            v_params["state"] = json.loads(v_params["state"])
            v_params["location"] = r_params["loc"]
            members.append(models.Variation(**v_params).model_dump())
        return members

    @staticmethod
    def _get_defining_context(tx: Transaction, cv_id: str) -> models.Variation:
        query = f"""
        MATCH (v:Variation) <- [:HAS_DEFINING_CONTEXT] - (cv:CategoricalVariation
            {{ id: '{cv_id}' }})
        MATCH (loc:Location) <- [:HAS_LOCATION] - (v)
        RETURN v, loc
        """
        v_loc_params = tx.run(query).single().data()

        v_params = v_loc_params["v"]
        v_params["state"] = json.loads(v_params["state"])
        v_params["location"] = v_loc_params["loc"]
        return models.Variation(**v_params)

    @staticmethod
    def _get_method_document(tx: Transaction, method_id: str) -> Document:
        query = f"""
        MATCH (m:Method {{ id: '{method_id}' }}) -[:IS_REPORTED_IN] -> (d:Document)
        RETURN d
        """
        doc_params = tx.run(query).single().data()["d"]
        return Document(**doc_params)

    @staticmethod
    def _get_gene_context(
        tx: Transaction,
        study_id: str,
    ) -> core_models.Gene:
        query = f"""
        MATCH (s:Study {{ id: '{study_id}' }}) -[:HAS_GENE_CONTEXT] -> (g:Gene)
        RETURN g
        """
        gene_params = tx.run(query).single().data()["g"]

        mappings = gene_params.get("mappings")
        if mappings:
            gene_params["mappings"] = json.loads(mappings)

        gene_params["extensions"] = [
            core_models.Extension(
                name="gene_normalizer_id",
                value=gene_params["gene_normalizer_id"]
            )
        ]

        return core_models.Gene(**gene_params)

    @staticmethod
    def _get_related_studies(
        tx: Transaction,
        normalized_variation: str = "",
        normalized_therapy: str = "",
        normalized_disease: str = "",
        normalized_gene: str = ""
    ) -> List[Node]:
        """Get studies that contain normalized concepts queried

        :param tx: Neo4j session transaction object
        :param normalized_variation: variation VRS ID
        :param normalized_therapy: normalized therapy concept ID
        :param normalized_disease: normalized disease concept ID
        :param normalized_gene: normalized gene concept ID
        :return: List of Study nodes matching given parameters
        """
        query = "MATCH (s:Study)"
        params: Dict[str, str] = {}

        if normalized_variation:
            # TODO: Should we handle HAS_MEMBERS relationship?
            query += """
            MATCH (s) -[:HAS_VARIANT] -> (cv:CategoricalVariation)
            MATCH (cv) -[:HAS_DEFINING_CONTEXT] -> (v:Variation {id:$v_id})
            """
            params["v_id"] = normalized_variation

        if normalized_disease:
            query += """
            MATCH (s) -[:HAS_TUMOR_TYPE] -> (c:Condition {disease_normalizer_id:$c_id})
            """
            params["c_id"] = normalized_disease

        if normalized_gene:
            query += """
            MATCH (s) -[:HAS_QUALIFIERS] -> (q:Qualifier) -[:HAS_GENE_CONTEXT] -> (
                g:Gene {gene_normalizer_id:$g_id})
            """
            params["g_id"] = normalized_gene

        if normalized_therapy:
            query += """
            MATCH (s1:Study) -[:HAS_THERAPEUTIC] ->(
                tp:TherapeuticAgent {therapy_normalizer_id:$t_id})
            RETURN s1 as s
            UNION
            MATCH (s2:Study) -[:HAS_THERAPEUTIC]-> () - [:HAS_SUBSTITUTES|
                HAS_COMPONENTS] ->(ta:TherapeuticAgent {therapy_normalizer_id:$t_id})
            RETURN s2 as s
            """
            params["t_id"] = normalized_therapy
        else:
            query += "RETURN s"

        return [s[0] for s in tx.run(query, **params)]
