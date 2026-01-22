MERGE (p:Condition {id: $phenotype.id})
ON CREATE SET
  p +=
    {
      name: $phenotype.name,
      mappings: $phenotype.mappings
    }
SET p:Phenotype
