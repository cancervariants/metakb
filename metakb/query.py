"""Module for queries."""
import logging
from typing import Optional, Tuple, Dict, List
import json
from urllib.parse import quote

from neo4j import Driver
from neo4j.exceptions import DriverError
from neo4j.work.transaction import Transaction
from ga4gh.vrsatile.pydantic.vrsatile_models import ValueObjectDescriptor, \
    VariationDescriptor, Expression

from metakb.database import Graph
from metakb.normalizers import VICCNormalizers
from metakb.exceptions import NormalizationException
from metakb.schemas import NestedStatementResponse, SearchIDService, SearchQuery, \
    Matches, SearchService, SearchStatementsQuery, SearchStatementsService, \
    Statement, ServiceMeta, PropositionType, DiagnosticProposition, \
    TherapeuticResponseProposition, PrognosticProposition, Document, Method


logger = logging.getLogger("metakb.new_query")
logger.setLevel(logging.DEBUG)  # different level?


class QueryHandler:
    """Provide querying services."""

    def __init__(self, uri: str = "",
                 creds: Tuple[str, str] = ("", ""),
                 normalizers: VICCNormalizers = VICCNormalizers()) -> None:
        """Initialize neo4j driver and the VICC normalizers.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        """
        self.graph = Graph(uri, creds)
        self.vicc_normalizers = normalizers
        self.driver = None

    def _get_driver(self) -> Driver:
        """Acquire driver from graph for creating sessions.
        :return: Neo4j driver instance.
        :raise: DriverError if attempt to instantiate driver fails
        """
        if self.driver is None:
            self.driver = self.graph.driver
            if self.driver is None:
                raise DriverError
        return self.graph.driver  # type: ignore

    def _add_normalized_term(self, term: str, term_type: str)\
            -> Tuple[str, Dict[str, str]]:
        """Get normalized gene, disease, or therapy concept.
        :param str term: query term to normalize
        :param str term_type: one of {"disease", "therapy", "gene",
        "variation"}
        :return: tuple containing query match clause and return value key/value
        :raise: ValueError if unrecognized term_type used
        :raise: NormalizationException if normalization fails

        TODO
         * probably no need to get so funky w/ string interpollation,
         just do some if/thens to get normalized terms, then more if/thens
         to make the string
        """
        param_key = f"{term_type}_id"
        if term_type == "variation":
            normalizer = self.vicc_normalizers.normalize_variation
            relation = "-[:HAS_SUBJECT]->"
            if term.lower().startswith("ga4gh:sq."):  # TODO does this exist?
                property = f"{{location_sequence_id: ${param_key}}}"
            else:
                property = f"{{id: ${param_key}}}"
        else:
            property = f"{{id:${param_key}}}"
            if term_type == "disease":
                normalizer = self.vicc_normalizers.normalize_disease
                relation = "-[:HAS_OBJECT_QUALIFIER]->"
            elif term_type == "therapy":
                normalizer = self.vicc_normalizers.normalize_therapy
                relation = "-[:HAS_OBJECT]->"
            elif term_type == "gene":
                normalizer = self.vicc_normalizers.normalize_gene
                relation = """-[:HAS_SUBJECT]->(v:Variation)
                <-[:DESCRIBES]-(:VariationDescriptor)-[:HAS_GENE]
                ->(:GeneDescriptor)-[:DESCRIBES]->"""
            else:
                raise ValueError(f"Unrecognized term type: {term_type}")

        if term.startswith(("ga4gh:VA.", "ga4gh:CNV.", "ga4gh:VH.")):
            normalized_response = (None, term)
        else:
            normalized_response = normalizer([term])

        if normalized_response is None:
            raise NormalizationException(
                f"Unable to normalize {term_type}: {term}")

        label = term_type.capitalize()
        term_alias = term_type[0]
        clause = f"MATCH (p) {relation} ({term_alias}:{label} {property})"
        param = {param_key: normalized_response[1]}
        return (clause, param)

    _match_value_lookup = {
        "therapy": "OPTIONAL MATCH (p)-[:HAS_OBJECT]->(t:Therapy)",
        "variation": "MATCH (p)-[:HAS_SUBJECT]->(v:Variation)",
        "disease": "MATCH (p)-[:HAS_OBJECT_QUALIFIER]->(d:Disease)",
    }

    def _get_search_parameters(self, variation: Optional[str],
                               disease: Optional[str], therapy: Optional[str],
                               gene: Optional[str])\
            -> Tuple[List[str], Dict[str, str], List[str]]:
        """Given search terms, produce normalized query clauses and return
        variable names.
        :param Optional[str] variation: variation search term
        :param Optional[str] disease: disease search term
        :param Optional[str] therapy: therapy search term
        :param Optional[str] gene: gene search term
        :return: Tuple containing query match clauses, return variable names,
        values to interpollate into the query, and a list of warnings.
        """
        match_clauses, values, warnings = [], {}, []

        for term, term_type in ((variation, "variation"), (disease, "disease"),
                                (therapy, "therapy"), (gene, "gene")):
            if term:
                try:
                    match_clause, value = self._add_normalized_term(term,
                                                                    term_type)
                except NormalizationException as e:
                    warnings.append(e.__str__())
                else:
                    match_clauses.append(match_clause)
                    values = {**values, **value}
            elif term_type != "gene":
                match_clauses.append(self._match_value_lookup[term_type])

        return match_clauses, values, warnings

    _prop_lookup = {
        PropositionType.PREDICTIVE.value: TherapeuticResponseProposition,
        PropositionType.DIAGNOSTIC.value: DiagnosticProposition,
        PropositionType.PROGNOSTIC.value: PrognosticProposition
    }

    def _get_vd_from_data(self, vd: Dict) -> VariationDescriptor:
        """Build VariationDescriptor given a Neo4j query result
        :param Dict vd: descriptor from Neo4j query result
        :return: complete VariationDescriptor object
        """
        assert vd["type"] == "VariationDescriptor"   # TODO debug remove
        extension_fields = (
            "moa_representative_coordinate", "moa_rsid",
            "civic_actionability_score",
            "civic_representative_coordinate"
        )
        for field in extension_fields:
            if field in vd:
                del vd[field]

        new_extensions = []
        for extension in vd.get("extensions", []):
            if extension["value"] is not None:
                try:
                    loaded = json.loads(extension["value"])
                except (json.JSONDecodeError, TypeError):
                    new_extensions.append(extension)
                else:
                    extension["value"] = loaded
                    new_extensions.append(extension)
        vd["extensions"] = new_extensions

        expressions = []
        for key in ["expressions_genomic", "expressions_protein",
                    "expressions_transcript"]:
            if key in vd:
                for value in vd[key]:
                    expressions.append(
                        Expression(
                            syntax=f"hgvs:{key.split('_')[-1]}",
                            value=value,
                            version=None
                        ).dict()
                    )
                del vd[key]
        if expressions:
            vd["expressions"] = expressions

        if vd.get("variation") is not None:
            vd["variation"] = json.loads(vd["variation"])

        return VariationDescriptor(**vd)

    def _get_response_data(self, response: Dict, data: List[Dict],
                           detail: bool) -> SearchService:
        """Construct response from query data.
        :param Dict response: in-progress response object
        :param List[Dict] data: response data from Neo4j query call
        :param bool detail: if true, build descriptors and related objects
        :returns: completed SearchService response
        """
        propositions, statements = {}, {}
        therapy_ds, disease_ds, variation_ds, gene_ds = {}, {}, {}, {}
        documents, methods = {}, {}

        for result in data:
            proposition_id = result["proposition"]["id"]
            if proposition_id not in propositions:
                prop_type = result["proposition"]["type"]
                propositions[proposition_id] = self._prop_lookup[prop_type](
                    **result["proposition"])
            statement_id = result["statement"]["id"]
            if statement_id not in statements:
                statements[statement_id] = Statement(**result["statement"])
            if detail:
                if result.get("therapy_descriptor") is not None:
                    td_id = result["therapy_descriptor"]["id"]
                    if td_id not in therapy_ds:
                        therapy_ds[td_id] = ValueObjectDescriptor(
                            **result["therapy_descriptor"])
                dd_id = result["disease_descriptor"]["id"]
                if dd_id not in disease_ds:
                    disease_ds[dd_id] = ValueObjectDescriptor(
                        **result["disease_descriptor"])
                vd_id = result["variation_descriptor"]["id"]
                if vd_id not in variation_ds:
                    variation_ds[vd_id] = self._get_vd_from_data(
                        result["variation_descriptor"]
                    )
                gd_id = result["gene_descriptor"]["id"]
                if gd_id not in gene_ds:
                    gene_ds[gd_id] = ValueObjectDescriptor(
                        **result["gene_descriptor"])
                doc_id = result["document"]["id"]
                if doc_id not in documents:
                    documents[doc_id] = Document(**result["document"])
                method_id = result["method"]["id"]
                if method_id not in documents:
                    result["method"]["version"] = json.loads(
                        result["method"]["version"])
                    methods[method_id] = Method(**result["method"])

        # TODO had some space here? maybe was working on something?
        if propositions and statements:
            return SearchService(
                matches=Matches(
                    statements=list(statements.keys()),
                    propositions=list(propositions.keys())),
                statements=list(statements.values()),
                propositions=list(propositions.values()),
                therapy_descriptors=list(therapy_ds.values()),
                disease_descriptors=list(disease_ds.values()),
                variation_descriptors=list(variation_ds.values()),
                gene_descriptors=list(gene_ds.values()),
                methods=list(methods.values()),
                documents=list(documents.values()),
                **response
            )
        elif response["query"].statement_id:
            pass  # do an extra query to see if statement ID is valid
        else:
            response["warnings"] += [
                "Could not find statements associated with the queried concepts."  # noqa: E501
            ]
            return SearchService(
                matches=Matches(
                    statements=[],
                    propositions=[]
                ),
                statements=[],
                propositions=[],
                **response
            )

    _match_proposition = "MATCH (p:Proposition)"

    _match_statement = "MATCH (s:Statement)-[:DEFINED_BY]->(p)"

    _match_descriptors = [
        "OPTIONAL MATCH (s)-[:HAS_THERAPY]-(td:TherapyDescriptor)",
        "MATCH (s)-[:HAS_DISEASE]-(dd:DiseaseDescriptor)",
        "MATCH (s)-[:HAS_VARIATION]-(vd:VariationDescriptor)",
        "MATCH (vd)-[:HAS_GENE]->(gd:GeneDescriptor)",
    ]

    _match_descriptors_detail = _match_descriptors + [
        "MATCH (gd)-[:DESCRIBES]->(g:Gene)",
        "OPTIONAL MATCH (vd)-[:IN_VARIATION_GROUP]->(vg:VariationGroup)"
    ]

    _match_ev = [
        "OPTIONAL MATCH (s)-[:CITES]->(cite_statement:Statement)",
        "OPTIONAL MATCH (s)-[:CITES]->(cite_doc:Document)"
        "MATCH (s)-[:USES_METHOD]->(m:Method)"
    ]

    _return_proposition = """p{
        .*,
        subject: v.id,
        object_qualifier: d.id,
        object: t.id
    }"""

    _return_vd = """vd{
        .*,
        variation_id: v.id,
        type: "VariationDescriptor",
        extensions: COLLECT(
            {name: "variant_group", value: vg{.*, type: "variant_group"}}
        ) + {
            name: "civic_actionability_score",
            value: vd.civic_actionability_score
        } + {
            name: "civic_representative_coordinate",
            value: vd.civic_representative_coordinate
        } + {
            name: "moa_representative_coordinate",
            value: vd.moa_representative_coordinate
        } + {
            name: "moa_rsid", value: vd.moa_rsid
        },
        gene_context: gd{.*, gene_id: g.id, type: "GeneDescriptor"}
    }
    """

    _return_dd = "dd{.*, disease_id: d.id, type: \"DiseaseDescriptor\"}"

    _return_td = "td{.*, therapy_id: t.id, type: \"TherapyDescriptor\"}"

    _return_statement_enref = """s{
        .*,
        proposition: p.id,
        variation_descriptor: vd.id,
        therapy_descriptor: td.id,
        disease_descriptor: dd.id,
        supported_by: COLLECT(DISTINCT cite_doc.id)
            + COLLECT(DISTINCT cite_statement.id),
        method: m.id
    } AS statement
    """

    def search(self, variation: Optional[str] = None,
               disease: Optional[str] = None, therapy: Optional[str] = None,
               gene: Optional[str] = None, statement_id: Optional[str] = None,
               detail: bool = False) -> SearchService:
        """Get statements and propositions from queried concepts.

        :param Optional[str] variation: Variation query
        :param Optional[str] disease: Disease query
        :param Optional[str] therapy: Therapy query
        :param Optional[str] gene: Gene query
        :param Optional[str] statement_id: Statement ID query
        :param bool detail: Whether or not to display all descriptors,
            methods, and documents
        :return: complete SearchService object

        * How to handle extra mess added by gene search values?
        * still too messy?
        * in detail, how to get full statements that support other statements
        * ensure correct response if requested statement ID doesn't exist
        * warning for no response:
            "Could not find statements associated with the queried concepts."
        """
        response = {
            "warnings": [],
            "query": SearchQuery(variation=variation, disease=disease,
                                 therapy=therapy, gene=gene,
                                 statement_id=statement_id, detail=detail),
            "service_meta_": ServiceMeta().dict()
        }
        if not any([variation, disease, therapy, gene, statement_id]):
            response["warnings"].append("No parameters were entered.")
            return SearchService(**response)

        search_params = self._get_search_parameters(variation, disease,
                                                    therapy, gene)
        if search_params[2]:
            response["warnings"] += search_params[2]
            return SearchService(**response)

        clauses = search_params[0] + [self._match_proposition]
        values = search_params[1]

        # TODO what if statement ID doesnt exist?
        # optional match + check if null in response?
        if statement_id:
            clauses.append("MATCH (s:Statement {id:$s_id})-[:DEFINED_BY]->(p)")
            values["s_id"] = statement_id
        else:
            clauses.append(self._match_statement)
        clauses += self._match_ev

        return_variables = [
            self._return_proposition + " AS proposition",
            self._return_statement_enref
        ]

        if detail:
            clauses += self._match_descriptors_detail
            return_variables += [
                self._return_td + "AS therapy_descriptor",
                self._return_dd + "AS disease_descriptor",
                self._return_vd + "AS variation_descriptor",
                "gd{ .*, gene_id: g.id, type: \"GeneDescriptor\"} AS gene_descriptor",  # noqa: E501
                "cite_doc{.*, type: \"Document\"} AS document",
                "m{.*, type: \"Method\"} AS method"
            ]
        else:
            clauses += self._match_descriptors

        clauses.append(f"RETURN {', '.join(return_variables)}")
        query = "\n".join(clauses)

        with self._get_driver().session() as session:
            data = session.read_transaction(self._get_query_data, query,
                                            **values)

        return self._get_response_data(response, data, detail)

    _search_statements_return_subclauses = [
        "proposition: " + _return_proposition,
        "variation_descriptor: " + _return_vd,
        "disease_descriptor: " + _return_dd,
        "therapy_descriptor: " + _return_td,
        "method: m",
        "supported_by: COLLECT(DISTINCT cite_doc{.*}) "
        "+ COLLECT(DISTINCT cite_statement.id)"
    ]

    def search_statements(
            self, variation: Optional[str] = None,
            disease: Optional[str] = None, therapy: Optional[str] = None,
            gene: Optional[str] = None, statement_id: Optional[str] = None
    ) -> SearchStatementsService:
        """Get nested statements from queried concepts

        :param Optional[str] variation: Variation query
        :param Optional[str] disease: Disease query
        :param Optional[str] therapy: Therapy query
        :param Optional[str] gene: Gene query
        :param Optional[str] statement_id: Statement ID query
        :return: A dictionary containing the statements with nested
            propositions, descriptors, methods, and supported by documents
        """
        response = {
            "warnings": [],
            "query": SearchStatementsQuery(
                variation=variation, disease=disease, therapy=therapy,
                gene=gene, statement_id=statement_id,),
            "service_meta_": ServiceMeta().dict()
        }
        if not any([variation, disease, therapy, gene, statement_id]):
            response["warnings"].append("No parameters were entered.")
            return SearchStatementsService(
                matches=Matches(statements=[], propositions=[]),
                **response)

        search_params = self._get_search_parameters(variation, disease,
                                                    therapy, gene)
        if search_params[2]:
            response["warnings"] += search_params[2]
            return SearchStatementsService(
                matches=Matches(statements=[], propositions=[]),
                **response)

        clauses = search_params[0] + [self._match_proposition]
        values = search_params[1]

        # TODO what if statemnet ID doesnt exist?
        # optional match + check if null in response?
        if statement_id:
            clauses.append("MATCH (s:Statement {id:$s_id})-[:DEFINED_BY]->(p)")
            values["s_id"] = statement_id
        else:
            clauses.append(self._match_statement)
        clauses += self._match_ev + self._match_descriptors_detail

        query = "\n".join(clauses)
        return_section = ", ".join(self._search_statements_return_subclauses)
        query += f"RETURN s{{.*, {return_section}}} AS statement"

        with self._get_driver().session() as session:
            data = session.read_transaction(self._get_query_data, query,
                                            **search_params[1])
        propositions = []
        statements: Dict[str, NestedStatementResponse] = {}

        for result in data:
            statement_id: str = result["statement"]["id"]
            if statement_id not in statements:
                statement = result["statement"]
                statement["variation_descriptor"] = self._get_vd_from_data(
                    statement["variation_descriptor"]
                )
                statement["method"]["version"] = json.loads(
                    statement["method"]["version"])
                propositions.append(result["statement"]["proposition"]["id"])
                statements[statement_id] = NestedStatementResponse(
                    **result["statement"])

        return SearchStatementsService(
            matches=Matches(
                statements=list(statements.keys()),
                propositions=list(set(propositions))
            ),
            statements=list(statements.values()),
            **response
        )

    # use conditional subqueries to avoid retrieving related info unless
    # node labels match.
    _search_by_id_query = """MATCH (n {id:$node_id})
    CALL {
        WITH n WITH n
        WHERE (n:TherapyDescriptor)
        MATCH (n)-[:DESCRIBES]->(t:Therapy)
        RETURN n{.*, therapy_id: t.id, type:"TherapyDescriptor"} AS value

        UNION WITH n WITH n
        WHERE (n:GeneDescriptor)
        MATCH (n)-[:DESCRIBES]->(g:Gene)
        RETURN n{.*, gene_id: g.id, type:"GeneDescriptor"} AS value

        UNION WITH n WITH n
        WHERE (n:DiseaseDescriptor)
        MATCH (n)-[:DESCRIBES]->(d:Disease)
        RETURN n{.*, disease_id: d.id, type:"DiseaseDescriptor"} AS value

        UNION WITH n WITH n
        WHERE (n:VariationDescriptor)
        MATCH (n)-[:DESCRIBES]->(v:Variation)
        MATCH (n)-[:HAS_GENE]->(gd:GeneDescriptor)
        OPTIONAL MATCH (n)-[:IN_VARIATION_GROUP]->(vg:VariationGroup)
        RETURN n{
            .*,
            variation: v.variation,
            variation_id: v.id,
            gene_context: gd.id,
            type:"VariationDescriptor",
            extensions: COLLECT(
                {name: "variant_group", value: vg{.*, type: "variant_group"}}
            ) + {
                name: "civic_actionability_score",
                value: n.civic_actionability_score
            } + {
                name: "civic_representative_coordinate",
                value: n.civic_representative_coordinate
            } + {
                name: "moa_representative_coordinate",
                value: n.moa_representative_coordinate
            } + {
                name: "moa_rsid", value: n.moa_rsid
            }
        } AS value

        UNION WITH n WITH n
        WHERE (n:Statement)
        MATCH (n)-[:HAS_VARIATION]->(vd:VariationDescriptor)
        MATCH (n)-[:HAS_DISEASE]->(dd:DiseaseDescriptor)
        OPTIONAL MATCH (n)-[:HAS_THERAPY]->(td:TherapyDescriptor)
        MATCH (n)-[:DEFINED_BY]->(p:Proposition)
        MATCH (n)-[:USES_METHOD]->(m:Method)
        OPTIONAL MATCH (n)-[:CITES]->(cite)
        RETURN n{
            .*,
            variation_descriptor: vd.id,
            disease_descriptor: dd.id,
            therapy_descriptor: td.id,
            proposition: p.id,
            method: m.id,
            supported_by: COLLECT(cite.id),
            type: "Statement"
        } AS value

        UNION WITH n WITH n
        WHERE (n:TherapeuticResponse) OR (n:Diagnostic) OR (n:Prognostic)
        MATCH (n)-[:HAS_SUBJECT]->(v:Variation)
        OPTIONAL MATCH (n)-[:HAS_OBJECT]->(t:Therapy)
        MATCH (n)-[:HAS_OBJECT_QUALIFIER]->(d:Disease)
        RETURN n{
            .*,
            subject: v.id,
            object: t.id,
            object_qualifier: d.id
        } AS value

        UNION WITH n WITH n
        WHERE (n:Document)
        RETURN n{.*, type:"Document"} AS value

        UNION WITH n WITH n
        WHERE (n:Method)
        RETURN n{.*, type:"Method"} AS value
    }
    RETURN value
    """

    def search_by_id(self, node_id: str) -> SearchIDService:
        """Get node information given id query

        :param str node_id: node ID value provided by user
        :return: completed search response object
        """
        response = {
            "query": node_id,
            "warnings": [],
            "service_meta_": ServiceMeta().dict()
        }

        if not node_id:
            response["warnings"].append("No parameters were entered.")
        elif node_id.strip() == "":
            response["warnings"].append("Cannot enter empty string.")
        else:
            node_id = node_id.strip()
            if "%" not in node_id and ":" in node_id:
                # TODO double check ????
                concept_name = quote(node_id.split(":", 1)[1])
                node_id = \
                    f"{node_id.split(':', 1)[0]}" \
                    f":{concept_name}"

        # TODO handle warnings

        with self._get_driver().session() as session:
            data = session.read_transaction(self._get_query_data,
                                            self._search_by_id_query,
                                            node_id=node_id)
        if len(data) == 0:
            response["warnings"].append(f"Node: {node_id} does not exist.")
            return SearchIDService(**response)
        value = data[0]["value"]
        value_type = value.get("type")
        if value_type == "Statement":
            response["statement"] = Statement(**value)
        elif value_type in (e.value for e in PropositionType):
            response["proposition"] = self._prop_lookup[value_type](**value)
        elif value_type == "TherapyDescriptor":
            response["therapy_descriptor"] = ValueObjectDescriptor(**value)
        elif value_type == "DiseaseDescriptor":
            response["disease_descriptor"] = ValueObjectDescriptor(**value)
        elif value_type == "GeneDescriptor":
            response["gene_descriptor"] = ValueObjectDescriptor(**value)
        elif value_type == "VariationDescriptor":
            response["variation_descriptor"] = self._get_vd_from_data(value)
        elif value_type == "Document":
            response["document"] = Document(**value)
        elif value_type == "Method":
            value["version"] = json.loads(value["version"])
            response["method"] = Method(**value)
        else:
            raise ValueError  # TODO handle fail??
        return SearchIDService(**response)

    @staticmethod
    def _get_query_data(tx: Transaction, query, **properties):
        """Run raw query string and properties kwargs."""
        # TODO WORKING
        # maybe put this in the Graph DB instance?
        return tx.run(query.replace("\n", " "), **properties).data()
