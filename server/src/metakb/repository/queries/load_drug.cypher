MERGE (drug:Therapeutic:Drug {id: $drug.id})
  ON CREATE SET
    drug +=
      {
        name: $drug.name,
        mappings: $drug.mappings,
        aliases: $drug.aliases,
        extensions: $drug.extensions
      }
