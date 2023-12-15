"""Validate property and relationship rules for graph DB."""
import json
from typing import Optional

import pytest

from metakb.database import Graph
from metakb.schemas.app import SourceName


@pytest.fixture(scope="module")
def sources_count():
    """Get length of sources"""
    return len(SourceName)


@pytest.fixture(scope="module")
def graph():
    """Return graph object."""
    g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
    yield g
    g.close()


@pytest.fixture(scope="module")
def get_node_by_id(graph: Graph):
    """Return node by its ID"""
    def _get_node(node_id: str):
        query = f"MATCH (n {{id: '{node_id}'}}) RETURN (n)"
        with graph.driver.session() as s:
            record = s.run(query).single(strict=True)
        return record[0]
    return _get_node


@pytest.fixture(scope="module")
def check_unique_property(graph: Graph):
    """Verify that nodes satisfy uniqueness property"""
    def _check_function(label: str, property: str):
        query = f"""
        MATCH (x:{label})
        WITH x.{property} AS {property}, COUNT(x) AS x_count
        WHERE x_count > 1
        RETURN COUNT({property})
        """
        with graph.driver.session() as s:
            record = s.run(query).single()

        assert record.values()[0] == 0
    return _check_function


@pytest.fixture(scope="module")
def check_single_label(graph: Graph):
    """Check that nodes don't contain additional labels"""
    def _check_function(label: str):
        query = f"""
        MATCH (a:{label})
        WHERE SIZE(LABELS(a)) > 1
        RETURN COUNT(a)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0
    return _check_function


@pytest.fixture(scope="module")
def check_study_relation(graph: Graph):
    """Check that node is used in a study."""
    def _check_function(value_label: str):
        query = f"""
        MATCH (d:{value_label})
        OPTIONAL MATCH (d)<-[:HAS_{value_label.upper()}]-(s:Study)
        WITH d, COUNT(s) as s_count
        WHERE s_count < 1
        RETURN COUNT(s_count)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0
    return _check_function


@pytest.fixture(scope="module")
def check_relation_count(graph: Graph):
    """Check that the quantity of relationships from one Node type to another
    are within a certain range.
    """
    def _check_function(self_label: str, other_label: str, relation: str,
                        min: int = 1, max: Optional[int] = 1,
                        direction: Optional[str] = "out"):
        if direction == "out":
            rel_query = f"-[:{relation}]->"
        elif direction == "in":
            rel_query = f"<-[:{relation}]-"
        elif direction is None:
            rel_query = f"-[:{relation}]-"
        else:
            raise ValueError("direction must be 'out', 'in' or None")
        query = f"""
        MATCH (s:{self_label})
        OPTIONAL MATCH (s){rel_query}(d:{other_label})
        WITH s, COUNT(d) as d_count
        WHERE d_count < {min}
            {f"OR d_count > {max}" if max is not None else ""}
        RETURN COUNT(s)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0
    return _check_function


def test_gene_rules(check_unique_property, check_single_label, check_relation_count, get_node_by_id):
    """Verify property and relationship rules for Gene nodes."""
    check_unique_property("Gene", "id")
    check_single_label("Gene")
    check_relation_count("Gene", "Qualifier", "HAS_GENE_CONTEXT", direction="in", min=1, max=None)

    gene = get_node_by_id("civic.gid:5")
    assert set(gene.keys()) == {"gene_normalizer_id", "label", "id"}
    assert gene["gene_normalizer_id"] == "hgnc:1097"
    assert gene["label"] == "BRAF"


def test_qualifier_rules(check_unique_property, check_single_label, check_relation_count):
    """Verify property and relationship rules for Qualifier nodes."""
    check_unique_property("Qualifier", "alleleOrigin")
    check_single_label("Qualifier")
    check_relation_count("Qualifier", "Gene", "HAS_GENE_CONTEXT", direction="out", max=None)


def test_variation_rules(graph, check_unique_property, check_relation_count, get_node_by_id):
    """Verify property and relationship rules for Variation nodes."""
    check_unique_property("Variation", "id")
    check_relation_count("CategoricalVariation", "Variation", "HAS_DEFINING_CONTEXT", max=1)

    # all Alleles are Variations and all Variations are Alleles
    label_query = """
    MATCH (v:Variation)
    WHERE NOT (v:Allele)
    RETURN COUNT(v)
    UNION
    MATCH (v:Allele)
    WHERE NOT (v:Variation)
    RETURN COUNT(v)
    """
    with graph.driver.session() as s:
        record = s.run(label_query).single()
    assert record.values()[0] == 0

    cv = get_node_by_id("civic.mpid:12")
    assert set(cv.keys()) == {
        "id",
        "label",
        "description",
        "aliases",
        "civic_molecular_profile_score",
        "civic_representative_coordinate",
        "mappings",
        "variant_types"
    }
    assert cv["label"] == "BRAF V600E"
    assert cv["description"] and isinstance(cv["description"], str)
    assert cv["aliases"] and isinstance(cv["aliases"], list)
    assert isinstance(cv["civic_molecular_profile_score"], float)
    crc = json.loads(cv["civic_representative_coordinate"])
    assert set(crc.keys()) == {
        "ensembl_version",
        "reference_build",
        "reference_bases",
        "variant_bases",
        "representative_transcript",
        "chromosome",
        "start",
        "stop",
        "type"
    }
    mappings = json.loads(cv["mappings"])
    for m in mappings:
        assert m["coding"] and isinstance(m["coding"], dict)
        assert m["relation"] and isinstance(m["relation"], str)

    variant_types = json.loads(cv["variant_types"])
    for vt in variant_types:
        assert set(vt.keys()) == {"label", "system", "version", "code"}

    v = get_node_by_id("ga4gh:VA.4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO")
    assert set(v.keys()) == {"id", "label", "digest", "state", "expression_hgvs_p", "expression_hgvs_c", "expression_hgvs_g"}

    assert v["label"] == "V600E"
    assert v["digest"] == "4XBXAxSAk-WyAu5H0S1-plrk_SCTW1PO"
    assert json.loads(v["state"]) == {"type": "LiteralSequenceExpression", "sequence": "E"}
    assert v["expression_hgvs_p"] == ["NP_004324.2:p.Val600Glu"]
    assert set(v["expression_hgvs_c"]) == {"NM_004333.4:c.1799T>A", "ENST00000288602.6:c.1799T>A"}
    assert v["expression_hgvs_g"] == ["NC_000007.13:g.140453136A>T"]


def test_location_rules(check_unique_property):
    """Verify property and relationship rules for Location nodes."""
    check_unique_property("Location", "id")


def test_therapeutic_procedure_rules(check_unique_property):
    """Verify property and relationship rules for Therapeutic Procedure nodes."""
    check_unique_property("TherapeuticProcedure", "id")


def test_disease_rules(check_unique_property):
    """Verify property and relationship rules for disease nodes."""
    check_unique_property("Disease", "id")


def test_study_rules(graph: Graph, check_unique_property, check_relation_count):
    """Verify property and relationship rules for Study nodes."""
    check_unique_property("Study", "id")

    check_relation_count("Study", "CategoricalVariation", "HAS_VARIANT")
    check_relation_count("Study", "Condition", "HAS_TUMOR_TYPE")
    check_relation_count("Study", "TherapeuticProcedure", "HAS_THERAPEUTIC", min=1)
    check_relation_count("Study", "Coding", "HAS_STRENGTH")
    check_relation_count("Study", "Method", "IS_SPECIFIED_BY", max=None)
    check_relation_count("Study", "Qualifier", "HAS_QUALIFIERS")

    cite_query = """
    MATCH (s:Study)
    OPTIONAL MATCH (s)-[:IS_REPORTED_IN]->(d:Document)
    WITH s, COUNT(d) as d_count
    WHERE d_count < 1
    RETURN COUNT(s)
    """
    with graph.driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0


def test_document_rules(graph, check_unique_property, check_single_label, check_relation_count):
    """Verify property and relationship rules for Document nodes."""
    check_unique_property("Document", "id")
    check_single_label("Document")

    # PMIDs: 31779674 and 35121878 are do not have this relationship
    is_reported_in_query = """
    MATCH (s:Document)
    OPTIONAL MATCH (s)<-[:IS_REPORTED_IN]-(d:Study)
    WITH s, COUNT(d) as d_count
    WHERE (d_count < 1) AND (s.pmid <> 31779674) AND (s.pmid <> 35121878)
    RETURN COUNT(s)
    """
    with graph.driver.session() as s:
        record = s.run(is_reported_in_query).single()
    assert record.values()[0] == 0


def test_method_rules(check_unique_property, check_single_label, check_relation_count):
    """Verify property and relationship rules for Method nodes."""
    check_unique_property("Method", "id")
    check_single_label("Method")
    check_relation_count("Method", "Study", "IS_SPECIFIED_BY", max=None,
                         direction="in")


def test_no_lost_nodes(graph: Graph):
    """Verify that no unlabeled or isolated nodes have been created."""
    # non-normalizable nodes can be excepted
    labels_query = """
    MATCH (n)
    WHERE size(labels(n)) = 0
    AND NOT (n)<-[:IS_REPORTED_IN]-(:Study)
    RETURN COUNT(n)
    """
    with graph.driver.session() as s:
        record = s.run(labels_query).single()
    assert record.values()[0] == 0

    rels_query = """
    MATCH (n)
    WHERE NOT (n)--()
    RETURN COUNT(n)
    """
    with graph.driver.session() as s:
        result = s.run(rels_query).single()
    assert result.values()[0] == 0
