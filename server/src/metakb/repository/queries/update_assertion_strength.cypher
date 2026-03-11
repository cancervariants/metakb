MATCH (s:Statement {id: $statement_id})

// grab the old strength association to delete the edge later
OPTIONAL MATCH (s)-[old_rel:HAS_STRENGTH]->(old_strength:Strength)

// match against the new strength node and create it if it doesn't exist
MERGE (strength:Strength {id: $strength.id})
  ON CREATE SET
    strength +=
      {
        name: $strength.name,
        mappings: $strength.mappings,
        primary_coding: $strength.primary_coding
      }

// delete edge to previous and merge into an edge to the new strength value
WITH s, strength, old_rel, old_strength
DELETE old_rel
MERGE (s)-[:HAS_STRENGTH]->(strength)

// "garbage collect" -- if the old strength value is no longer used anywhere, then remove it
WITH old_strength
WHERE old_strength IS NOT NULL AND NOT (old_strength)--()
DELETE old_strength
