"""Validate property and relationship rules for graph DB."""
import json
from typing import Dict, List, Optional, Set

import pytest
from neo4j.graph import Node

from metakb.database import Graph
from metakb.schemas.app import SourceName


@pytest.fixture(scope="module")
def sources_count():
    """Get length of sources"""
    return len(SourceName)


@pytest.fixture(scope="module")
def graph():
    """Return graph object."""
    g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "password"))
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
def get_node_labels(graph: Graph):
    """Get node labels"""
    def _get_labels_function(parent_label: str):
        query = f"""
        MATCH (n:{parent_label})
        RETURN collect(DISTINCT labels(n))
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        return record.values()[0]
    return _get_labels_function


@pytest.fixture(scope="module")
def check_node_labels(get_node_labels: callable):
    """Check node labels match expected"""
    def _check_function(
        node_label: str,
        expected: List[Set[str]],
        expected_num_labels: int
    ):
        node_labels = get_node_labels(node_label)
        assert len(node_labels) == expected_num_labels
        node_labels_set = list(set(x) for x in node_labels)
        for e in expected:
            assert e in node_labels_set

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


@pytest.fixture(scope="module")
def check_extension_props():
    """Check that node extension properties match expected"""
    def _check_function(
        node: Node, fixture_extensions: List[Dict], ext_names: Set[str]
    ):
        checked = set()
        for ext in fixture_extensions:
            if ext["name"] in ext_names:
                try:
                    assert json.loads(node[ext["name"]]) == ext["value"]
                except json.decoder.JSONDecodeError:
                    assert node[ext["name"]] == ext["value"]
                checked.add(ext["name"])
        assert checked == ext_names
    return _check_function


@pytest.fixture(scope="module")
def check_node_props():
    """Check that node properties match expected. For extensions, use
    `check_extension_props`
    """
    def _check_function(
        node: Node, fixture: Dict, expected_keys: Set[str],
        extension_names: Set[str] = set()
    ):
        assert node.keys() == expected_keys
        for k in expected_keys - extension_names:
            if k == "mappings":
                assert json.loads(node[k]) == fixture[k]
            elif isinstance(fixture[k], list):
                assert set(node[k]) == set(fixture[k])
            else:
                assert node[k] == fixture[k]
    return _check_function


def test_gene_rules(
    check_unique_property,
    check_node_labels,
    check_relation_count,
    get_node_by_id,
    civic_gid5,
    check_node_props,
    check_extension_props
):
    """Verify property and relationship rules for Gene nodes."""
    check_unique_property("Gene", "id")
    check_relation_count(
        "Gene", "Study", "HAS_GENE_CONTEXT", direction="in", min=1, max=None
    )

    expected_labels = [{"Gene"}]
    check_node_labels("Gene", expected_labels, 1)

    gene = get_node_by_id(civic_gid5["id"])
    extension_names = {"gene_normalizer_id"}
    check_extension_props(gene, civic_gid5["extensions"], extension_names)
    expected_keys = {
        "gene_normalizer_id", "label", "id", "description", "mappings", "type",
        "aliases"
    }
    check_node_props(gene, civic_gid5, expected_keys, extension_names)


def test_variation_rules(
    graph, check_unique_property,
    check_relation_count,
    get_node_by_id,
    check_node_labels,
    civic_vid12
):
    """Verify property and relationship rules for Variation nodes."""
    check_unique_property("Variation", "id")
    # members dont have defining context
    check_relation_count(
        "Variation", "CategoricalVariation", "HAS_DEFINING_CONTEXT", direction="in",
        min=0, max=None
    )
    check_relation_count(
        "Variation", "CategoricalVariation", "HAS_MEMBERS", min=0, max=None,
        direction="in"
    )

    expected_labels = [{"Variation", "Allele"}]
    check_node_labels("Variation", expected_labels, 1)

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

    v = get_node_by_id(civic_vid12["id"])
    assert set(v.keys()) == {
        "id", "label", "digest", "state", "expression_hgvs_p", "expression_hgvs_c",
        "expression_hgvs_g", "type"
    }

    assert v["type"] == "Allele"
    assert v["label"] == civic_vid12["label"]
    assert v["digest"] == civic_vid12["digest"]
    assert json.loads(v["state"]) == civic_vid12["state"]
    expected_p, expected_c, expected_g = [], [], []
    for expr in civic_vid12["expressions"]:
        syntax = expr["syntax"]
        val = expr["value"]
        if syntax == "hgvs.p":
            expected_p.append(val)
        elif syntax == "hgvs.c":
            expected_c.append(val)
        elif syntax == "hgvs.g":
            expected_g.append(val)

    assert v["expression_hgvs_p"] == expected_p
    assert set(v["expression_hgvs_c"]) == set(expected_c)
    assert v["expression_hgvs_g"] == expected_g


def test_categorical_variation_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_mpid12
):
    """Verify property and relationship rules for Categorical Variation nodes."""
    check_unique_property("CategoricalVariation", "id")
    check_relation_count(
        "CategoricalVariation", "Variation", "HAS_DEFINING_CONTEXT", max=1
    )
    check_relation_count(
        "CategoricalVariation", "Variation", "HAS_MEMBERS", min=0, max=None
    )

    expected_node_labels = [{"CategoricalVariation", "ProteinSequenceConsequence"}]
    check_node_labels("CategoricalVariation", expected_node_labels, 1)

    cv = get_node_by_id(civic_mpid12["id"])
    assert set(cv.keys()) == {
        "id",
        "label",
        "description",
        "aliases",
        "civic_molecular_profile_score",
        "civic_representative_coordinate",
        "mappings",
        "variant_types",
        "type"
    }
    assert cv["type"] == civic_mpid12["type"]
    assert cv["label"] == civic_mpid12["label"]
    assert cv["description"] == civic_mpid12["description"]
    assert set(cv["aliases"]) == set(civic_mpid12["aliases"])
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


def test_location_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id
):
    """Verify property and relationship rules for Location nodes."""
    check_unique_property("Location", "id")
    check_relation_count(
        "Location", "Variation", "HAS_LOCATION", direction="in", max=None
    )

    expected_labels = [{"Location", "SequenceLocation"}]
    check_node_labels("Location", expected_labels, 1)

    loc = get_node_by_id("ga4gh:SL.xdFHLf7Q45VKT57U4kwcDd7MUOtV2Bdz")
    assert set(loc.keys()) == {"id", "sequence_reference", "start", "end", "type"}
    assert json.loads(loc["sequence_reference"]) == {
        "type": "SequenceReference",
        "refgetAccession": "SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE"
    }
    assert loc["start"] == 766
    assert loc["end"] == 769
    assert loc["type"] == "SequenceLocation"


def test_therapeutic_procedure_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_tid146,
    check_node_props,
    check_extension_props,
    civic_ct,
    civic_tsg
):
    """Verify property and relationship rules for Therapeutic Procedure nodes."""
    check_unique_property("TherapeuticProcedure", "id")
    # min is 0 because TherapeuticAgent may not be attached to study directly, but
    # through CombinationTherapy and TherapeuticSubstituteGroup
    check_relation_count(
        "TherapeuticProcedure", "Study", "HAS_THERAPEUTIC", min=0, max=None,
        direction="in"
    )
    check_relation_count(
        "CombinationTherapy", "TherapeuticAgent", "HAS_COMPONENTS", max=None
    )
    check_relation_count(
        "CombinationTherapy", "Study", "HAS_THERAPEUTIC", max=None, direction="in"
    )
    check_relation_count(
        "TherapeuticSubstituteGroup", "TherapeuticAgent", "HAS_SUBSTITUTES", max=None
    )
    check_relation_count(
        "TherapeuticSubstituteGroup", "Study", "HAS_THERAPEUTIC", max=None,
        direction="in"
    )

    expected_node_labels = [
        {"TherapeuticProcedure", "TherapeuticAgent"},
        {"TherapeuticProcedure", "CombinationTherapy"},
        {"TherapeuticProcedure", "TherapeuticSubstituteGroup"}
    ]
    check_node_labels("TherapeuticProcedure", expected_node_labels, 3)

    # Test TherapeuticAgent
    ta = get_node_by_id(civic_tid146["id"])
    extension_names = {"therapy_normalizer_data", "regulatory_approval"}
    check_extension_props(ta, civic_tid146["extensions"], extension_names)
    expected_keys = {
        "id", "label", "aliases", "therapy_normalizer_data", "regulatory_approval",
        "mappings", "type"
    }
    check_node_props(ta, civic_tid146, expected_keys, extension_names)

    # Test CombinationTherapy
    ct = get_node_by_id(civic_ct["id"])
    check_extension_props(
        ct, civic_ct["extensions"], {"civic_therapy_interaction_type"}
    )
    assert ct["type"] == civic_ct["type"]

    # Test TherapeuticSubstituteGroup
    tsg = get_node_by_id(civic_tsg["id"])
    check_extension_props(
        tsg, civic_tsg["extensions"], {"civic_therapy_interaction_type"}
    )
    assert tsg["type"] == tsg["type"]


def test_condition_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_did8,
    check_node_props,
    check_extension_props
):
    """Verify property and relationship rules for condition nodes."""
    check_unique_property("Condition", "id")
    check_relation_count(
        "Condition", "Study", "HAS_TUMOR_TYPE", max=None, direction="in"
    )

    expected_node_labels = [{"Disease", "Condition"}]
    check_node_labels("Condition", expected_node_labels, 1)

    disease = get_node_by_id(civic_did8["id"])
    extension_names = {"disease_normalizer_data"}
    check_extension_props(disease, civic_did8["extensions"], extension_names)
    expected_keys = {"id", "label", "mappings", "disease_normalizer_data", "type"}
    check_node_props(disease, civic_did8, expected_keys, extension_names)


def test_study_rules(
    graph: Graph,
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_eid2997_study,
    check_node_props
):
    """Verify property and relationship rules for Study nodes."""
    check_unique_property("Study", "id")

    check_relation_count("Study", "CategoricalVariation", "HAS_VARIANT")
    check_relation_count("Study", "Condition", "HAS_TUMOR_TYPE")
    check_relation_count("Study", "TherapeuticProcedure", "HAS_THERAPEUTIC")
    check_relation_count("Study", "Coding", "HAS_STRENGTH")
    check_relation_count("Study", "Method", "IS_SPECIFIED_BY", max=None)
    check_relation_count("Study", "Gene", "HAS_GENE_CONTEXT", max=None)

    expected_node_labels = [{"Study", "VariantTherapeuticResponseStudy"}]
    check_node_labels("Study", expected_node_labels, 1)

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

    study = get_node_by_id(civic_eid2997_study["id"])
    expected_keys = {
        "id", "description", "direction", "predicate", "alleleOrigin", "type"
    }
    civic_eid2997_study_cp = civic_eid2997_study.copy()
    civic_eid2997_study_cp["alleleOrigin"] = civic_eid2997_study_cp["qualifiers"]["alleleOrigin"]  # noqa: E501
    check_node_props(study, civic_eid2997_study_cp, expected_keys)


def test_document_rules(
    graph,
    check_unique_property,
    check_node_labels,
    check_relation_count,
    get_node_by_id,
    moa_source44,
    check_node_props,
    check_extension_props
):
    """Verify property and relationship rules for Document nodes."""
    check_unique_property("Document", "id")
    check_relation_count(
        "Document", "Study", "IS_REPORTED_IN", min=0, max=None, direction="in"
    )

    expected_labels = [{"Document"}]
    check_node_labels("Document", expected_labels, 1)

    # PMIDs: 31779674 and 35121878 do not have this relationship
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

    # PMIDs: 31779674 and 35121878 are only used in methods
    is_reported_in_query = """
    MATCH (s)<-[:IS_REPORTED_IN]-(d:Method)
    RETURN collect(s.pmid)
    """
    with graph.driver.session() as s:
        record = s.run(is_reported_in_query).single()
    assert set(record.values()[0]) == {31779674, 35121878}

    doc = get_node_by_id(moa_source44["id"])
    extension_names = {"source_type"}
    check_extension_props(doc, moa_source44["extensions"], extension_names)
    expected_keys = {"id", "title", "doi", "source_type", "url", "pmid"}
    check_node_props(doc, moa_source44, expected_keys, extension_names)


def test_method_rules(
    check_unique_property,
    check_node_labels,
    check_relation_count,
    get_node_by_id,
    civic_method,
    check_node_props
):
    """Verify property and relationship rules for Method nodes."""
    check_unique_property("Method", "id")
    check_relation_count("Method", "Study", "IS_SPECIFIED_BY", max=None, direction="in")

    expected_node_labels = [{"Method"}]
    check_node_labels("Method", expected_node_labels, 1)

    method = get_node_by_id(civic_method["id"])
    expected_keys = {"id", "label"}
    check_node_props(method, civic_method, expected_keys)


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
