"""Module for queries."""
import logging  # TODO debug
from typing import Optional, Tuple, Dict, List

from neo4j import Driver
from neo4j.exceptions import DriverError
from neo4j.work.transaction import Transaction

from metakb.database import Graph
from metakb.normalizers import VICCNormalizers
from metakb.exceptions import NormalizationException
from metakb.schemas import SearchQuery, Matches, SearchService, Statement, \
    ServiceMeta


logger = logging.getLogger("metakb.new_query")
logger.setLevel(logging.DEBUG)


class QueryHandler:
    """Provide querying services."""

    def __init__(self, uri: str = "",
                 creds: Tuple[str, str] = ("", "")) -> None:
        """Initialize neo4j driver and the VICC normalizers.
        :param str uri: address of Neo4j DB
        :param Tuple[str, str] credentials: tuple containing username and
            password
        """
        self.graph = Graph(uri, creds)
        self.vicc_normalizers = VICCNormalizers()
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
                relation = """-[:HAS_OBJECT]->(v:Variation)
                <-[:DESCRIBES]-(:VariationDescriptor)-[:HAS_GENE]
                ->(:GeneDescriptor)-[:DESCRIBES]->"""  # noqa: E501
            else:
                raise ValueError(f"Unrecognized term type: {term_type}")

        normalized_response = normalizer([term])
        if (normalized_response is None) or \
                (term_type == "variation" and not
                 normalized_response[1].startswith(
                ("ga4gh:VA.", "ga4gh:CNV.", "ga4gh:VH")
                 )):
            raise NormalizationException(
                f"Unable to normalize {term_type}: {term}")

        label = term_type.capitalize()
        term_alias = term_type[0]
        clause = f"MATCH (p) {relation} ({term_alias}:{label} {property})"
        param = {param_key: normalized_response[1]}
        return (clause, param)

    _optional_matches = {
        "therapy": "OPTIONAL MATCH (p)-[:HAS_OBJECT]->(t:Therapy)",
        "variation": "OPTIONAL MATCH (p)-[:HAS_SUBJECT]->(v:Variation)",
        "disease": "OPTIONAL MATCH (p)-[:HAS_OBJECT_QUALIFIER]->(d:Disease)"
    }

    def _get_search_parameters(self, variation: Optional[str],
                               disease: Optional[str], therapy: Optional[str],
                               gene: Optional[str])\
            -> Tuple[List[str], List[str], Dict[str, str], List[str]]:
        """Given search terms, produce normalized query clauses and return
        variable names.
        :param Optional[str] variation: variation search term
        :param Optional[str] disease: disease search term
        :param Optional[str] therapy: therapy search term
        :param Optional[str] gene: gene search term
        :return: Tuple containing query match clauses, return variable names,
        values to interpollate into the query, and a list of warnings.
        """
        match_clauses = []
        values = {}
        warnings = []
        return_variables = ["v.id", "d.id", "t.id"]

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
                    if term_type == "gene":
                        return_variables.append("g.id")
            elif term_type != "gene":
                match_clauses.append(self._optional_matches[term_type])

        return match_clauses, return_variables, values, warnings

    @staticmethod
    def _get_proposition_from_data(result: Dict) -> Dict:
        """Given query result data, extract a Proposition object
        :param Dict result: result data returned by Neo4j query
        :return: complete Proposition-like dict instance
        """
        result_proposition = result["p"]
        params = {
            **result_proposition,
            "subject": result["v.id"],
            "object_qualifier": result["d.id"]
        }
        if params["type"] == "therapeutic_response_proposition":
            params["object"] = result["t.id"]
        return params

    @staticmethod
    def _get_statement_from_data(result: Dict, detail: bool,
                                 proposition_type: str) -> Statement:
        """Given query result data, extract a Statement object
        :param Dict result: result data returned by Neo4j query
        :param bool detail: if true, result should contain complete descriptor
        objects, not just descriptor IDs
        :param str proposition_type: type of proposition
        :return: a complete Statement instance
        """
        statement_params = {
            **result["s"],
            "method": result["m.id"],
            "supported_by": result["cites"],
            "proposition": result["p"]["id"]
        }
        if detail:
            statement_params["variation_descriptor"] = result["vd"]["id"]
            statement_params["disease_descriptor"] = result["dd"]["id"]
            if proposition_type == "therapeutic_response_proposition":
                statement_params["therapy_descriptor"] = result["td"]["id"]
        else:
            statement_params["variation_descriptor"] = result["vd.id"]
            statement_params["disease_descriptor"] = result["dd.id"]
            if proposition_type == "therapeutic_response_proposition":
                statement_params["therapy_descriptor"] = result["td.id"]
        return Statement(**statement_params)

    def search(self, variation: Optional[str] = None,
               disease: Optional[str] = None, therapy: Optional[str] = None,
               gene: Optional[str] = None, statement_id: Optional[str] = None,
               detail: bool = False):
        """TODO docstring

        * How to handle extra mess added by gene search values?
        * get detail flag stuff
        * still too messy?
        """
        response = {
            "warnings": [],
            "query": SearchQuery(
                variation=variation,
                disease=disease,
                therapy=therapy,
                gene=gene,
                statement_id=statement_id,
                detail=detail
            ),
            "service_meta_": ServiceMeta().dict()
        }
        if not any([variation, disease, therapy, gene, statement_id]):
            response["warnings"].append("No parameters were entered.")
            return None

        search_params = self._get_search_parameters(variation, disease,
                                                    therapy, gene)
        if search_params[3]:
            response["warnings"] += search_params[3]
            return response
        clauses = ["MATCH (p:Proposition)"] + search_params[0]
        return_variables = search_params[1]
        values = search_params[2]

        # TODO optional match + check if null in response?
        if statement_id:
            clauses.append("MATCH (s:Statement {id:$s_id})-[:DEFINED_BY]->(p)")
            values["s_id"] = statement_id
        else:
            clauses.append("MATCH (s:Statement)-[:DEFINED_BY]->(p)")

        return_variables += ["p", "s"]
        clauses += [
            "OPTIONAL MATCH (s)-[:HAS_THERAPY]-(td:TherapyDescriptor)",
            "OPTIONAL MATCH (s)-[:HAS_DISEASE]-(dd:DiseaseDescriptor)",
            "OPTIONAL MATCH (s)-[:HAS_VARIATION]-(vd:VariationDescriptor)",
        ]
        if detail:
            return_variables += ["td", "dd", "vd"]
        else:
            return_variables += ["td.id", "dd.id", "vd.id"]

        clauses += [
            "MATCH (s)-[:CITES]->(cite)",
            "MATCH (s)-[:USES_METHOD]->(m:Method)"
        ]
        return_variables += ["COLLECT(cite.id) AS cites", "m.id"]

        clauses.append(f"RETURN {','.join(return_variables)}")
        query = " ".join(clauses)

        logger.debug(query)
        logger.debug(values)
        with self._get_driver().session() as session:
            data = session.read_transaction(self._get_query_data, query,
                                            **values)

        # pretty sure this will spit out redundant IDs
        propositions, statements = [], []
        proposition_ids, statement_ids = [], []
        for result in data:
            proposition_id = result["p"]["id"]
            if proposition_id not in proposition_ids:
                proposition = self._get_proposition_from_data(result)
                propositions.append(proposition)
                proposition_ids.append(proposition_id)

            statement_id = result["s"]["id"]
            if statement_id not in statement_ids:
                statement = self._get_statement_from_data(result, detail,
                                                          result["p"]["type"])
                statements.append(statement)
                statement_ids.append(statement_id)

        return SearchService(
            matches=Matches(
                statements=statement_ids, propositions=proposition_ids),
            statements=statements,  # type: ignore
            propositions=propositions,  # type: ignore
            **response
        )

    @staticmethod
    def _get_query_data(tx: Transaction, query, **properties):
        # TODO WORKING
        # maybe put this in the Graph DB instance?
        return tx.run(query, **properties).data()


# q = QueryHandler()
# q.search(disease="cancer", therapy="rxcui:282388")
# q.search(variation="egfr l858r", disease="ncit:C2926", therapy="afatinib")
# q._get_driver().close()
