"""Module for queries."""
from enum import StrEnum
import json
import logging
from typing import Dict, List, Optional, Tuple

from ga4gh.core import core_models
from ga4gh.vrs import models
from neo4j import Transaction
from neo4j.graph import Node

from metakb.database import Graph
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Document, Method
from metakb.schemas.api import SearchStudiesService, ServiceMeta
from metakb.schemas.categorical_variation import CategoricalVariation
from metakb.schemas.variation_statement import (
    VariantTherapeuticResponseStudy,
    _VariantOncogenicityStudyQualifier,
)

logger = logging.getLogger(__name__)


class VariationRelation(StrEnum):
    """Create enum for relation between variation and categorical variation"""

    HAS_MEMBERS = "HAS_MEMBERS"
    HAS_DEFINING_CONTEXT = "HAS_DEFINING_CONTEXT"


class TherapeuticRelation(StrEnum):
    """Create enum for therapeutic relation"""

    HAS_COMPONENTS = "HAS_COMPONENTS"
    HAS_SUBSTITUTES = "HAS_SUBSTITUTES"


class TherapeuticProcedureType(StrEnum):
    """Create enum for therapeutic procedures"""

    COMBINATION = "CombinationTherapy"
    SUBSTITUTES = "TherapeuticSubstituteGroup"


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

    def _get_normalized_therapy(self, therapy: str,
                                warnings: List[str]) -> Optional[str]:
        """Get normalized therapy concept.

        :param therapy: Therapy query
        :param warnings: A list of warnings for the search query
        :return: A normalized therapy concept if it exists
        """
        _, normalized_therapy_id = \
            self.vicc_normalizers.normalize_therapy([therapy])

        if not normalized_therapy_id:
            warnings.append(f"Therapy Normalizer unable to normalize: "
                            f"{therapy}")
        return normalized_therapy_id

    def _get_normalized_disease(self, disease: str,
                                warnings: List[str]) -> Optional[str]:
        """Get normalized disease concept.

        :param disease: Disease query
        :param warnings: A list of warnings for the search query
        :return: A normalized disease concept if it exists
        """
        _, normalized_disease_id = \
            self.vicc_normalizers.normalize_disease([disease])

        if not normalized_disease_id:
            warnings.append(f"Disease Normalizer unable to normalize: "
                            f"{disease}")
        return normalized_disease_id

    async def _get_normalized_variation(self, variation: str,
                                        warnings: List[str]) -> Optional[str]:
        """Get normalized variation concept.

        :param variation: Variation query
        :param warnings: A list of warnings for the search query
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

    def _get_normalized_gene(self, gene: str, warnings: List[str]) -> Optional[str]:
        """Get normalized gene concept.

        :param gene: Gene query
        :param warnings: A list of warnings for the search query.
        :return: A normalized gene concept if it exists
        """
        _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
        if not normalized_gene_id:
            warnings.append(f"Gene Normalizer unable to normalize: {gene}")
        return normalized_gene_id

    async def _get_normalized_terms(
        self, variation: Optional[str], disease: Optional[str],
        therapy: Optional[str], gene: Optional[str],
        study_id: Optional[str], response: Dict
    ) -> Optional[Tuple]:
        """Find normalized terms for queried concepts.

        :param variation: Variation (subject) query
        :param disease: Disease (object_qualifier) query
        :param therapy: Therapy (object) query
        :param gene: Gene query
        :param study_id: Study ID query
        :param response: The response for the query
        :return: A tuple containing the normalized concepts
        """
        if not (variation or disease or therapy or gene or study_id):
            response["warnings"].append("No parameters were entered.")
            return None

        # Find normalized terms using VICC normalizers
        if therapy:
            response["query"]["therapy"] = therapy
            normalized_therapy = \
                self._get_normalized_therapy(therapy.strip(), response["warnings"])
        else:
            normalized_therapy = None
        if disease:
            response["query"]["disease"] = disease
            normalized_disease = \
                self._get_normalized_disease(disease.strip(), response["warnings"])
        else:
            normalized_disease = None
        if variation:
            response["query"]["variation"] = variation
            normalized_variation = \
                await self._get_normalized_variation(variation, response["warnings"])
        else:
            normalized_variation = None
        if gene:
            response["query"]["gene"] = gene
            normalized_gene = self._get_normalized_gene(gene, response["warnings"])
        else:
            normalized_gene = None

        # Check that queried study_id is valid
        valid_study_id = None
        study = None
        if study_id:
            response["query"]["study_id"] = study_id
            with self.driver.session() as session:
                study = session.execute_read(
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
        study_id: Optional[str] = None
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
                "study_id": None
            },
            "warnings": [],
            "study_ids": [],
            "studies": [],
            "service_meta_": ServiceMeta()
        }

        normalized_terms = await self._get_normalized_terms(
            variation, disease, therapy, gene, study_id, response)

        if normalized_terms is None:
            return SearchStudiesService(**response)

        (normalized_variation, normalized_disease,
         normalized_therapy, normalized_gene, study,
         valid_study_id) = normalized_terms

        with self.driver.session() as session:
            if valid_study_id:
                study_nodes = [study]
                response["study_ids"].append(study["id"])
            else:
                study_nodes = self._get_related_studies(
                    session,
                    normalized_variation,
                    normalized_therapy,
                    normalized_disease,
                    normalized_gene
                )
                response["study_ids"] = [s["id"] for s in study_nodes]
            response["studies"] = self._get_studies_response(session, study_nodes)

        return SearchStudiesService(**response)

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

        :param tx: Neo4j session transaction object
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

        :param tx: Neo4j session transaction object
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
                mappings = node.get("mappings")
                if mappings:
                    node["mappings"] = json.loads(mappings)
                node["extensions"] = [
                    core_models.Extension(
                        name="disease_normalizer_id",
                        value=node["disease_normalizer_id"]
                    )
                ]
                params["tumorType"] = core_models.Disease(**node)
            elif rel_type == "HAS_VARIANT":
                mappings = node.get("mappings")
                if mappings:
                    node["mappings"] = json.loads(mappings)

                extensions = []
                for node_k, ext_n in (
                    ("moa_representative_coordinate", "MOA representative coordinate"),
                    ("civic_representative_coordinate", "CIViC representative coordinate"),  # noqa: E501
                    ("civic_molecular_profile_score", "CIViC Molecular Profile Score"),
                    ("variant_types", "Variant types")
                ):
                    val = node.get(node_k)
                    if val:
                        try:
                            val = json.loads(val)
                        except TypeError:
                            val = val
                        extensions.append(
                            core_models.Extension(
                                name=ext_n,
                                value=val
                            )
                        )
                        if node_k.startswith("moa"):
                            # Cant be civic
                            break
                node["extensions"] = extensions or None

                node["definingContext"] = self._get_variations(
                    tx, node["id"], VariationRelation.HAS_DEFINING_CONTEXT
                )[0]
                node["members"] = self._get_variations(
                    tx, node["id"], VariationRelation.HAS_MEMBERS
                )
                params["variant"] = CategoricalVariation(**node)
            elif rel_type == "HAS_GENE_CONTEXT":
                params["qualifiers"] = _VariantOncogenicityStudyQualifier(
                    alleleOrigin=s.get("alleleOrigin"),
                    geneContext=self._get_gene_context_for_study(tx, study_id)
                )
            elif rel_type == "IS_SPECIFIED_BY":
                node["isReportedIn"] = self._get_method_document(tx, node["id"])
                params["specifiedBy"] = Method(**node)
            elif rel_type == "IS_REPORTED_IN":
                mappings = node.get("mappings")
                if mappings:
                    node["mappings"] = json.loads(mappings)

                source_type = node.get("source_type")
                if source_type:
                    node["extensions"] = [
                        core_models.Extension(
                            name="source_type",
                            value=source_type
                        )
                    ]
                params["isReportedIn"].append(Document(**node))
            elif rel_type == "HAS_STRENGTH":
                params["strength"] = core_models.Coding(**node)
            elif rel_type == "HAS_THERAPEUTIC":
                node_type = node["type"]
                if node_type == "CombinationTherapy":
                    node["components"] = self._get_therapeutic_agents(
                        tx, node["id"], TherapeuticProcedureType.COMBINATION,
                        TherapeuticRelation.HAS_COMPONENTS
                    )
                    params["therapeutic"] = core_models.TherapeuticProcedure(**node)
                elif node_type == "TherapeuticSubstituteGroup":
                    node["substitutes"] = self._get_therapeutic_agents(
                        tx, node["id"], TherapeuticProcedureType.SUBSTITUTES,
                        TherapeuticRelation.HAS_SUBSTITUTES
                    )
                    params["therapeutic"] = core_models.TherapeuticProcedure(**node)
                elif node_type == "TherapeuticAgent":
                    params["therapeutic"] = self._get_ta(node)

        return VariantTherapeuticResponseStudy(**params).model_dump()

    @staticmethod
    def _get_ta(ta_params: Dict) -> core_models.TherapeuticAgent:
        """Transform parameters into TherapeuticAgent

        :param ta_params: Therapeutic agent properties
        :return: TherapeuticAgent
        """
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

    def _get_therapeutic_agents(
        self,
        tx: Transaction,
        tp_id: str,
        tp_type: TherapeuticProcedureType,
        tp_relation: TherapeuticRelation
    ) -> List[core_models.TherapeuticAgent]:
        """Get list of components for therapeutic combination or substitute group

        :param tp_id: ID for combination therapy or therapeutic substitute group
        :param tp_type: Therapeutic Procedure type
        :param tp_relation: Therapeutic procedure relation and therapeutic agent
        :return: List of Therapeutic Agents for a combination therapy or therapeutic
            substitute group
        """
        query = f"""
        MATCH (tp:{tp_type} {{ id: '{tp_id}' }}) -[:{tp_relation}]
            -> (ta:TherapeuticAgent)
        RETURN ta
        """
        therapeutic_agents = []
        results = tx.run(query)
        for r in results:
            r_params = r.data()
            ta_params = r_params["ta"]
            ta = self._get_ta(ta_params)
            therapeutic_agents.append(ta)
        return therapeutic_agents

    @staticmethod
    def _get_variations(
        tx: Transaction,
        cv_id: str,
        relation: VariationRelation
    ) -> List[Dict]:
        """Get list of variations associated to categorical variation

        :param tx: Neo4j session transaction object
        :param cv_id: ID for categorical variation
        :param relation: Relation type for categorical variation and variation
        :return: List of variations with `relation` to categorical variation. If
            VariationRelation.HAS_MEMBERS, expects at least one variation. Otherwise,
            expects exactly one variation
        """
        query = f"""
        MATCH (v:Variation) <- [:{relation}] - (cv:CategoricalVariation
            {{ id: '{cv_id}' }})
        MATCH (loc:Location) <- [:HAS_LOCATION] - (v)
        RETURN v, loc
        """
        results = tx.run(query)
        variations = []
        for r in results:
            r_params = r.data()
            v_params = r_params["v"]
            expressions = []
            for variation_k, variation_v in v_params.items():
                if variation_k == "state":
                    v_params[variation_k] = json.loads(variation_v)
                elif variation_k.startswith("expression_hgvs_"):
                    syntax = variation_k.split("expression_")[-1].replace("_", ".")
                    for hgvs_expr in variation_v:
                        expressions.append(
                            models.Expression(
                                syntax=syntax,
                                value=hgvs_expr
                            )
                        )

            v_params["expressions"] = expressions or None
            loc_params = r_params["loc"]
            v_params["location"] = loc_params
            v_params["location"]["sequenceReference"] = json.loads(loc_params["sequence_reference"])  # noqa: E501
            variations.append(models.Variation(**v_params).model_dump())
        return variations

    @staticmethod
    def _get_method_document(tx: Transaction, method_id: str) -> Document:
        """Get document for a given method

        :param tx: Neo4j session transaction object
        :param method_id: ID for method
        :return: Document
        """
        query = f"""
        MATCH (m:Method {{ id: '{method_id}' }}) -[:IS_REPORTED_IN] -> (d:Document)
        RETURN d
        """
        doc_params = tx.run(query).single().data()["d"]
        return Document(**doc_params)

    @staticmethod
    def _get_gene_context_for_study(
        tx: Transaction,
        study_id: str,
    ) -> core_models.Gene:
        """Get gene context for a given study

        :param tx: Neo4j session transaction object
        :param study_id: ID for study
        :return: Gene context associated to study
        """
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
        normalized_variation: Optional[str] = None,
        normalized_therapy: Optional[str] = None,
        normalized_disease: Optional[str] = None,
        normalized_gene: Optional[str] = None
    ) -> List[Node]:
        """Get studies that contain queried normalized concepts

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
            MATCH (s) -[:HAS_GENE_CONTEXT] -> (g:Gene {gene_normalizer_id:$g_id})
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
