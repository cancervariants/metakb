"""Validate property and relationship rules for graph DB."""

import json

import pytest
from neo4j import Driver
from neo4j.graph import Node

from metakb.database import get_driver
from metakb.normalizers import VICC_NORMALIZER_DATA, ViccDiseaseNormalizerData
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
def check_study_relation(driver: Driver):
    """Check that node is used in a study."""

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
def check_extension_props():
    """Check that node extension properties match expected"""

    def _check_function(
        node: Node, fixture_extensions: list[dict], ext_names: set[str]
    ):
        checked = set()
        for ext in fixture_extensions:
            if ext["name"] == VICC_NORMALIZER_DATA:
                for normalized_field in ViccDiseaseNormalizerData.model_fields:
                    normalized_val = ext["value"].get(normalized_field)
                    if normalized_val is None:
                        continue

                    ext_name = f"normalizer_{normalized_field}"
                    assert node[ext_name] == ext["value"][normalized_field]
                    checked.add(ext_name)
            elif ext["name"] in ext_names:
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
    extension_names = {"normalizer_label", "normalizer_id"}
    check_extension_props(gene, civic_gid5["extensions"], extension_names)
    expected_keys = {
        "normalizer_id",
        "normalizer_label",
        "label",
        "id",
        "description",
        "mappings",
        "type",
        "alternativeLabels",
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
        "label",
        "digest",
        "state",
        "expression_hgvs_p",
        "type",
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


def test_categorical_variation_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_mpid12,
):
    """Verify property and relationship rules for Categorical Variation nodes."""
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
        "label",
        "description",
        "alternativeLabels",
        "civic_molecular_profile_score",
        "civic_representative_coordinate",
        "mappings",
        "variant_types",
        "type",
    }
    assert cv["type"] == civic_mpid12["type"]
    assert cv["label"] == civic_mpid12["label"]
    assert cv["description"] == civic_mpid12["description"]
    assert set(cv["alternativeLabels"]) == set(civic_mpid12["alternativeLabels"])
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
        assert set(vt.keys()) == {"label", "system", "code"}


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
        "sequence_reference",
        "start",
        "end",
        "sequence",
        "type",
    }
    assert json.loads(loc["sequence_reference"]) == {
        "type": "SequenceReference",
        "refgetAccession": "SQ.vyo55F6mA6n2LgN4cagcdRzOuh38V4mE",
    }
    assert loc["start"] == 766
    assert loc["end"] == 769
    assert loc["type"] == "SequenceLocation"
    assert loc["digest"] == loc_digest


def test_therapeutic_procedure_rules(
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_tid146,
    check_node_props,
    check_extension_props,
    civic_ct,
    civic_tsg,
):
    """Verify property and relationship rules for Therapeutic Procedure nodes."""
    check_unique_property("TherapeuticProcedure", "id")
    # min_rels is 0 because TherapeuticAgent may not be attached to study directly, but
    # through CombinationTherapy and TherapeuticSubstituteGroup
    check_relation_count(
        "TherapeuticProcedure",
        "Statement",
        "HAS_THERAPEUTIC",
        min_rels=0,
        max_rels=None,
        direction="in",
    )
    check_relation_count(
        "CombinationTherapy", "TherapeuticAgent", "HAS_COMPONENTS", max_rels=None
    )
    check_relation_count(
        "CombinationTherapy",
        "Statement",
        "HAS_THERAPEUTIC",
        max_rels=None,
        direction="in",
    )
    check_relation_count(
        "TherapeuticSubstituteGroup",
        "TherapeuticAgent",
        "HAS_SUBSTITUTES",
        max_rels=None,
    )
    check_relation_count(
        "TherapeuticSubstituteGroup",
        "Statement",
        "HAS_THERAPEUTIC",
        max_rels=None,
        direction="in",
    )

    expected_node_labels = [
        {"TherapeuticProcedure", "TherapeuticAgent"},
        {"TherapeuticProcedure", "CombinationTherapy"},
        {"TherapeuticProcedure", "TherapeuticSubstituteGroup"},
    ]
    check_node_labels("TherapeuticProcedure", expected_node_labels, 3)

    # Test TherapeuticAgent
    ta = get_node_by_id(civic_tid146["id"])
    extension_names = {
        "normalizer_id",
        "normalizer_label",
        "regulatory_approval",
    }
    check_extension_props(ta, civic_tid146["extensions"], extension_names)
    expected_keys = {
        "id",
        "label",
        "alternativeLabels",
        "normalizer_id",
        "normalizer_label",
        "regulatory_approval",
        "mappings",
        "type",
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
    extension_names = {
        "normalizer_id",
        "normalizer_label",
        "normalizer_mondo_id",
    }
    check_extension_props(disease, civic_did8["extensions"], extension_names)
    expected_keys = {
        "id",
        "label",
        "mappings",
        "normalizer_id",
        "normalizer_label",
        "normalizer_mondo_id",
        "type",
    }
    check_node_props(disease, civic_did8, expected_keys, extension_names)


def test_study_rules(
    driver: Driver,
    check_unique_property,
    check_relation_count,
    check_node_labels,
    get_node_by_id,
    civic_eid2997_study,
    check_node_props,
):
    """Verify property and relationship rules for Statement nodes."""
    check_unique_property("Statement", "id")

    check_relation_count("Statement", "CategoricalVariant", "HAS_VARIANT")
    check_relation_count("Statement", "Condition", "HAS_TUMOR_TYPE")
    check_relation_count("Statement", "TherapeuticProcedure", "HAS_THERAPEUTIC")
    check_relation_count("Statement", "Coding", "HAS_STRENGTH")
    check_relation_count("Statement", "Method", "IS_SPECIFIED_BY", max_rels=None)
    check_relation_count("Statement", "Gene", "HAS_GENE_CONTEXT", max_rels=None)

    expected_node_labels = [{"Statement", "VariantTherapeuticResponseStudyStatement"}]
    check_node_labels("Statement", expected_node_labels, 1)

    cite_query = """
    MATCH (s:Statement)
    OPTIONAL MATCH (s)-[:IS_REPORTED_IN]->(d:Document)
    WITH s, COUNT(d) as d_count
    WHERE d_count < 1
    RETURN COUNT(s)
    """
    with driver.session() as s:
        record = s.run(cite_query).single()
    assert record.values()[0] == 0

    study = get_node_by_id(civic_eid2997_study["id"])
    expected_keys = {
        "id",
        "description",
        "direction",
        "predicate",
        "alleleOriginQualifier",
        "type",
    }
    civic_eid2997_study_cp = civic_eid2997_study.copy()
    civic_eid2997_study_cp["alleleOriginQualifier"] = civic_eid2997_study_cp[
        "alleleOriginQualifier"
    ]
    check_node_props(study, civic_eid2997_study_cp, expected_keys)


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
    expected_keys = {"id", "label"}
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
