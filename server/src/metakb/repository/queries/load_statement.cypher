// create statement
MERGE (statement:Statement {id: $statement.id})
  ON CREATE SET
    statement +=
      {
        description: $statement.description,
        predicate: $statement.predicate,
        proposition_type: $statement.proposition_type,
        allele_origin_qualifier: $statement.allele_origin_qualifier,
        direction: $statement.direction
      }
// add strength node and connect it
MERGE (strength:Strength {id: $statement.has_strength.id})
  ON CREATE SET
    strength +=
      {
        name: $statement.has_strength.name,
        mappings: $statement.has_strength.mappings,
        primary_coding: $statement.has_strength.primary_coding
      }
MERGE (statement)-[:HAS_STRENGTH]->(strength)
// connect proposition components
MERGE (g:Gene {id: $statement.has_gene_context.id})
MERGE (statement)-[:HAS_GENE_CONTEXT]->(g)
WITH statement, $statement.has_therapeutic AS statement_therapeutic
FOREACH (_ IN
CASE
  WHEN statement_therapeutic IS NOT NULL THEN [1]
  ELSE []
END |
  MERGE (t:Therapeutic {id: statement_therapeutic.id})
  MERGE (statement)-[:HAS_THERAPEUTIC]->(t)
)
MERGE
  (statement)-[:HAS_TUMOR_TYPE]->
  (:Condition {id: $statement.has_tumor_type.id})
MERGE (method:Method {id: $statement.method.id})
MERGE (statement)-[:IS_SPECIFIED_BY]->(method)
MERGE (cv:CategoricalVariant {id: $statement.has_subject_variant.id})
MERGE (statement)-[:HAS_SUBJECT_VARIANT]->(cv)
// add supporting documents
WITH statement, coalesce($statement.documents, []) AS documents
UNWIND documents AS document
MERGE (doc:Document {id: document.id})
MERGE (statement)-[:IS_REPORTED_IN]->(doc)
// add evidence lines
WITH DISTINCT statement
WITH statement, coalesce($statement.evidence_lines, []) AS ev_lines
UNWIND ev_lines AS ev_line
MERGE (el:EvidenceLine {id: ev_line.id})
  ON CREATE SET el += {direction: ev_line.direction}
MERGE (statement)-[:HAS_EVIDENCE_LINE]->(el)

WITH el, coalesce(ev_line.evidence_item_ids, []) AS item_ids
UNWIND [x IN item_ids WHERE x IS NOT NULL] AS ev_item_id
MERGE (item:Statement {id: ev_item_id})
MERGE (el)-[:HAS_EVIDENCE_ITEM]->(item)
