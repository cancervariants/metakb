"""Module for queries."""
import json
import logging
from copy import copy
from enum import Enum

from ga4gh.core._internal.models import (
    Coding,
    Disease,
    Extension,
    Gene,
    TherapeuticAgent,
    TherapeuticProcedure,
)
from ga4gh.vrs import models
from neo4j import Transaction
from neo4j.graph import Node
from pydantic import ValidationError

from metakb.database import Graph
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Document, Method
from metakb.schemas.api import SearchStudiesService, ServiceMeta
from metakb.schemas.app import SourceName
from metakb.schemas.categorical_variation import CategoricalVariation
from metakb.schemas.variation_statement import (
    VariantTherapeuticResponseStudy,
    _VariantOncogenicityStudyQualifier,
)

logger = logging.getLogger(__name__)


class VariationRelation(str, Enum):
    """Create enum for relation between variation and categorical variation"""

    HAS_MEMBERS = "HAS_MEMBERS"
    HAS_DEFINING_CONTEXT = "HAS_DEFINING_CONTEXT"


class TherapeuticRelation(str, Enum):
    """Create enum for therapeutic relation"""

    HAS_COMPONENTS = "HAS_COMPONENTS"
    HAS_SUBSTITUTES = "HAS_SUBSTITUTES"


class TherapeuticProcedureType(str, Enum):
    """Create enum for therapeutic procedures"""

    COMBINATION = "CombinationTherapy"
    SUBSTITUTES = "TherapeuticSubstituteGroup"


def _update_mappings(params: dict) -> None:
    """Update ``params.mappings`` if it exists
    The mappings field will be a string and will be updated to the dict representation

    :param params: Parameters. Will be mutated if mappings field exists
    """
    mappings = params.get("mappings")
    if mappings:
        params["mappings"] = json.loads(mappings)


class QueryHandler:
    """Class for handling queries."""

    def __init__(
        self,
        uri: str = "",
        creds: tuple[str, str] = ("", ""),
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize neo4j driver and the VICC normalizers.

        :param uri: address of Neo4j DB
        :param credentials: tuple containing username and
            password
        :param normalizers: normalizer collection instance
        """
        if normalizers is None:
            normalizers = ViccNormalizers()
        self.driver = Graph(uri, creds).driver
        self.vicc_normalizers = normalizers

    async def search_studies_intersect(
        self,
        variation: str | None = None,
        disease: str | None = None,
        therapy: str | None = None,
        gene: str | None = None,
        study_id: str | None = None,
    ) -> SearchStudiesService:
        """Get nested studies from queried concepts that match all conditions provided.
        For example, if `variation` and `therapy` are provided, will return all studies
        that have both the provided `variation` and `therapy`.

        :param variation: Variation query (Free text or VRS Variation ID)
        :param disease: Disease query
        :param therapy: Therapy query
        :param gene: Gene query
        :param study_id: Study ID query.
        :return: SearchStudiesService response containing nested studies and service
            metadata
        """
        response: dict = {
            "query": {
                "variation": None,
                "disease": None,
                "therapy": None,
                "gene": None,
                "study_id": None,
            },
            "warnings": [],
            "study_ids": [],
            "studies": [],
            "service_meta_": ServiceMeta(),
        }

        normalized_terms = await self._get_normalized_terms(
            variation, disease, therapy, gene, study_id, response
        )

        if normalized_terms is None:
            return SearchStudiesService(**response)

        (
            normalized_variation,
            normalized_disease,
            normalized_therapy,
            normalized_gene,
            study,
            valid_study_id,
        ) = normalized_terms

        with self.driver.session() as session:
            if valid_study_id:
                study_nodes = [study]
                response["study_ids"].append(study["id"])
            else:
                study_nodes = self._get_studies_intersect(
                    session,
                    normalized_variation=normalized_variation,
                    normalized_therapy=normalized_therapy,
                    normalized_disease=normalized_disease,
                    normalized_gene=normalized_gene,
                )
                response["study_ids"] = [s["id"] for s in study_nodes]

            response["studies"] = self._get_nested_studies(session, study_nodes)

        if not response["studies"]:
            response["warnings"].append(
                "No studies found with the provided query parameters."
            )

        return SearchStudiesService(**response)

    async def _get_normalized_terms(
        self,
        variation: str | None,
        disease: str | None,
        therapy: str | None,
        gene: str | None,
        study_id: str | None,
        response: dict,
    ) -> tuple | None:
        """Find normalized terms for queried concepts.

        :param variation: Variation (subject) query
        :param disease: Disease (object_qualifier) query
        :param therapy: Therapy (object) query
        :param gene: Gene query
        :param study_id: Study ID query
        :param response: The response for the query
        :return: A tuple containing the normalized concepts
        """
        if not any((variation, disease, therapy, gene, study_id)):
            response["warnings"].append("No query parameters were provided.")
            return None

        # Find normalized terms using VICC normalizers
        if therapy:
            response["query"]["therapy"] = therapy
            normalized_therapy = self._get_normalized_therapy(
                therapy.strip(), response["warnings"]
            )
        else:
            normalized_therapy = None
        if disease:
            response["query"]["disease"] = disease
            normalized_disease = self._get_normalized_disease(
                disease.strip(), response["warnings"]
            )
        else:
            normalized_disease = None
        if variation:
            response["query"]["variation"] = variation
            normalized_variation = await self._get_normalized_variation(
                variation, response["warnings"]
            )
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
                study = self._get_study_by_id(session, study_id)
                if study:
                    valid_study_id = study.get("id")
                else:
                    response["warnings"].append(f"Study: {study_id} does not exist.")

        # If queried concept is given check that it is normalized / valid
        if (
            (variation and not normalized_variation)
            or (therapy and not normalized_therapy)
            or (disease and not normalized_disease)
            or (gene and not normalized_gene)
            or (study_id and not valid_study_id)
        ):
            return None

        return (
            normalized_variation,
            normalized_disease,
            normalized_therapy,
            normalized_gene,
            study,
            valid_study_id,
        )

    def _get_normalized_therapy(self, therapy: str, warnings: list[str]) -> str | None:
        """Get normalized therapy concept.

        :param therapy: Therapy query
        :param warnings: A list of warnings for the search query
        :return: A normalized therapy concept if it exists
        """
        _, normalized_therapy_id = self.vicc_normalizers.normalize_therapy([therapy])

        if not normalized_therapy_id:
            warnings.append(f"Therapy Normalizer unable to normalize: " f"{therapy}")
        return normalized_therapy_id

    def _get_normalized_disease(self, disease: str, warnings: list[str]) -> str | None:
        """Get normalized disease concept.

        :param disease: Disease query
        :param warnings: A list of warnings for the search query
        :return: A normalized disease concept if it exists
        """
        _, normalized_disease_id = self.vicc_normalizers.normalize_disease([disease])

        if not normalized_disease_id:
            warnings.append(f"Disease Normalizer unable to normalize: " f"{disease}")
        return normalized_disease_id

    async def _get_normalized_variation(
        self, variation: str, warnings: list[str]
    ) -> str | None:
        """Get normalized variation concept.

        :param variation: Variation query
        :param warnings: A list of warnings for the search query
        :return: A normalized variant concept if it exists
        """
        variant_norm_resp = await self.vicc_normalizers.normalize_variation([variation])
        normalized_variation = variant_norm_resp.id if variant_norm_resp else None

        if not normalized_variation:
            # Check if VRS variation (allele, copy number change, copy number count)
            if variation.startswith(("ga4gh:VA.", "ga4gh:CX.", "ga4gh:CN.")):
                normalized_variation = variation
            else:
                warnings.append(
                    f"Variation Normalizer unable to normalize: " f"{variation}"
                )
        return normalized_variation

    def _get_normalized_gene(self, gene: str, warnings: list[str]) -> str | None:
        """Get normalized gene concept.

        :param gene: Gene query
        :param warnings: A list of warnings for the search query.
        :return: A normalized gene concept if it exists
        """
        _, normalized_gene_id = self.vicc_normalizers.normalize_gene([gene])
        if not normalized_gene_id:
            warnings.append(f"Gene Normalizer unable to normalize: {gene}")
        return normalized_gene_id

    @staticmethod
    def _get_study_by_id(tx: Transaction, study_id: str) -> Node | None:
        """Get a Study node by ID.

        :param tx: Neo4j session transaction object
        :param study_id: Study ID to retrieve
        :return: Study node if successful
        """
        query = f"""
        MATCH (s:Study)
        WHERE toLower(s.id) = toLower('{study_id}')
        RETURN s
        """
        return (tx.run(query).single() or [None])[0]

    @staticmethod
    def _get_studies_intersect(
        tx: Transaction,
        normalized_variation: str | None = None,
        normalized_therapy: str | None = None,
        normalized_disease: str | None = None,
        normalized_gene: str | None = None,
    ) -> list[Node]:
        """Get studies that match the intersection of provided concepts.

        :param tx: Neo4j session transaction object
        :param normalized_variation: VRS Variation ID
        :param normalized_therapy: normalized therapy concept ID
        :param normalized_disease: normalized disease concept ID
        :param normalized_gene: normalized gene concept ID
        :return: List of Study nodes that match the intersection of the given parameters
        """
        query = "MATCH (s:Study)"
        params: dict[str, str] = {}

        if normalized_variation:
            query += """
            MATCH (s) -[:HAS_VARIANT] -> (cv:CategoricalVariation)
            MATCH (cv) -[:HAS_DEFINING_CONTEXT|HAS_MEMBERS] -> (v:Variation {id:$v_id})
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
            OPTIONAL MATCH (s) -[:HAS_THERAPEUTIC] -> (tp:TherapeuticAgent {therapy_normalizer_id:$t_id})
            OPTIONAL MATCH (s) -[:HAS_THERAPEUTIC] -> () -[:HAS_SUBSTITUTES|HAS_COMPONENTS] -> (ta:TherapeuticAgent {therapy_normalizer_id:$t_id})
            WITH s, tp, ta
            WHERE tp IS NOT NULL OR ta IS NOT NULL
            """
            params["t_id"] = normalized_therapy

        query += "RETURN DISTINCT s"

        return [s[0] for s in tx.run(query, **params)]

    def _get_nested_studies(
        self, tx: Transaction, study_nodes: list[Node]
    ) -> list[dict]:
        """Get a list of nested studies.

        :param tx: Neo4j session transaction object
        :param study_nodes: A list of Study Nodes
        :return: A list of nested studies
        """
        nested_studies = []
        added_studies = set()
        for s in study_nodes:
            s_id = s.get("id")
            if s_id not in added_studies:
                try:
                    nested_study = self._get_nested_study(tx, s)
                except ValidationError as e:
                    logger.error("%s: %s", s_id, e)
                else:
                    if nested_study:
                        nested_studies.append(nested_study)
                        added_studies.add(s_id)

        return nested_studies

    def _get_nested_study(self, tx: Transaction, s: Node) -> dict:
        """Get information related to a study
        Only VariantTherapeuticResponseStudy are supported at the moment

        :param tx: Neo4j session transaction object
        :param Node s: Study Node
        :return: Nested study
        """
        if s["type"] != "VariantTherapeuticResponseStudy":
            return {}

        params = {
            "tumorType": None,
            "variant": None,
            "strength": None,
            "isReportedIn": [],
            "specifiedBy": None,
        }
        params.update(s)
        study_id = s["id"]

        # Get relationship and nodes for a study
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
                params["tumorType"] = self._get_disease(node)
            elif rel_type == "HAS_VARIANT":
                params["variant"] = self._get_cat_var(tx, node)
            elif rel_type == "HAS_GENE_CONTEXT":
                params["qualifiers"] = self._get_variant_onco_study_qualifier(
                    tx, study_id, s.get("alleleOrigin")
                )
            elif rel_type == "IS_SPECIFIED_BY":
                node["isReportedIn"] = self._get_method_document(tx, node["id"])
                params["specifiedBy"] = Method(**node)
            elif rel_type == "IS_REPORTED_IN":
                params["isReportedIn"].append(self._get_document(node))
            elif rel_type == "HAS_STRENGTH":
                params["strength"] = Coding(**node)
            elif rel_type == "HAS_THERAPEUTIC":
                params["therapeutic"] = self._get_therapeutic_procedure(tx, node)
            else:
                logger.warning("relation type not supported: %s", rel_type)

        return VariantTherapeuticResponseStudy(**params).model_dump()

    @staticmethod
    def _get_disease(node: dict) -> Disease:
        """Get disease data from a node with relationship ``HAS_TUMOR_TYPE``

        :param node: Disease node data. This will be mutated.
        :return: Disease data
        """
        _update_mappings(node)
        node["extensions"] = [
            Extension(name="disease_normalizer_id", value=node["disease_normalizer_id"])
        ]
        return Disease(**node)

    def _get_cat_var(self, tx: Transaction, node: dict) -> CategoricalVariation:
        """Get categorical variation data from a node with relationship ``HAS_VARIANT``

        :param tx: Neo4j session transaction object
        :param node: Variant node data. This will be mutated.
        :return: Categorical Variation data
        """
        _update_mappings(node)

        extensions = []
        for node_key, ext_name in (
            ("moa_representative_coordinate", "MOA representative coordinate"),
            ("civic_representative_coordinate", "CIViC representative coordinate"),
            ("civic_molecular_profile_score", "CIViC Molecular Profile Score"),
            ("variant_types", "Variant types"),
        ):
            node_val = node.get(node_key)
            if node_val:
                try:
                    ext_val = json.loads(node_val)
                except TypeError:
                    ext_val = node_val
                extensions.append(Extension(name=ext_name, value=ext_val))
                if node_key.startswith(SourceName.MOA.value):
                    # Cant be civic
                    break

        node["extensions"] = extensions or None
        node["definingContext"] = self._get_variations(
            tx, node["id"], VariationRelation.HAS_DEFINING_CONTEXT
        )[0]
        node["members"] = self._get_variations(
            tx, node["id"], VariationRelation.HAS_MEMBERS
        )
        return CategoricalVariation(**node)

    @staticmethod
    def _get_variations(
        tx: Transaction, cv_id: str, relation: VariationRelation
    ) -> list[dict]:
        """Get list of variations associated to categorical variation

        :param tx: Neo4j session transaction object
        :param cv_id: ID for categorical variation
        :param relation: Relation type for categorical variation and variation
        :return: List of variations with `relation` to categorical variation. If
            VariationRelation.HAS_MEMBERS, returns at least one variation. Otherwise,
            returns exactly one variation
        """
        query = f"""
        MATCH (v:Variation) <- [:{relation.value}] - (cv:CategoricalVariation
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
                            models.Expression(syntax=syntax, value=hgvs_expr)
                        )

            v_params["expressions"] = expressions or None
            loc_params = r_params["loc"]
            v_params["location"] = loc_params
            v_params["location"]["sequenceReference"] = json.loads(
                loc_params["sequence_reference"]
            )
            variations.append(models.Variation(**v_params).model_dump())
        return variations

    @staticmethod
    def _get_variant_onco_study_qualifier(
        tx: Transaction, study_id: str, allele_origin: str | None
    ) -> _VariantOncogenicityStudyQualifier:
        """Get variant oncogenicity study qualifier data for a study

        :param tx: Neo4j session transaction object
        :param study_id: ID of study node
        :param allele_origin: Study's allele origin
        :return Variant oncogenicity study qualifier data
        """
        query = f"""
        MATCH (s:Study {{ id: '{study_id}' }}) -[:HAS_GENE_CONTEXT] -> (g:Gene)
        RETURN g
        """
        record = tx.run(query).single()
        if not record:
            return None

        gene_params = record.data()["g"]
        _update_mappings(gene_params)

        gene_params["extensions"] = [
            Extension(
                name="gene_normalizer_id", value=gene_params["gene_normalizer_id"]
            )
        ]

        return _VariantOncogenicityStudyQualifier(
            alleleOrigin=allele_origin, geneContext=Gene(**gene_params)
        )

    @staticmethod
    def _get_method_document(tx: Transaction, method_id: str) -> Document | None:
        """Get document for a given method

        :param tx: Neo4j session transaction object
        :param method_id: ID for method
        :return: Document
        """
        query = f"""
        MATCH (m:Method {{ id: '{method_id}' }}) -[:IS_REPORTED_IN] -> (d:Document)
        RETURN d
        """
        record = tx.run(query).single()
        if not record:
            return None

        doc_params = record.data()["d"]
        return Document(**doc_params)

    @staticmethod
    def _get_document(node: dict) -> Document:
        """Get document data from a node with relationship ``IS_SPECIFIED_BY``

        :param node: Document node data. This will be mutated
        :return: Document data
        """
        _update_mappings(node)

        source_type = node.get("source_type")
        if source_type:
            node["extensions"] = [Extension(name="source_type", value=source_type)]
        return Document(**node)

    def _get_therapeutic_procedure(
        self,
        tx: Transaction,
        node: dict,
    ) -> TherapeuticProcedure | TherapeuticAgent | None:
        """Get therapeutic procedure from a node with relationship ``HAS_THERAPEUTIC``

        :param tx: Neo4j session transaction object
        :param node: Therapeutic node data. This will be mutated.
        :return: Therapeutic procedure if node type is supported. Currently, therapeutic
            action is not supported.
        """
        node_type = node["type"]
        if node_type in {"CombinationTherapy", "TherapeuticSubstituteGroup"}:
            civic_therapy_interaction_type = node.get("civic_therapy_interaction_type")
            if civic_therapy_interaction_type:
                node["extensions"] = [
                    Extension(
                        name="civic_therapy_interaction_type",
                        value=civic_therapy_interaction_type,
                    )
                ]

            if node_type == "CombinationTherapy":
                node["components"] = self._get_therapeutic_agents(
                    tx,
                    node["id"],
                    TherapeuticProcedureType.COMBINATION,
                    TherapeuticRelation.HAS_COMPONENTS,
                )
            else:
                node["substitutes"] = self._get_therapeutic_agents(
                    tx,
                    node["id"],
                    TherapeuticProcedureType.SUBSTITUTES,
                    TherapeuticRelation.HAS_SUBSTITUTES,
                )

            therapeutic = TherapeuticProcedure(**node)
        elif node_type == "TherapeuticAgent":
            therapeutic = self._get_therapeutic_agent(node)
        else:
            logger.warning("node type not supported: %s", node_type)
            therapeutic = None

        return therapeutic

    def _get_therapeutic_agents(
        self,
        tx: Transaction,
        tp_id: str,
        tp_type: TherapeuticProcedureType,
        tp_relation: TherapeuticRelation,
    ) -> list[TherapeuticAgent]:
        """Get list of therapeutic agents for therapeutic combination or substitutes
        group

        :param tp_id: ID for combination therapy or therapeutic substitute group
        :param tp_type: Therapeutic Procedure type
        :param tp_relation: Relationship type for therapeutic procedure and therapeutic
            agent
        :return: List of Therapeutic Agents for a combination therapy or therapeutic
            substitute group
        """
        query = f"""
        MATCH (tp:{tp_type.value} {{ id: '{tp_id}' }}) -[:{tp_relation.value}]
            -> (ta:TherapeuticAgent)
        RETURN ta
        """
        therapeutic_agents = []
        results = tx.run(query)
        for r in results:
            r_params = r.data()
            ta_params = r_params["ta"]
            ta = self._get_therapeutic_agent(ta_params)
            therapeutic_agents.append(ta)
        return therapeutic_agents

    @staticmethod
    def _get_therapeutic_agent(in_ta_params: dict) -> TherapeuticAgent:
        """Transform input parameters into TherapeuticAgent object

        :param in_ta_params: Therapeutic Agent node properties
        :return: TherapeuticAgent
        """
        ta_params = copy(in_ta_params)
        _update_mappings(ta_params)
        extensions = [
            Extension(
                name="therapy_normalizer_id", value=ta_params["therapy_normalizer_id"]
            )
        ]
        regulatory_approval = ta_params.get("regulatory_approval")
        if regulatory_approval:
            regulatory_approval = json.loads(regulatory_approval)
            extensions.append(
                Extension(name="regulatory_approval", value=regulatory_approval)
            )

        ta_params["extensions"] = extensions
        return TherapeuticAgent(**ta_params)
