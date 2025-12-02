MERGE (g:Gene {id: $gene.id})
  ON CREATE SET
    g +=
      {
        description: $gene.description,
        name: $gene.name,
        mappings: $gene.mappings,
        extensions: $gene.extensions
      }
MERGE (ng:NormalizedGene {id: $gene.normalized_gene.id})
  ON CREATE SET
    ng +=
      {
        name: $gene.normalized_gene.name,
        mappings: $gene.normalized_gene.mappings,
        extensions: $gene.normalized_gene.extensions
      }
MERGE (g)-[:NORMALIZES_TO]->(ng)
