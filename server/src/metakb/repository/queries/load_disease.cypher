MERGE (d:Condition {id: $disease.id})
  ON CREATE SET
    d +=
      {
        name: $disease.name,
        mappings: $disease.mappings,
        primary_coding: $disease.primary_coding
      }
SET d: Disease
