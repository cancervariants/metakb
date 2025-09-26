MERGE (g:Gene {id: $gene.id})
  ON CREATE SET
    g +=
      {
        normalized_id: $gene.normalized_id,
        description: $gene.description,
        name: $gene.name,
        aliases: $gene.aliases,
        mappings: $gene.mappings,
        extensions: $gene.extensions
      }
