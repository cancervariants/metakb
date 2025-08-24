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

// add classification node and connect it
WITH statement, $statement.has_classification AS statement_classification
FOREACH (_ IN
CASE
  WHEN statement_classification IS NOT NULL THEN [1]
  ELSE []
END |
  MERGE (classification:Classification {id: $statement.has_classification.id})
    ON CREATE SET
      classification +=
        {primary_coding: $statement.has_classification.primary_coding}
  MERGE (statement)-[:HAS_CLASSIFICATION]->(classification)
)

// connect proposition components
MERGE (g:Gene {id: $statement.has_gene.id})
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
MERGE (c:Condition {id: $statement.has_condition.id})
MERGE (statement)-[:HAS_TUMOR_TYPE]->(c)
MERGE (method:Method {id: $statement.has_method.id})
MERGE (statement)-[:IS_SPECIFIED_BY]->(method)
MERGE (cv:CategoricalVariant {id: $statement.has_variant.id})
MERGE (statement)-[:HAS_SUBJECT_VARIANT]->(cv)

// add edges to supporting documents
WITH statement
CALL {
  WITH statement
  WITH statement, coalesce($statement.has_documents, []) AS docs
  UNWIND docs AS document
  MERGE (doc:Document {id: document.id})
  MERGE (statement)-[:IS_REPORTED_IN]->(doc)
  RETURN count(*) AS _docs
}

// add evidence lines and edges to statements
CALL {
  WITH statement
  WITH statement, coalesce($statement.has_evidence_lines, []) AS ev_lines
  UNWIND ev_lines AS ev_line
  MERGE (el:EvidenceLine {id: ev_line.id})
    ON CREATE SET el += {direction: ev_line.direction}
  MERGE (statement)-[:HAS_EVIDENCE_LINE]->(el)

  WITH statement, el, ev_line
  UNWIND coalesce(ev_line.evidence_items, []) AS ev_item
  MERGE (item:Statement {id: ev_item.id})
  MERGE (el)-[:HAS_EVIDENCE_ITEM]->(item)
  RETURN count(*) AS _ev
}

RETURN 1
