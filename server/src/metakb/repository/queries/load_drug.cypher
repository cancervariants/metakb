MERGE (drug:Therapeutic:Drug {id: $drug.id})
  ON CREATE SET
    drug +=
      {name: $drug.name, mappings: $drug.mappings, extensions: $drug.extensions}
MERGE (normalized_drug:NormalizedDrug {id: $drug.normalized_drug.id})
  ON CREATE SET
    normalized_drug +=
      {
        name: $drug.normalized_drug.name,
        mappings: $drug.normalized_drug.mappings,
        extensions: $drug.normalized_drug.extensions
      }
MERGE (drug)-[:NORMALIZES_TO]->(normalized_drug)
