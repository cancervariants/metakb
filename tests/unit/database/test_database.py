"""Validate property and relationship rules for graph DB."""
from typing import Optional

import pytest
from metakb.database import Graph


@pytest.fixture(scope="session")
def graph():
    """Return graph object."""
    g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
    yield g
    g.close()


@pytest.fixture(scope="session")
def check_unique_property(graph: Graph):
    """Verify that IDs are unique"""

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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def check_descriptor_count(graph: Graph, sources_count: int):
    """Check that value contains no more than 1 descriptor for each source,
    and at least 1 descriptor overall.
    """

    def _check_function(label: str, max_descriptors: int = sources_count):
        query = f"""
        MATCH (a:{label})
        OPTIONAL MATCH (a)<-[:DESCRIBES]-(b:{label}Descriptor)
        WITH a, COUNT(b) as descriptor_count
        WHERE descriptor_count > {max_descriptors} OR descriptor_count = 0
        RETURN COUNT(a)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="session")
def check_describes_count(graph: Graph):
    """Check that descriptor only describes 1 value object"""

    def _check_function(label: str):
        query = f"""
        MATCH (d:{label}Descriptor)
        OPTIONAL MATCH (d)-[:DESCRIBES]->(v:{label})
        WITH d, COUNT(v) as describes_count
        WHERE describes_count <> 1
        RETURN COUNT(d)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="session")
def check_proposition_relation(graph: Graph):
    """Check that a value's relations with a Proposition are correct.
    Provided relation value should be coming from the proposition, ie one of
    {"HAS_SUBJECT", "HAS_OBJECT", "HAS_OBJECT_QUALIFIER"}
    """

    def _check_function(label: str, relation: str):
        query = f"""
        MATCH (v:{label})
        WHERE NOT (v)<-[:{relation}]-(:Proposition)
        RETURN count(v)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="session")
def check_statement_relation(graph: Graph):
    """Check that descriptor is used in a statement."""

    def _check_function(value_label: str):
        query = f"""
        MATCH (d:{value_label}Descriptor)
        OPTIONAL MATCH (d)<-[:HAS_{value_label.upper()}]-(s:Statement)
        WITH d, COUNT(s) as s_count
        WHERE s_count < 1
        RETURN COUNT(s_count)
        """
        with graph.driver.session() as s:
            record = s.run(query).single()
        assert record.values()[0] == 0

    return _check_function


@pytest.fixture(scope="session")
def check_relation_count(graph: Graph):
    """Check that the quantity of relationships from one Node type to another
    are within a certain range.
    """

    def _check_function(
        self_label: str,
        other_label: str,
        relation: str,
        min: int = 1,
        max: Optional[int] = 1,
        direction: Optional[str] = "out",
    ):
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


def test_gene_rules(check_unique_property, check_single_label, check_descriptor_count):
    """Verify property and relationship rules for Gene nodes."""
    check_unique_property("Gene", "id")
    check_single_label("Gene")
    check_descriptor_count("Gene")


def test_gene_descriptor_rules(
    check_unique_property, check_single_label, check_describes_count
):
    """Verify property and relationship rules for GeneDescriptor nodes."""
    check_unique_property("GeneDescriptor", "id")
    check_single_label("GeneDescriptor")
    check_describes_count("Gene")


def test_variation_rules(
    graph, check_unique_property, check_descriptor_count, check_proposition_relation
):
    """Verify property and relationship rules for Variation nodes."""
    check_unique_property("Variation", "id")
    check_descriptor_count("Variation", 4)
    check_proposition_relation("Variation", "HAS_SUBJECT")


def test_variation_descriptor_rules(
    check_unique_property,
    check_single_label,
    check_describes_count,
    check_statement_relation,
    check_relation_count,
):
    """Verify property and relationship rules for VariationDescriptor nodes."""
    check_unique_property("VariationDescriptor", "id")
    check_single_label("VariationDescriptor")
    check_describes_count("Variation")
    check_statement_relation("Variation")
    check_relation_count("VariationDescriptor", "GeneDescriptor", "HAS_GENE")
    check_relation_count(
        "VariationDescriptor", "VariationGroup", "IN_VARIATION_GROUP", min=0, max=1
    )


def test_variation_group_rules(
    check_unique_property, check_single_label, check_relation_count
):
    """Verify property and relationship rules for VariationDescriptor nodes."""
    check_unique_property("VariationGroup", "id")
    check_single_label("VariationGroup")
    check_relation_count(
        "VariationGroup",
        "VariationDescriptor",
        "IN_VARIATION_GROUP",
        max=None,
        direction="in",
    )


def test_therapy_rules(
    check_unique_property,
    check_single_label,
    check_proposition_relation,
    check_descriptor_count,
    sources_count,
):
    """Verify property and relationship rules for Therapy nodes."""
    check_unique_property("Therapy", "id")
    check_single_label("Therapy")
    check_proposition_relation("Therapy", "HAS_OBJECT")
    # n+1 because civic divides imatinib and imatinib mesylate
    check_descriptor_count("Therapy", sources_count + 1)


def test_therapy_descriptor_rules(
    check_unique_property,
    check_single_label,
    check_describes_count,
    check_statement_relation,
):
    """Verify property and relationship rules for TherapyDescriptor nodes."""
    check_unique_property("TherapyDescriptor", "id")
    check_single_label("TherapyDescriptor")
    check_describes_count("Therapy")
    check_statement_relation("Therapy")


def test_disease_rules(
    check_unique_property,
    check_single_label,
    check_proposition_relation,
    check_descriptor_count,
    sources_count,
):
    """Verify property and relationship rules for disease nodes."""
    check_unique_property("Disease", "id")
    check_single_label("Disease")
    check_proposition_relation("Disease", "HAS_OBJECT_QUALIFIER")
    # n+1 because civic divides ALL and lymphoid leukemia
    check_descriptor_count("Disease", sources_count + 1)


def test_disease_descriptor_rules(
    check_unique_property,
    check_single_label,
    check_describes_count,
    check_statement_relation,
):
    """Verify property and relationship rules for DiseaseDescriptor nodes."""
    check_unique_property("DiseaseDescriptor", "id")
    check_single_label("DiseaseDescriptor")
    check_describes_count("Disease")
    check_statement_relation("Disease")


def test_statement_rules(
    graph: Graph,
    check_unique_property,
    check_single_label,
    check_descriptor_count,
    check_relation_count,
):
    """Verify property and relationship rules for Statement nodes."""
    check_unique_property("Statement", "id")
    check_single_label("Statement")

    check_relation_count("Statement", "VariationDescriptor", "HAS_VARIATION")
    check_relation_count("Statement", "DiseaseDescriptor", "HAS_DISEASE")
    check_relation_count("Statement", "TherapyDescriptor", "HAS_THERAPY", min=0)
    check_relation_count("Statement", "Proposition", "DEFINED_BY")
    check_relation_count("Statement", "Method", "USES_METHOD")


def test_proposition_rules(graph, check_unique_property):
    """Verify property and relationship rules for Proposition nodes."""
    check_unique_property("Proposition", "id")

    # all propositions are TherapeuticResponse, Prognostic, or Diagnostic
    prop_query = """
    MATCH (p:Proposition)
    WHERE NOT (p:TherapeuticResponse)
        AND NOT (p:Prognostic)
        AND NOT (p:Diagnostic)
    RETURN COUNT(p)
    """
    with graph.driver.session() as s:
        record = s.run(prop_query).single()
    assert record.values()[0] == 0

    # propositions have appropriate predicates and relationships
    tr_query = """
    MATCH (p:TherapeuticResponse)
    WHERE NOT (p)-[:HAS_SUBJECT]->(:Variation)
    OR NOT (p)-[:HAS_OBJECT]->(:Therapy)
    OR NOT (p)-[:HAS_OBJECT_QUALIFIER]->(:Disease)
    OR ((p.predicate <> "predicts_resistance_to")
        AND (p.predicate <> "predicts_sensitivity_to"))
    RETURN COUNT(p)
    """
    with graph.driver.session() as s:
        record = s.run(tr_query).single()
    assert record.values()[0] == 0

    prog_diag_query = """
    MATCH (p)
    WHERE ((p:Prognostic) OR (p:Diagnostic))
    AND (
        (NOT (p)-[:HAS_SUBJECT]->(:Variation))
        OR (NOT (p)-[:HAS_OBJECT_QUALIFIER]->(:Disease))
        OR ((p)-[:HAS_OBJECT]->(:Therapy))
        OR ((p:Prognostic)
            AND (p.predicate <> "is_prognostic_of_worse_outcome_for")
            AND (p.predicate <> "is_prognostic_of_better_outcome_for"))
        OR ((p:Diagnostic)
            AND (p.predicate <> "is_diagnostic_exclusion_criterion_for")
            AND (p.predicate <> "is_diagnostic_inclusion_criterion_for"))
    )
    RETURN COUNT(p)
    """
    with graph.driver.session() as s:
        record = s.run(prog_diag_query).single()
    assert record.values()[0] == 0


def test_document_rules(
    check_unique_property, check_single_label, check_relation_count
):
    """Verify property and relationship rules for Document nodes."""
    check_unique_property("Document", "id")
    check_single_label("Document")
    check_relation_count("Document", "Statement", "CITES", max=None, direction="in")


def test_method_rules(check_unique_property, check_single_label, check_relation_count):
    """Verify property and relationship rules for Method nodes."""
    check_unique_property("Method", "id")
    check_single_label("Method")
    check_relation_count("Method", "Statement", "USES_METHOD", max=None, direction="in")


def test_no_lost_nodes(graph: Graph):
    """Verify that no unlabeled or isolated nodes have been created."""
    # nonnormalizable nodes can be excepted
    labels_query = """
    MATCH (n)
    WHERE size(labels(n)) = 0
    AND NOT (n)<-[:CITES]-(:Statement)
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
