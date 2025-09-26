MERGE (drug:Therapeutic:Drug {id: $drug.id})
  ON CREATE SET
    drug +=
      {
        normalized_id: $drug.normalized_id,
        name: $drug.name,
        mappings: $drug.mappings,
        aliases: $drug.aliases,
        extensions: $drug.extensions
      }
