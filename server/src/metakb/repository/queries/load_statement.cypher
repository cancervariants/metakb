// create or update statement and its properties
MERGE (statement:Statement {id: $statement.id})
SET
  statement +=
    {
      url: $statement.url,
      description: $statement.description,
      extensions: $statement.extensions,
      predicate: $statement.predicate,
      proposition_type: $statement.proposition_type,
      allele_origin_qualifier: $statement.allele_origin_qualifier,
      direction: $statement.direction
    }

// sever edge to an existing strength node, and make edge to strength node
// this query gets used to both create AND update statements, so we'll just eat the cost
// of redundant queries to make things simpler
WITH statement
OPTIONAL MATCH (statement)-[old_rel:HAS_STRENGTH]->(:Strength)
DELETE old_rel
WITH statement
MERGE (strength:Strength {id: $statement.has_strength.id})
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

// replace condition block
WITH statement, $statement.has_condition AS conditionInput

CALL {
  WITH conditionInput
  WITH conditionInput
  WHERE conditionInput IS NOT NULL

  CALL {
    // ConditionSet case
    WITH conditionInput
    WITH conditionInput
    WHERE conditionInput.conditions IS NOT NULL

    MERGE (conditionSet:ConditionSet {id: conditionInput.id})
    SET conditionSet.membershipOperator = conditionInput.membershipOperator

    WITH conditionSet, conditionInput
    UNWIND conditionInput.conditions AS childInput

    CALL {
      // child condition set
      WITH childInput
      WITH childInput
      WHERE childInput.conditions IS NOT NULL

      MERGE (childConditionSet:ConditionSet {id: childInput.id})
      SET childConditionSet.membershipOperator = childInput.membershipOperator

      RETURN childConditionSet AS childNode

        UNION

      // child condition
      WITH childInput
      WITH childInput
      WHERE childInput.conditions IS NULL

      MERGE (childCondition:Condition {id: childInput.id})
      SET childCondition += childInput

      RETURN childCondition AS childNode
    }

    MERGE (conditionSet)-[:HAS_CONDITION]->(childNode)
    RETURN conditionSet AS builtCondition

      UNION

    // Condition case
    WITH conditionInput
    WITH conditionInput
    WHERE conditionInput.conditions IS NULL

    MERGE (condition:Condition {id: conditionInput.id})
    SET condition += conditionInput

    RETURN condition AS builtCondition
  }

  RETURN builtCondition
}

WITH statement, builtCondition
FOREACH (_ IN
CASE
  WHEN builtCondition IS NOT NULL THEN [1]
  ELSE []
END |
  MERGE (statement)-[:HAS_TUMOR_TYPE]->(builtCondition)
)

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

// add edges to contained evidence lines
CALL {
  WITH statement
  WITH statement, coalesce($statement.has_evidence_lines, []) AS ev_lines
  UNWIND ev_lines AS ev_line
  MATCH (el:EvidenceLine {id: ev_line.id})
  MERGE (statement)-[:HAS_EVIDENCE_LINE]->(el)
}
