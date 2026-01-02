MERGE (p:Phenotype:Condition {id: $phenotype.id})
  ON CREATE SET
    p +=
      {
        name: $phenotype.name,
        mappings: $phenotype.mappings,
        node_type: 'Phenotype'
      }
