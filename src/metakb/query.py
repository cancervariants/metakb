"""Provide class/methods/schemas for issuing queries against the database."""
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
from neo4j import Driver
from neo4j.graph import Node
from pydantic import ValidationError

from metakb.database import get_driver
from metakb.normalizers import ViccNormalizers
from metakb.schemas.annotation import Document, Method
from metakb.schemas.api import (
    BatchSearchStudiesQuery,
    BatchSearchStudiesService,
    NormalizedQuery,
    SearchStudiesService,
    ServiceMeta,
)
from metakb.schemas.app import SourceName
from metakb.schemas.categorical_variation import CategoricalVariation
from metakb.schemas.variation_statement import (
    VariantTherapeuticResponseStudy,
    _VariantOncogenicityStudyQualifier,
)

logger = logging.getLogger(__name__)


class VariationRelation(str, Enum):
    """Constrain possible values for the relationship between variations and
    categorical variations.
    """

    HAS_MEMBERS = "HAS_MEMBERS"
    HAS_DEFINING_CONTEXT = "HAS_DEFINING_CONTEXT"


class TherapeuticRelation(str, Enum):
    """Constrain possible values for therapeutic relationships."""

    HAS_COMPONENTS = "HAS_COMPONENTS"
    HAS_SUBSTITUTES = "HAS_SUBSTITUTES"


class TherapeuticProcedureType(str, Enum):
    """Constrain possible values for kinds of therapeutic procedures."""

    COMBINATION = "CombinationTherapy"
    SUBSTITUTES = "TherapeuticSubstituteGroup"


def _deserialize_field(node: dict, field_name: str) -> None | dict:
    """Deserialize JSON blob property.

    :param node: Neo4j graph node data
    :param field_name: Name of field to check/deserialize
    :return: property dictionary if available, ``None`` if empty
    """
    field = node.get(field_name)
    if field:
        return json.loads(field)
    return None


class QueryHandler:
    """Primary query-handling class. Wraps database connections and hooks to external
    services such as the concept normalizers.
    """

    def __init__(
        self,
        driver: Driver | None = None,
        normalizers: ViccNormalizers | None = None,
    ) -> None:
        """Initialize neo4j driver and the VICC normalizers.

        All arguments are optional; if not given, resources acquisition will be
        attempted with default parameters. Pass arguments for ``uri`` and ``creds``
        to provide them manually:

        >>> from metakb.query import QueryHandler
        >>> from metakb.database import get_driver
        >>> qh = QueryHandler(get_driver("bolt://localhost:7687", ("neo4j", "password")))

        :param graph: database handler instance
        :param normalizers: normalizer collection instance
        """
        if driver is None:
            driver = get_driver()
        if normalizers is None:
            normalizers = ViccNormalizers()
        self.driver = driver
        self.vicc_normalizers = normalizers

    async def search_studies(
        self,
        variation: str | None = None,
        disease: str | None = None,
        therapy: str | None = None,
        gene: str | None = None,
        study_id: str | None = None,
    ) -> SearchStudiesService:
        """Get nested studies from queried concepts that match all conditions provided.
        For example, if ``variation`` and ``therapy`` are provided, will return all studies
        that have both the provided ``variation`` and ``therapy``.

        >>> from metakb.query import QueryHandler
        >>> qh = QueryHandler()
        >>> result = qh.search_studies("BRAF V600E")
        >>> result.study_ids[:3]
        ['moa.assertion:944', 'moa.assertion:911', 'moa.assertion:865']
        >>> result.studies[0].isReportedIn[0].url
        'https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/202429s019lbl.pdf'


        Variation, disease, therapy, and gene terms are resolved via their respective
        :ref:`concept normalization services<normalization>`.

        :param variation: Variation query. Free text variation description, e.g.
            ``"BRAF V600E"``, or GA4GH variation ID, e.g.
            ``"ga4gh:VA.4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO"``. Case-insensitive.
        :param disease: Disease query. Full disease name, e.g. ``"glioblastoma"``,
            common shorthand name, e.g. ``"GBM"``, concept URI, e.g. ``"ncit:C3058"``.
            Case-insensitive.
        :param therapy: Therapy query. Full name, e.g. ``"imatinib"``, trade name, e.g.
            ``"GLEEVEC"``, or concept URI, e.g. ``"chembl:CHEMBL941"``. Case-insensitive.
        :param gene: Gene query. Common shorthand name, e.g. ``"NTRK1"``, or compact URI,
            e.g. ``"ensembl:ENSG00000198400"``.
        :param study_id: Study ID query provided by source, e.g. ``"civic.eid:3017"``.
        :return: Service response object containing nested studies and service metadata.
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

        if valid_study_id:
            study_nodes = [study]
            response["study_ids"].append(study["id"])
        else:
            study_nodes = self._get_studies(
                normalized_variation=normalized_variation,
                normalized_therapy=normalized_therapy,
                normalized_disease=normalized_disease,
                normalized_gene=normalized_gene,
            )
            response["study_ids"] = [s["id"] for s in study_nodes]

        response["studies"] = self._get_nested_studies(study_nodes)

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
            study = self._get_study_by_id(study_id)
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

    def _get_study_by_id(self, study_id: str) -> Node | None:
        """Get a Study node by ID.

        :param study_id: Study ID to retrieve
        :return: Study node if successful
        """
        query = """
        MATCH (s:Study)
        WHERE toLower(s.id) = toLower($study_id)
        RETURN s
        """
        records = self.driver.execute_query(query, study_id=study_id).records
        if not records:
            return None
        return records[0]["s"]

    def _get_studies(
        self,
        normalized_variation: str | None = None,
        normalized_therapy: str | None = None,
        normalized_disease: str | None = None,
        normalized_gene: str | None = None,
    ) -> list[Node]:
        """Get studies that match the intersection of provided concepts.

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

        return [s[0] for s in self.driver.execute_query(query, params).records]

    def _get_nested_studies(self, study_nodes: list[Node]) -> list[dict]:
        """Get a list of nested studies.

        :param study_nodes: A list of Study Nodes
        :return: A list of nested studies
        """
        nested_studies = []
        added_studies = set()
        for s in study_nodes:
            s_id = s.get("id")
            if s_id not in added_studies:
                try:
                    nested_study = self._get_nested_study(s)
                except ValidationError as e:
                    logger.error("%s: %s", s_id, e)
                else:
                    if nested_study:
                        nested_studies.append(nested_study)
                        added_studies.add(s_id)

        return nested_studies

    def _get_nested_study(self, study_node: Node) -> dict:
        """Get information related to a study
        Only VariantTherapeuticResponseStudy are supported at the moment

        :param study_node: Neo4j graph node for study
        :return: Nested study
        """
        if study_node["type"] != "VariantTherapeuticResponseStudy":
            return {}

        params = {
            "tumorType": None,
            "variant": None,
            "strength": None,
            "isReportedIn": [],
            "specifiedBy": None,
        }
        params.update(study_node)
        study_id = study_node["id"]

        # Get relationship and nodes for a study
        query = """
        MATCH (s:Study { id: $study_id })
        OPTIONAL MATCH (s)-[r]-(n)
        RETURN type(r) as r_type, n;
        """
        nodes_and_rels = self.driver.execute_query(query, study_id=study_id).records

        for item in nodes_and_rels:
            data = item.data()
            rel_type = data["r_type"]
            node = data["n"]

            if rel_type == "HAS_TUMOR_TYPE":
                params["tumorType"] = self._get_disease(node)
            elif rel_type == "HAS_VARIANT":
                params["variant"] = self._get_cat_var(node)
            elif rel_type == "HAS_GENE_CONTEXT":
                params["qualifiers"] = self._get_variant_onco_study_qualifier(
                    study_id, study_node.get("alleleOrigin")
                )
            elif rel_type == "IS_SPECIFIED_BY":
                node["isReportedIn"] = self._get_method_document(node["id"])
                params["specifiedBy"] = Method(**node)
            elif rel_type == "IS_REPORTED_IN":
                params["isReportedIn"].append(self._get_document(node))
            elif rel_type == "HAS_STRENGTH":
                params["strength"] = Coding(**node)
            elif rel_type == "HAS_THERAPEUTIC":
                params["therapeutic"] = self._get_therapeutic_procedure(node)
            else:
                logger.warning("relation type not supported: %s", rel_type)

        return VariantTherapeuticResponseStudy(**params).model_dump()

    @staticmethod
    def _get_disease(node: dict) -> Disease:
        """Get disease data from a node with relationship ``HAS_TUMOR_TYPE``

        :param node: Disease node data
        :return: Disease object
        """
        node["mappings"] = _deserialize_field(node, "mappings")
        node["extensions"] = [
            Extension(name="disease_normalizer_id", value=node["disease_normalizer_id"])
        ]
        return Disease(**node)

    def _get_variations(self, cv_id: str, relation: VariationRelation) -> list[dict]:
        """Get list of variations associated to categorical variation

        :param cv_id: ID for categorical variation
        :param relation: Relation type for categorical variation and variation
        :return: List of variations with `relation` to categorical variation. If
            VariationRelation.HAS_MEMBERS, returns at least one variation. Otherwise,
            returns exactly one variation
        """
        query = f"""
        MATCH (v:Variation) <- [:{relation.value}] - (cv:CategoricalVariation
            {{ id: $cv_id }})
        MATCH (loc:Location) <- [:HAS_LOCATION] - (v)
        RETURN v, loc
        """
        results = self.driver.execute_query(query, cv_id=cv_id).records
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

    def _get_cat_var(self, node: dict) -> CategoricalVariation:
        """Get categorical variation data from a node with relationship ``HAS_VARIANT``

        :param node: Variant node data. This will be mutated.
        :return: Categorical Variation data
        """
        node["mappings"] = _deserialize_field(node, "mappings")

        extensions = []
        for node_key, ext_name in (
            ("moa_representative_coordinate", "MOA representative coordinate"),
            ("civic_representative_coordinate", "CIViC representative coordinate"),
            # ("civic_molecular_profile_score", "CIViC Molecular Profile Score"),
            ("variant_types", "Variant types"),
        ):
            ext_val = _deserialize_field(node, node_key)
            if ext_val:
                extensions.append(Extension(name=ext_name, value=ext_val))
                if node_key.startswith(SourceName.MOA.value):
                    # no need to check additional fields if it's a MOA variant
                    # this could be highly brittle to changes/new sources, and any edits
                    # to the data model or inputs should be very careful to ensure
                    # this remains correct
                    break

        if "civic_molecular_profile_score" in node:
            extensions.append(
                Extension(
                    name="CIViC Molecular Profile Score",
                    value=node["civic_molecular_profile_score"],
                )
            )

        node["extensions"] = extensions or None
        node["definingContext"] = self._get_variations(
            node["id"], VariationRelation.HAS_DEFINING_CONTEXT
        )[0]
        node["members"] = self._get_variations(
            node["id"], VariationRelation.HAS_MEMBERS
        )
        return CategoricalVariation(**node)

    def _get_variant_onco_study_qualifier(
        self, study_id: str, allele_origin: str | None
    ) -> _VariantOncogenicityStudyQualifier:
        """Get variant oncogenicity study qualifier data for a study

        :param study_id: ID of study node
        :param allele_origin: Study's allele origin
        :return Variant oncogenicity study qualifier data
        """
        query = """
        MATCH (s:Study { id: $study_id }) -[:HAS_GENE_CONTEXT] -> (g:Gene)
        RETURN g
        """
        results = self.driver.execute_query(query, study_id=study_id)
        if not results.records:
            logger.error(
                "Unable to complete oncogenicity study qualifier lookup for study_id %s",
                study_id,
            )
            return None
        if len(results.records) > 1:
            # TODO should this be an error? can studies have multiple gene contexts?
            logger.error(
                "Encountered multiple matches for oncogenicity study qualifier lookup for study_id %s",
                study_id,
            )
            return None

        gene_node = results.records[0].data()["g"]
        gene_node["mappings"] = _deserialize_field(gene_node, "mappings")

        gene_node["extensions"] = [
            Extension(name="gene_normalizer_id", value=gene_node["gene_normalizer_id"])
        ]

        return _VariantOncogenicityStudyQualifier(
            alleleOrigin=allele_origin, geneContext=Gene(**gene_node)
        )

    def _get_method_document(self, method_id: str) -> Document | None:
        """Get document for a given method

        :param method_id: ID for method
        :return: Document
        """
        query = """
        MATCH (m:Method { id: $method_id }) -[:IS_REPORTED_IN] -> (d:Document)
        RETURN d
        """
        records = self.driver.execute_query(query, method_id=method_id).records
        if not records:
            return None

        doc_params = records[0].data()["d"]
        return Document(**doc_params)

    @staticmethod
    def _get_document(node: dict) -> Document:
        """Get document data from a node with relationship ``IS_SPECIFIED_BY``

        :param node: Document node data. This will be mutated
        :return: Document data
        """
        node["mappings"] = _deserialize_field(node, "mappings")

        source_type = node.get("source_type")
        if source_type:
            node["extensions"] = [Extension(name="source_type", value=source_type)]
        return Document(**node)

    def _get_therapeutic_procedure(
        self,
        node: dict,
    ) -> TherapeuticProcedure | TherapeuticAgent | None:
        """Get therapeutic procedure from a node with relationship ``HAS_THERAPEUTIC``

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
                    node["id"],
                    TherapeuticProcedureType.COMBINATION,
                    TherapeuticRelation.HAS_COMPONENTS,
                )
            else:
                node["substitutes"] = self._get_therapeutic_agents(
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
        MATCH (tp:{tp_type.value} {{ id: $tp_id }}) -[:{tp_relation.value}]
            -> (ta:TherapeuticAgent)
        RETURN ta
        """
        therapeutic_agents = []
        results = self.driver.execute_query(query, tp_id=tp_id).records
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
        ta_params["mappings"] = _deserialize_field(ta_params, "mappings")
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

    async def batch_search_studies(
        self,
        variations: list[str] | None = None,
    ) -> BatchSearchStudiesService:
        """Fetch all studies associated with any of the provided variation description
        strings.

        Because this method could be expanded to include other kinds of search terms,
        ``variations`` is optionally nullable.

        >>> from metakb.query import QueryHandler
        >>> qh = QueryHandler()
        >>> response = await qh.batch_search_studies(["EGFR L858R"])
        >>> response.study_ids[:3]
        ['civic.eid:229', 'civic.eid:3811', 'moa.assertion:268']

        All terms are normalized, so redundant terms don't alter search results:

        >>> redundant_response = await qh.batch_search_studies(
        ...     ["EGFR L858R", "NP_005219.2:p.Leu858Arg"]
        ... )
        >>> len(response.study_ids) == len(redundant_response.study_ids)
        True

        :param variations: a list of variation description strings, e.g.
            ``["BRAF V600E"]``
        :return: response object including all matching studies
        """
        response = BatchSearchStudiesService(
            query=BatchSearchStudiesQuery(variations=[]),
            service_meta_=ServiceMeta(),
            warnings=[],
        )
        if not variations:
            return response

        for query_variation in set(variations):
            variation_id = await self._get_normalized_variation(
                query_variation, response.warnings
            )
            response.query.variations.append(
                NormalizedQuery(term=query_variation, normalized_id=variation_id)
            )
        variation_ids = list(
            {v.normalized_id for v in response.query.variations if v.normalized_id}
        )
        if not variation_ids:
            return response

        query = """
            MATCH (s) -[:HAS_VARIANT] -> (cv:CategoricalVariation)
            MATCH (cv) -[:HAS_DEFINING_CONTEXT|HAS_MEMBERS] -> (v:Variation)
            WHERE v.id IN $v_ids
            RETURN s
        """
        with self.driver.session() as session:
            result = session.run(query, v_ids=variation_ids)
            study_nodes = [r[0] for r in result]
        response.study_ids = list({n["id"] for n in study_nodes})
        studies = self._get_nested_studies(study_nodes)
        response.studies = [VariantTherapeuticResponseStudy(**s) for s in studies]
        return response
