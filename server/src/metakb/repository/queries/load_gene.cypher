MERGE (g:Gene {id: $gene.id})
  ON CREATE SET
    g +=
      {
        description: $gene.description,
        name: $gene.name,
        aliases: $gene.aliases,
        mappings: $gene.mappings,
        extensions: $gene.extensions
      }
