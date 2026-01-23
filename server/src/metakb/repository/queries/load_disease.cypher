MERGE (d:Condition {id: $disease.id})
ON CREATE SET
  d +=
    {
      normalized_id: $disease.normalized_id,
      name: $disease.name,
      mappings: $disease.mappings
    }
SET d:Disease
