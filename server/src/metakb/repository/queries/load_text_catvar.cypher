MERGE (cv:Variation:CategoricalVariant:TextVariant {id: $cv.id})
  ON CREATE SET
    cv +=
      {
        name: $cv.name,
        description: $cv.description,
        aliases: $cv.aliases,
        extensions: $cv.extensions,
        mappings: $cv.mappings
      }
