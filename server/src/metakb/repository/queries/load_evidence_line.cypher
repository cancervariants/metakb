MERGE (el:EvidenceLine {id: $evidence_line.id})
  ON CREATE SET
    el +=
      {
        extensions: $evidence_line.extensions,
        direction: $evidence_line.direction,
        evidence_outcome: $evidence_line.evidence_outcome
      }

// sometimes source evidence lines don't have richer metadata so there's no
// associated strength (eg with civic assertions)
WITH el
OPTIONAL MATCH (strength:Strength {id: $strength_id})
FOREACH (_ IN
CASE
  WHEN strength IS NULL THEN []
  ELSE [1]
END |
  MERGE (el)-[:HAS_STRENGTH]->(strength)
)

WITH el
UNWIND $item_ids AS item_id
MATCH (item {id: item_id})
MERGE (el)-[:HAS_EVIDENCE_ITEM]->(item)
