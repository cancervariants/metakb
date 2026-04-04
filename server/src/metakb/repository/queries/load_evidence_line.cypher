MERGE (el:EvidenceLine {id: $evidence_line.id})
  ON CREATE SET
    el +=
      {
        extensions: $evidence_line.extensions,
        direction: $evidence_line.direction,
        evidence_outcome: $evidence_line.evidence_outcome
      }

WITH el
MATCH (strength:Strength {id: $evidence_line.has_strength.id})
MERGE (el)-[:HAS_STRENGTH]->(strength)

WITH el
UNWIND $item_ids AS item_id
MATCH (item {id: item_id})
MERGE (el)-[:HAS_EVIDENCE_ITEM]->(item)
