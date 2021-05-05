"""Validate property and relationship rules for graph DB."""
import pytest
from metakb.database import Graph


@pytest.fixture(scope='module')
def graph():
    """Return graph object."""
    g = Graph(uri="bolt://localhost:7687", credentials=("neo4j", "admin"))
    yield g
    g.close()


def test_gene_rules(graph):
    """Verify property and relationship rules for Gene nodes."""
    ids = set()
    with graph.driver.session() as s:
        genes = s.run("MATCH (g:Gene) RETURN g")
        for gene in genes:
            values = gene.values()[0]

            # ID is unique
            gene_id = values['id']
            assert gene_id not in ids
            ids.add(gene_id)

            # labeling is correct
            assert set(values.labels) == {'Gene'}

            # only described by one or two GeneDescriptors
            d_query = "MATCH (:Gene {id:$gene_id}) <-[:DESCRIBES]- (:GeneDescriptor) RETURN count(*)"  # noqa: E501
            described_by = s.run(d_query, gene_id=gene_id)
            assert described_by.value()[0] in (1, 2)


def test_gene_descriptor_rules(graph):
    """Verify property and relationship rules for GeneDescriptor nodes."""
    ids = set()
    with graph.driver.session() as s:
        gene_descrs = s.run("MATCH (g:GeneDescriptor) RETURN g")
        for descr in gene_descrs:
            values = descr.values()[0]

            # ID is unique
            descr_id = values['id']
            assert descr_id not in ids
            ids.add(descr_id)

            # labeling is correct
            assert set(values.labels) == {'GeneDescriptor'}

            # describes only 1 Gene
            descr_query = "MATCH (:GeneDescriptor {id:$descr_id}) -[:DESCRIBES]-> (:Gene) RETURN count(*)"  # noqa: E501
            genes = s.run(descr_query, descr_id=descr_id)
            assert genes.value()[0] == 1

            # described by 1 or more GeneDescriptor
            gene_query = "MATCH (:GeneDescriptor {id:$descr_id}) <-[:HAS_GENE]- (:VariationDescriptor) RETURN count(*)"  # noqa: E501
            gene_descrs = s.run(gene_query, descr_id=descr_id)
            assert gene_descrs.value()[0] >= 1


def test_variation_rules(graph):
    """Verify property and relationship rules for Variation nodes."""
    ids = set()
    with graph.driver.session() as s:
        variations = s.run("MATCH (v:Variation) RETURN v")
        for v in variations:
            values = v.values()[0]

            # ID is unique
            v_id = values['id']
            assert v_id not in ids
            ids.add(v_id)

            # labeling is correct
            assert set(values.labels) == {'Variation', 'Allele'}

            # described by at least one VariationDescriptor
            query = "MATCH (:Variation {id:$v_id}) <-[:DESCRIBES]- (:VariationDescriptor) RETURN count(*)"  # noqa: E501
            described_by = s.run(query, v_id=v_id)
            assert described_by.value()[0] >= 1

            # Proposition relationships >= 1 and matches
            query = "MATCH (:Variation {id:$v_id}) <-[:HAS_SUBJECT]- (p:Proposition) RETURN p.id"  # noqa: E501
            props_in = {v[0] for v in s.run(query, v_id=v_id).values()}
            assert len(props_in) >= 1
            query = "MATCH (:Variation {id:$v_id}) -[:IS_SUBJECT_OF]-> (p:Proposition) RETURN p.id"  # noqa: E501
            props_out = {v[0] for v in s.run(query, v_id=v_id).values()}
            assert props_in == props_out


def test_variation_descriptor_rules(graph):
    """Verify property and relationship rules for VariationDescriptor nodes."""
    ids = set()
    with graph.driver.session() as s:
        var_descrs = s.run("MATCH (v:VariationDescriptor) RETURN v")
        for descr in var_descrs:
            values = descr.values()[0]

            # ID is unique
            descr_id = values['id']
            assert descr_id not in ids
            ids.add(descr_id)

            # labeling is correct
            assert set(values.labels) == {'VariationDescriptor'}

            # describes only 1 Variation
            descr_query = "MATCH (:VariationDescriptor {id:$descr_id}) -[:DESCRIBES]-> (:Variation) RETURN count(*)"  # noqa: E501
            variations = s.run(descr_query, descr_id=descr_id)
            assert variations.value()[0] == 1

            # has only 1 Gene
            gene_query = "MATCH (:VariationDescriptor {id:$descr_id}) -[:HAS_GENE]-> (:GeneDescriptor) RETURN count(*)"  # noqa: E501
            gene_descrs = s.run(gene_query, descr_id=descr_id)
            assert gene_descrs.value()[0] == 1

            # in <= 2 VariationGroups.
            # This number could change (represents the known max, not a rule)
            grp_query = "MATCH (:VariationDescriptor {id:$descr_id}) -[:IN_VARIATION_GROUP]-> (:VariationGroup) RETURN count(*)"  # noqa: E501
            grp = s.run(grp_query, descr_id=descr_id)
            assert grp.value()[0] <= 2

            # used by at least 1 Statement
            statement_query = "MATCH (:VariationDescriptor {id:$descr_id}) <-[:HAS_VARIATION]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(statement_query, descr_id=descr_id)
            assert statements.value()[0] >= 1


def test_variation_group_rules(graph):
    """Verify property and relationship rules for VariationDescriptor nodes."""
    ids = set()
    with graph.driver.session() as s:
        groups = s.run("MATCH (g:VariationGroup) return g")
        for grp in groups:
            values = grp.values()[0]
            grp_id = values['id']
            # ID is unique
            assert grp_id not in ids
            ids.add(grp_id)
            # labeling is correct
            assert set(values.labels) == {'VariationGroup'}
            query = "MATCH (:VariationDescriptor) -[:IN_VARIATION_GROUP]-> (:VariationGroup {id:$grp_id}) RETURN count(*)"  # noqa: E501
            members = s.run(query, grp_id=grp_id)
            # group has at least 1 member
            assert members.value()[0] >= 1


def test_statement_rules(graph):
    """Verify property and relationship rules for Statement nodes."""
    ids = set()
    with graph.driver.session() as s:
        statements = s.run("MATCH (s:Statement) RETURN s")
        for statement in statements:
            values = statement.values()[0]

            # ID is unique
            s_id = values['id']
            assert s_id not in ids
            ids.add(s_id)

            # labeling is correct
            assert set(values.labels) == {'Statement'}

            # Statement has 1 VariationDescriptor
            query = "MATCH (:Statement {id:$s_id}) -[:HAS_VARIATION]-> (:VariationDescriptor) RETURN count(*)"  # noqa: E501
            var = s.run(query, s_id=s_id)
            assert var.value()[0] == 1

            # Statement has 1 DiseaseDescriptor
            query = "MATCH (:Statement {id:$s_id}) -[:HAS_DISEASE]-> (:DiseaseDescriptor) RETURN count(*)"  # noqa: E501
            disease = s.run(query, s_id=s_id)
            assert disease.value()[0] == 1

            # Statement has 0 or 1 TherapyDescriptor
            query = "MATCH (:Statement {id:$s_id}) -[:HAS_THERAPY]-> (:TherapyDescriptor) RETURN count(*)"  # noqa: E501
            therapy = s.run(query, s_id=s_id)
            assert therapy.value()[0] in [0, 1]

            # Statement defines 1 Proposition
            query = "MATCH (:Statement {id:$s_id}) -[:DEFINED_BY]-> (:Proposition) RETURN count(*)"  # noqa: E501
            prop = s.run(query, s_id=s_id)
            assert prop.value()[0] == 1

            # Statement has 1 Method
            query = "MATCH (:Statement {id:$s_id}) -[:USES_METHOD]-> (:Method) RETURN count(*)"  # noqa: E501
            method = s.run(query, s_id=s_id)
            assert method.value()[0] == 1

            # Statement has at least 1 SupportEvidence
            query = "MATCH (:Statement {id:$s_id}) -[:CITES]-> (:SupportEvidence) RETURN count(*)"  # noqa: E501
            ev = s.run(query, s_id=s_id)
            assert len(ev.data()) >= 1


def test_proposition_rules(graph):
    """Verify property and relationship rules for Proposition nodes."""
    ids = set()
    with graph.driver.session() as s:
        props = s.run("MATCH (s:Proposition) RETURN s")
        for prop in props:
            values = prop.values()[0]

            # ID is unique
            p_id = values['id']
            assert p_id not in ids
            ids.add(p_id)
            # labeling is correct
            assert set(values.labels) in [
                {'Proposition', 'TherapeuticResponse'},
                {'Proposition', 'Prognostic'}
            ]

            # Proposition is defined by 1 or more Statements
            query = "MATCH (:Proposition {id:$p_id}) <-[:DEFINED_BY]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(query, p_id=p_id)
            assert statements.value()[0] >= 1

            # Proposition-Variation relationships >= 1 and match
            query = "MATCH (:Proposition {id:$p_id}) -[:HAS_SUBJECT]-> (v:Variation) RETURN v.id"  # noqa: E501
            variations_in = {v[0] for v in s.run(query, p_id=p_id).values()}
            assert len(variations_in) >= 1
            query = "MATCH (:Proposition {id:$p_id}) <-[:IS_SUBJECT_OF]- (v:Variation) RETURN v.id"  # noqa: E501
            variations_out = {v[0] for v in s.run(query, p_id=p_id).values()}
            assert variations_in == variations_out

            query = "MATCH (:Proposition {id:$p_id}) -[:HAS_OBJECT]-> (v:Therapy) RETURN v.id"  # noqa: E501
            therapies_in = {v[0] for v in s.run(query, p_id=p_id).values()}
            if 'TherapeuticResponse' in values.labels:
                assert len(therapies_in) >= 1
            elif 'Prognostic' in values.labels:
                assert len(therapies_in) == 0
            query = "MATCH (:Proposition {id:$p_id}) <-[:IS_OBJECT_OF]- (v:Therapy) RETURN v.id"  # noqa: E501
            therapies_out = {v[0] for v in s.run(query,
                                                 p_id=p_id).values()}
            assert therapies_in == therapies_out

            # Proposition-Disease relationships >= 1 and match
            query = "MATCH (:Proposition {id:$p_id}) -[:HAS_OBJECT_QUALIFIER]-> (v:Disease) RETURN v.id"  # noqa: E501
            diseases_in = {v[0] for v in s.run(query, p_id=p_id).values()}
            assert len(diseases_in) >= 1
            query = "MATCH (:Proposition {id:$p_id}) <-[:IS_OBJECT_QUALIFIER_OF]- (v:Disease) RETURN v.id"  # noqa: E501
            diseases_out = {v[0] for v in s.run(query, p_id=p_id).values()}
            assert diseases_in == diseases_out


def test_therapy_descriptor_rules(graph):
    """Verify property and relationship rules for TherapyDescriptor nodes."""
    ids = set()
    with graph.driver.session() as s:
        therapy_descrs = s.run("MATCH (v:TherapyDescriptor) RETURN v")
        for descr in therapy_descrs:
            values = descr.values()[0]

            # ID is unique
            descr_id = values['id']
            assert descr_id not in ids
            ids.add(descr_id)

            # labeling is correct
            assert set(values.labels) == {'TherapyDescriptor'}

            # describes only 1 Variation
            descr_query = "MATCH (:TherapyDescriptor {id:$descr_id}) -[:DESCRIBES]-> (:Therapy) RETURN count(*)"  # noqa: E501
            variations = s.run(descr_query, descr_id=descr_id)
            assert variations.value()[0] == 1

            # used by at least 1 Statement
            statement_query = "MATCH (:TherapyDescriptor {id:$descr_id}) <-[:HAS_THERAPY]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(statement_query, descr_id=descr_id)
            assert statements.value()[0] >= 1


def test_therapy_rules(graph):
    """Verify property and relationship rules for Therapy nodes."""
    ids = set()
    with graph.driver.session() as s:
        therapies = s.run("MATCH (n:Therapy) RETURN n")
        for therapy in therapies:
            values = therapy.values()[0]

            # ID is unique
            th_id = values['id']
            assert th_id not in ids
            ids.add(th_id)

            # labeling is correct
            assert set(values.labels) == {'Therapy'}

            # described by at least one DiseaseDescriptor
            query = "MATCH (:Therapy {id:$th_id}) <-[:DESCRIBES]- (:TherapyDescriptor) RETURN count(*)"  # noqa: E501
            described_by = s.run(query, th_id=th_id)
            assert described_by.value()[0] >= 1

            # Proposition relationships >= 1 and matches
            query = "MATCH (:Therapy {id:$th_id}) <-[:HAS_OBJECT]- (p:Proposition) RETURN p.id"  # noqa: E501
            props_in = {v[0] for v in s.run(query, th_id=th_id).values()}
            assert len(props_in) >= 1
            query = "MATCH (:Therapy {id:$th_id}) -[:IS_OBJECT_OF]-> (p:Proposition) RETURN p.id"  # noqa: E501
            props_out = {v[0] for v in s.run(query, th_id=th_id).values()}
            assert props_in == props_out


def test_disease_descriptor_rules(graph):
    """Verify property and relationship rules for DiseaseDescriptor nodes."""
    ids = set()
    with graph.driver.session() as s:
        disease_descrs = s.run("MATCH (v:DiseaseDescriptor) RETURN v")
        for descr in disease_descrs:
            values = descr.values()[0]

            # ID is unique
            descr_id = values['id']
            assert descr_id not in ids
            ids.add(descr_id)

            # labeling is correct
            assert set(values.labels) == {'DiseaseDescriptor'}

            # describes only 1 Variation
            descr_query = "MATCH (:DiseaseDescriptor {id:$descr_id}) -[:DESCRIBES]-> (:Disease) RETURN count(*)"  # noqa: E501
            variations = s.run(descr_query, descr_id=descr_id)
            assert variations.value()[0] == 1

            # used by at least 1 Statement
            statement_query = "MATCH (:DiseaseDescriptor {id:$descr_id}) <-[:HAS_DISEASE]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(statement_query, descr_id=descr_id)
            assert statements.value()[0] >= 1


def test_disease_rules(graph):
    """Verify property and relationship rules for Disease nodes."""
    ids = set()
    with graph.driver.session() as s:
        diseases = s.run("MATCH (v:Disease) RETURN v")
        for v in diseases:
            values = v.values()[0]

            # ID is unique
            v_id = values['id']
            assert v_id not in ids
            ids.add(v_id)

            # labeling is correct
            assert set(values.labels) == {'Disease'}

            # described by at least one DiseaseDescriptor
            query = "MATCH (:Disease {id:$v_id}) <-[:DESCRIBES]- (:DiseaseDescriptor) RETURN count(*)"  # noqa: E501
            described_by = s.run(query, v_id=v_id)
            assert described_by.value()[0] >= 1

            # Proposition relationships >= 1 and matches
            query = "MATCH (:Disease {id:$v_id}) <-[:HAS_OBJECT_QUALIFIER]- (p:Proposition) RETURN p.id"  # noqa: E501
            props_in = {v[0] for v in s.run(query, v_id=v_id).values()}
            assert len(props_in) >= 1
            query = "MATCH (:Disease {id:$v_id}) -[:IS_OBJECT_QUALIFIER_OF]-> (p:Proposition) RETURN p.id"  # noqa: E501
            props_out = {v[0] for v in s.run(query, v_id=v_id).values()}
            assert props_in == props_out


def test_support_evidence_rules(graph):
    """Verify property and relationship rules for SupportEvidence nodes."""
    ids = set()
    with graph.driver.session() as s:
        support_evidence = s.run("MATCH (s:SupportEvidence) RETURN s")
        for ev in support_evidence:
            values = ev.values()[0]

            # ID is unique
            e_id = values['id']
            assert e_id not in ids
            ids.add(e_id)

            # labeling is correct
            assert set(values.labels) == {'SupportEvidence'}

            # SupportEvidence is used by 1 or more Statements
            query = "MATCH (:SupportEvidence {id:$e_id}) <-[:CITES]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(query, e_id=e_id)
            assert statements.value()[0] >= 1


def test_method_rules(graph):
    """Verify property and relationship rules for Method nodes."""
    ids = set()
    with graph.driver.session() as s:
        methods = s.run("MATCH (s:Method) RETURN s")
        for method in methods:
            values = method.values()[0]

            # ID is unique
            p_id = values['id']
            assert p_id not in ids
            ids.add(p_id)

            # labeling is correct
            assert set(values.labels) == {'Method'}

            # Method is used by 1 or more Statements
            query = "MATCH (:Method {id:$p_id}) <-[:USES_METHOD]- (:Statement) RETURN count(*)"  # noqa: E501
            statements = s.run(query, p_id=p_id)
            assert statements.value()[0] >= 1
