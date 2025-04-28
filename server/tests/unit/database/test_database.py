"""Validate property and relationship rules for graph DB."""

import json

import pytest
from deepdiff import DeepDiff
from neo4j import Driver
from neo4j.graph import Node
from tests.conftest import get_mappings_normalizer_id

from metakb.database import get_driver
from metakb.schemas.app import SourceName


@pytest.fixture(scope="module")
def sources_count():
    """Get length of sources"""
    return len(SourceName)


@pytest.fixture(scope="module")
def driver():
    """Return Neo4j graph connection driver object."""
    driver = get_driver(uri="bolt://localhost:7687", credentials=("neo4j", "password"))
    yield driver
    driver.close()


@pytest.fixture(scope="module")
def get_node_by_id(driver: Driver):
    """Return node by its ID"""

    def _get_node(node_id: str):
        query = f"MATCH (n {{id: '{node_id}'}}) RETURN (n)"
        result = driver.execute_query(query)
        return result.records[0]["n"]

    return _get_node


@pytest.fixture(scope="module")
def check_unique_property(driver: Driver):
    """Verify that nodes satisfy uniqueness property"""

    def _check_function(label: str, prop: str):
        query = f"""
        MATCH (x:{label})
        WITH x.{prop} AS {prop}, COUNT(x) AS x_count
        WHERE x_count > 1
        RETURN COUNT({prop})
        """
        with driver.session() as s:
            record = s.run(query).single()

        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="module")
def get_node_labels(driver: Driver):
    """Get node labels"""

    def _get_labels_function(parent_label: str):
        query = f"""
        MATCH (n:{parent_label})
        RETURN collect(DISTINCT labels(n))
        """
        with driver.session() as s:
            record = s.run(query).single()
        return record.values()[0]

    return _get_labels_function


@pytest.fixture(scope="module")
def check_node_labels(get_node_labels: callable):
    """Check node labels match expected"""

    def _check_function(
        node_label: str, expected: list[set[str]], expected_num_labels: int
    ):
        node_labels = get_node_labels(node_label)
        assert len(node_labels) == expected_num_labels
        node_labels_set = [set(x) for x in node_labels]
        for e in expected:
            assert e in node_labels_set

    return _check_function


@pytest.fixture(scope="module")
def check_statement_relation(driver: Driver):
    """Check that node is used in a statement."""

    def _check_function(value_label: str):
        query = f"""
        MATCH (d:{value_label})
        OPTIONAL MATCH (d)<-[:HAS_{value_label.upper()}]-(s:Statement)
        WITH d, COUNT(s) as s_count
        WHERE s_count < 1
        RETURN COUNT(s_count)
        """
        with driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="module")
def check_relation_count(driver: Driver):
    """Check that the quantity of relationships from one Node type to another
    are within a certain range.
    """

    def _check_function(
        self_label: str,
        other_label: str,
        relation: str,
        min_rels: int = 1,
        max_rels: int | None = 1,
        direction: str | None = "out",
    ):
        if direction == "out":
            rel_query = f"-[:{relation}]->"
        elif direction == "in":
            rel_query = f"<-[:{relation}]-"
        elif direction is None:
            rel_query = f"-[:{relation}]-"
        else:
            msg = "direction must be 'out', 'in' or None"
            raise ValueError(msg)
        query = f"""
        MATCH (s:{self_label})
        OPTIONAL MATCH (s){rel_query}(d:{other_label})
        WITH s, COUNT(d) as d_count
        WHERE d_count < {min_rels}
            {f"OR d_count > {max_rels}" if max_rels is not None else ""}
        RETURN COUNT(s)
        """
        with driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="module")
def check_tg_relation_count(driver: Driver):
    """Check that the quantity of relationships from TherapyGroup to Therapy are within
    a certain range.
    """

    def _check_function(relationship: str):
        query = f"""
        MATCH (s:TherapyGroup)
        WHERE NOT EXISTS {{
            MATCH (s)-[r]-(n)
            WHERE type(r) <> '{relationship}'
        }}
        AND NOT EXISTS {{
            MATCH (s)-[:{relationship}]->(:Therapy)
        }}
        RETURN COUNT(s)
        """
        with driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="module")
def check_extension_props():
    """Check that node extension properties match expected"""

    def _check_function(
        node: Node, fixture_extensions: list[dict], ext_names: set[str]
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
        node: Node,
        fixture: dict,
        expected_keys: set[str],
        extension_names: set[str] | None = None,
    ):
        if extension_names is None:
            extension_names = set()
        assert node.keys() == expected_keys
        for k in expected_keys - extension_names:
            if k == "mappings" or (k == "methodType" and isinstance(fixture[k], dict)):
                diff = DeepDiff(json.loads(node[k]), fixture[k], ignore_order=True)
                assert diff == {}, k
            elif k == "normalizer_id":
                normalizer_id = get_mappings_normalizer_id(fixture["mappings"])
                assert node[k] == normalizer_id
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
    check_extension_props,
):
    """Verify property and relationship rules for Gene nodes."""
    check_unique_property("Gene", "id")
    check_relation_count(
        "Gene",
        "Statement",
        "HAS_GENE_CONTEXT",
        direction="in",
        min_rels=1,
        max_rels=None,
    )

    expected_labels = [{"Gene"}]
    check_node_labels("Gene", expected_labels, 1)

    gene = get_node_by_id(civic_gid5["id"])
    extension_names = {"description", "aliases"}
    check_extension_props(gene, civic_gid5["extensions"], extension_names)
    expected_keys = {
        "normalizer_id",
        "name",
        "id",
        "description",
        "mappings",
        "conceptType",
        "aliases",
    }
    check_node_props(gene, civic_gid5, expected_keys, extension_names)


def test_variation_rules(
    driver: Driver,
    check_unique_property,
    check_relation_count,
    get_node_by_id,
    check_node_labels,
    civic_vid12,
):
    """Verify property and relationship rules for Variation nodes."""
    check_unique_property("Variation", "id")
    # members dont have defining context
    check_relation_count(
        "Variation",
        "CategoricalVariant",
        "HAS_DEFINING_CONTEXT",
        direction="in",
        min_rels=0,
        max_rels=None,
    )
    check_relation_count(
        "Variation",
        "CategoricalVariant",
        "HAS_MEMBERS",
        min_rels=0,
        max_rels=None,
        direction="in",
    )

    expected_labels = [{"Variation", "Allele"}, {"Variation", "CategoricalVariant"}]
    check_node_labels("Variation", expected_labels, 2)

    # all Variations are either Alleles or CategoricalVariants, and all Alleles and CategoricalVariants are Variation
    label_query = """
    MATCH (v)
    RETURN
        SUM(CASE WHEN (v:Variation AND NOT (v:Allele OR v:CategoricalVariant)) THEN 1 ELSE 0 END) +
        SUM(CASE WHEN (v:Allele AND NOT v:Variation) THEN 1 ELSE 0 END) +
        SUM(CASE WHEN (v:CategoricalVariant AND NOT v:Variation) THEN 1 ELSE 0 END)
    """
    with driver.session() as s:
        record = s.run(label_query).single()
    assert record.values()[0] == 0

    v = get_node_by_id(civic_vid12["id"])
    assert set(v.keys()) == {
        "id",
        "name",
        "digest",
        "state",
        "expression_hgvs_p",
        "expression_hgvs_c",
        "expression_hgvs_g",
        "type",
    }

    assert v["type"] == "Allele"
    assert v["name"] == civic_vid12["name"]
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


def test_categorical_variant_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_mpid12,
):
    """Verify property and relationship rules for Categorical Variant nodes."""
    check_unique_property("CategoricalVariant", "id")
    check_relation_count(
        "CategoricalVariant", "Variation", "HAS_DEFINING_CONTEXT", max_rels=1
    )
    check_relation_count(
        "CategoricalVariant", "Variation", "HAS_MEMBERS", min_rels=0, max_rels=None
    )

    expected_node_labels = [{"CategoricalVariant", "Variation"}]
    check_node_labels("CategoricalVariant", expected_node_labels, 1)

    cv = get_node_by_id(civic_mpid12["id"])
    assert set(cv.keys()) == {
        "id",
        "name",
        "description",
        "aliases",
        "civic_molecular_profile_score",
        "civic_representative_coordinate",
        "mappings",
        "variant_types",
        "type",
    }
    assert cv["type"] == civic_mpid12["type"]
    assert cv["name"] == civic_mpid12["name"]
    assert cv["description"] == civic_mpid12["description"]
    assert set(json.loads(cv["aliases"])) == set(civic_mpid12["aliases"])
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
        "type",
    }
    mappings = json.loads(cv["mappings"])
    for m in mappings:
        assert isinstance(m["coding"], dict)
        assert isinstance(m["relation"], str)

    variant_types = json.loads(cv["variant_types"])
    for vt in variant_types:
        assert set(vt.keys()) == {"id", "name", "system", "code"}


def test_location_rules(
    check_unique_property, check_relation_count, check_node_labels, get_node_by_id
):
    """Verify property and relationship rules for Location nodes."""
    check_unique_property("Location", "id")
    check_relation_count(
        "Location", "Variation", "HAS_LOCATION", direction="in", max_rels=None
    )

    expected_labels = [{"Location", "SequenceLocation"}]
    check_node_labels("Location", expected_labels, 1)

    # NP_005219.2:p.Val769_Asp770insAlaSerVal
    loc_digest = "7qyw-4VUk3oCczBuoaF_8vGQo19dM_mk"
    loc = get_node_by_id(f"ga4gh:SL.{loc_digest}")
    assert set(loc.keys()) == {
        "id",
        "digest",
        "sequenceReference",
        "start",
        "end",
        "sequence",
        "type",
    }
    assert json.loads(loc["sequenceReference"]) == {
        "type": "SequenceReference",
        "refgetAccession": "SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
    }
    assert loc["start"] == 766
    assert loc["end"] == 769
    assert loc["type"] == "SequenceLocation"
    assert loc["digest"] == loc_digest


def test_therapy_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_tid146,
    check_node_props,
    check_extension_props,
    civic_ct,
    civic_tsg,
    check_tg_relation_count,
):
    """Verify property and relationship rules for Therapy nodes."""
    check_unique_property("Therapy", "id")
    # min_rels is 0 because Therapy may not be attached to statement directly,
    # but through CombinationTherapy and TherapeuticSubstituteGroup
    check_relation_count(
        "Therapy",
        "Statement",
        "HAS_THERAPEUTIC",
        min_rels=0,
        max_rels=None,
        direction="in",
    )
    check_tg_relation_count(relationship="HAS_COMPONENTS")

    check_tg_relation_count(relationship="HAS_THERAPEUTIC")

    check_tg_relation_count(relationship="HAS_SUBSTITUTES")

    expected_node_labels = [{"Therapy"}, {"Therapy", "TherapyGroup"}]
    check_node_labels("Therapy", expected_node_labels, 2)

    # Test Therapy
    ta = get_node_by_id(civic_tid146["id"])
    extension_names = {
        "regulatory_approval",
        "aliases",
    }
    check_extension_props(ta, civic_tid146["extensions"], extension_names)
    expected_keys = {
        "id",
        "name",
        "aliases",
        "normalizer_id",
        "regulatory_approval",
        "mappings",
        "conceptType",
    }
    check_node_props(ta, civic_tid146, expected_keys, extension_names)

    # Test CombinationTherapy
    ct = get_node_by_id(civic_ct["id"])
    assert ct["membershipOperator"] == civic_ct["membershipOperator"]

    # Test TherapeuticSubstituteGroup
    tsg = get_node_by_id(civic_tsg["id"])
    assert tsg["membershipOperator"] == civic_tsg["membershipOperator"]


def test_condition_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_did8,
    check_node_props,
    check_extension_props,
):
    """Verify property and relationship rules for condition nodes."""
    check_unique_property("Condition", "id")
    check_relation_count(
        "Condition", "Statement", "HAS_TUMOR_TYPE", max_rels=None, direction="in"
    )

    expected_node_labels = [{"Disease", "Condition"}]
    check_node_labels("Condition", expected_node_labels, 1)

    disease = get_node_by_id(civic_did8["id"])

    expected_keys = {
        "id",
        "name",
        "mappings",
        "normalizer_id",
        "conceptType",
    }
    check_node_props(disease, civic_did8, expected_keys)


def test_statement_rules(
    driver: Driver,
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_eid2997_study_stmt,
    check_node_props,
    civic_aid6_statement,
):
    """Verify property and relationship rules for Statement nodes."""
    check_unique_property("Statement", "id")

    check_relation_count("Statement", "CategoricalVariant", "HAS_VARIANT")
    check_relation_count("Statement", "Condition", "HAS_TUMOR_TYPE")
    check_relation_count("Statement", "Therapy", "HAS_THERAPEUTIC", min_rels=0)
    check_relation_count("Statement", "Strength", "HAS_STRENGTH", min_rels=0)
    check_relation_count("Statement", "Method", "IS_SPECIFIED_BY", max_rels=None)
    check_relation_count("Statement", "Gene", "HAS_GENE_CONTEXT", max_rels=None)
    check_relation_count(
        "Statement", "Classification", "HAS_CLASSIFICATION", min_rels=0, max_rels=1
    )

    expected_node_labels = [
        {"Statement"},
        {"Statement", "StudyStatement"},
    ]
    check_node_labels("Statement", expected_node_labels, 2)

    # Evidence items should have documents
    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:IS_REPORTED_IN]->(d:Document)
    WITH s, COUNT(d) as d_count
    WHERE d_count < 1 AND NOT s.id STARTS WITH 'civic.aid:'
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    # Assertions should NOT have documents (right now we only have civic assertions)
    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:IS_REPORTED_IN]->(d:Document)
    WITH s, COUNT(d) as d_count
    WHERE d_count > 1 AND s.id STARTS WITH 'civic.aid:'
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    # Assertions must have evidence lines (right now we only have civic assertions)
    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:HAS_EVIDENCE_LINE]->(el:EvidenceLine)
    WITH s, COUNT(el) as el_count
    WHERE el_count < 1 AND s.id STARTS WITH 'civic.aid:'
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    statement = get_node_by_id(civic_eid2997_study_stmt["id"])
    expected_keys = {
        "id",
        "description",
        "direction",
        "predicate",
        "alleleOriginQualifier",
        "type",
        "propositionType",
    }
    civic_eid2997_ss_cp = civic_eid2997_study_stmt.copy()
    civic_eid2997_ss_cp["alleleOriginQualifier"] = civic_eid2997_ss_cp["proposition"][
        "alleleOriginQualifier"
    ]["name"]
    civic_eid2997_ss_cp["predicate"] = civic_eid2997_ss_cp["proposition"]["predicate"]
    civic_eid2997_ss_cp["propositionType"] = civic_eid2997_ss_cp["proposition"]["type"]
    check_node_props(statement, civic_eid2997_ss_cp, expected_keys)

    # Check CIViC assertion
    statement = get_node_by_id(civic_aid6_statement["id"])
    expected_keys = {
        "id",
        "description",
        "direction",
        "predicate",
        "alleleOriginQualifier",
        "type",
        "propositionType",
    }
    civic_aid6_ss_cp = civic_aid6_statement.copy()
    civic_aid6_ss_cp["alleleOriginQualifier"] = civic_aid6_ss_cp["proposition"][
        "alleleOriginQualifier"
    ]["name"]
    civic_aid6_ss_cp["predicate"] = civic_aid6_ss_cp["proposition"]["predicate"]
    civic_aid6_ss_cp["propositionType"] = civic_aid6_ss_cp["proposition"]["type"]
    check_node_props(statement, civic_aid6_ss_cp, expected_keys)


def test_strength_rules(driver: Driver, check_relation_count, civic_eid2997_study_stmt):
    """Verify property and relationship rules for Strength nodes."""
    query = """
    MATCH (s:Strength)
    WITH s.name AS name, s.primaryCoding AS primaryCoding, COUNT(*) AS count
    WHERE count > 1
    RETURN COUNT(*)
    """
    with driver.session() as s:
        record = s.run(query).single()
    assert record.values()[0] == 0

    # Evidence items should have strength
    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:HAS_STRENGTH]->(st:Strength)
    WITH s, COUNT(st) as strength_count
    WHERE strength_count < 1 AND NOT s.id STARTS WITH 'civic.aid:'
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    # Assertions do not have strength
    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:HAS_STRENGTH]->(st:Strength)
    WITH s, COUNT(st) as strength_count
    WHERE strength_count > 1 AND s.id STARTS WITH 'civic.aid:'
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    query = f"""
    MATCH (s:Strength {{primaryCoding: '{json.dumps(civic_eid2997_study_stmt['strength']['primaryCoding'])}', name: '{civic_eid2997_study_stmt['strength']['name']}'}})
    RETURN s
    """
    result = driver.execute_query(query)
    assert len(result.records) == 1
    strength_node = result.records[0].data()["s"]

    assert strength_node.keys() == civic_eid2997_study_stmt["strength"].keys()
    for k in ("mappings", "primaryCoding"):
        strength_node[k] = json.loads(strength_node[k])
    assert strength_node == civic_eid2997_study_stmt["strength"]


def test_classification_rules(
    driver: Driver, check_unique_property, check_relation_count, civic_aid6_statement
):
    """Verify property and relationship rules for Classification nodes."""
    check_unique_property("Classification", "primaryCoding")

    check_relation_count(
        "Classification",
        "Statement",
        "HAS_CLASSIFICATION",
        min_rels=0,
        max_rels=None,
        direction="in",
    )

    classification_primary_coding = json.dumps(
        civic_aid6_statement["classification"]["primaryCoding"]
    )
    query = f"""
    MATCH (c:Classification {{primaryCoding: '{classification_primary_coding}'}})
    RETURN c
    """
    result = driver.execute_query(query)
    assert len(result.records) == 1
    classification_node = result.records[0].data()["c"]
    classification_node["primaryCoding"] = json.loads(
        classification_node["primaryCoding"]
    )
    assert classification_node == {
        "primaryCoding": civic_aid6_statement["classification"]["primaryCoding"],
    }


def test_evidence_line_rules(
    check_unique_property,
    check_relation_count,
):
    """Verify property and relationship rules for EvidenceLine nodes."""
    check_unique_property("EvidenceLine", "id")
    check_relation_count(
        "EvidenceLine", "Statement", "HAS_EVIDENCE_ITEM", min_rels=0, direction="in"
    )


def test_document_rules(
    driver: Driver,
    check_unique_property,
    check_node_labels,
    check_relation_count,
    get_node_by_id,
    moa_source45,
    check_node_props,
    check_extension_props,
):
    """Verify property and relationship rules for Document nodes."""
    check_unique_property("Document", "id")
    check_relation_count(
        "Document",
        "Statement",
        "IS_REPORTED_IN",
        min_rels=0,
        max_rels=None,
        direction="in",
    )

    expected_labels = [{"Document"}]
    check_node_labels("Document", expected_labels, 1)

    # PMIDs: 31779674 and 35121878 do not have this relationship
    is_reported_in_query = """
    MATCH (s:Document)
    OPTIONAL MATCH (s)<-[:IS_REPORTED_IN]-(d:Statement)
    WITH s, COUNT(d) as d_count
    WHERE (d_count < 1) AND (s.pmid <> 31779674) AND (s.pmid <> 35121878)
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(is_reported_in_query).single()
    assert record.values()[0] == 0

    # PMIDs: 31779674 and 35121878 are only used in methods
    is_reported_in_query = """
    MATCH (s)<-[:IS_REPORTED_IN]-(d:Method)
    RETURN collect(s.pmid)
    """
    with driver.session() as s:
        record = s.run(is_reported_in_query).single()
    assert set(record.values()[0]) == {31779674, 35121878}

    doc = get_node_by_id(moa_source45["id"])
    extension_names = {"source_type"}
    check_extension_props(doc, moa_source45["extensions"], extension_names)
    expected_keys = {"id", "title", "doi", "source_type", "urls", "pmid"}
    check_node_props(doc, moa_source45, expected_keys, extension_names)


def test_method_rules(
    check_unique_property,
    check_node_labels,
    check_relation_count,
    get_node_by_id,
    civic_method,
    check_node_props,
):
    """Verify property and relationship rules for Method nodes."""
    check_unique_property("Method", "id")
    check_relation_count(
        "Method", "Statement", "IS_SPECIFIED_BY", max_rels=None, direction="in"
    )

    expected_node_labels = [{"Method"}]
    check_node_labels("Method", expected_node_labels, 1)

    method = get_node_by_id(civic_method["id"])
    expected_keys = {"id", "name", "methodType"}
    check_node_props(method, civic_method, expected_keys)


def test_no_lost_nodes(driver: Driver):
    """Verify that no unlabeled or isolated nodes have been created."""
    # non-normalizable nodes can be excepted
    labels_query = """
    MATCH (n)
    WHERE size(labels(n)) = 0
    AND NOT (n)<-[:IS_REPORTED_IN]-(:Statement)
    RETURN COUNT(n)
    """
    with driver.session() as s:
        record = s.run(labels_query).single()
    assert record.values()[0] == 0

    rels_query = """
    MATCH (n)
    WHERE NOT (n)--()
    RETURN COUNT(n)
    """
    with driver.session() as s:
        result = s.run(rels_query).single()
    assert result.values()[0] == 0
