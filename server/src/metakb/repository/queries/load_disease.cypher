MERGE (d:Condition {id: $disease.id})
  ON CREATE SET d += {name: $disease.name, mappings: $disease.mappings}
SET d: Disease
