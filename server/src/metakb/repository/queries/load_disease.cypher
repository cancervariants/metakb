MERGE (d:Disease:Condition {id: $disease.id})
  ON CREATE SET d += {name: $disease.name, mappings: $disease.mappings}
MERGE
  (normalized_disease:NormalizedDisease {id: $disease.normalized_disease.id})
  ON CREATE SET
    normalized_disease +=
      {
        name: $disease.normalized_disease.name,
        mappings: $disease.normalized_disease.mappings
      }
MERGE (d)-[:NORMALIZES_TO]->(normalized_disease)
