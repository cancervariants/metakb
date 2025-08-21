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
MERGE (g:Gene {id: $statement.has_gene_context_id})
MERGE (statement)-[:HAS_GENE_CONTEXT]->(g)
WITH statement, $statement.has_therapeutic_id AS tid
FOREACH (_ IN
CASE
  WHEN tid IS NOT NULL THEN [1]
  ELSE []
END |
  MERGE (t:Therapeutic {id: tid})
  MERGE (statement)-[:HAS_THERAPEUTIC]->(t)
)
MERGE
  (statement)-[:HAS_TUMOR_TYPE]->
  (:Condition {id: $statement.has_tumor_type_id})
MERGE (method:Method {id: $statement.method_id})
MERGE (statement)-[:IS_SPECIFIED_BY]->(method)
MERGE (cv:CategoricalVariant {id: $statement.has_subject_variant_id})
MERGE (statement)-[:HAS_SUBJECT_VARIANT]->(cv)
// add supporting documents
WITH statement, coalesce($statement.document_ids, []) AS doc_ids
UNWIND doc_ids AS doc_id
MERGE (doc:Document {id: doc_id})
MERGE (statement)-[:IS_REPORTED_IN]->(doc)
