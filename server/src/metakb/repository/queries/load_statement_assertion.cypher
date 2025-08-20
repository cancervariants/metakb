// create statement
MERGE (statement:Statement:StudyStatement {id: $statement.id})
  ON CREATE SET
    statement +=
      {
        description: $statement.description,
        predicate: $statement.predicate,
        proposition_type: $statement.proposition_type,
        allele_origin_qualifier: $statement.allele_origin_qualifier,
        direction: $statement.direction
      }
  ON MATCH SET
    statement +=
      {
        description: $statement.description,
        predicate: $statement.predicate,
        proposition_type: $statement.proposition_type,
        allele_origin_qualifier: $statement.allele_origin_qualifier,
        direction: $statement.direction
      }
// add strength node and connect it
MERGE (strength:Strength {id: $strength.id})
  ON CREATE SET
    strength +=
      {
        name: $strength.name,
        mappings: $strength.mappings,
        primary_coding: $strength.primary_coding
      }
MERGE (statement)-[:HAS_STRENGTH]->(strength)
// connect proposition components
// wrap therapeutic with a nullity guard to handle non-therapeutic propositions
MERGE
  (statement)-[:HAS_GENE_CONTEXT]->
  (:Gene {id: $statement.has_gene_context_id})
WITH statement, $statement.has_therapeutic_id AS tid
CALL {
  WITH statement, tid
  WHERE tid IS NOT NULL
  MERGE (statement)-[:HAS_THERAPEUTIC]->(:Therapeutic {id: tid})
}
MERGE
  (statement)-[:HAS_TUMOR_TYPE]->
  (:Condition {id: $statement.has_tumor_type_id})
MERGE (statement)-[:IS_SPECIFIED_BY]->(:Method {id: $statement.method_id})
MERGE
  (statement)-[:HAS_SUBJECT_VARIANT]->
  (:CategoricalVariant {id: $statement.has_subject_variant_id})
// add supporting documents
WITH statement, coalesce($statement.document_ids, []) AS doc_ids
UNWIND doc_ids AS doc_id
MERGE (doc:Document {id: doc_id})
MERGE (statement)-[:IS_REPORTED_IN]->(doc)
// add evidence lines
UNWIND coalesce($statement.evidence_lines, []) AS ev_line
MERGE (ev:EvidenceLine {id: ev_line.id})
  ON CREATE SET ev += {direction: ev_line.direction}
WITH ev, ev_line
UNWIND coalesce(ev_line.evidence_item_ids, []) AS ev_item_id
MERGE (item:Statement {id: ev_item_id})
MERGE (ev)-[:HAS_EVIDENCE_ITEM]->(item)
