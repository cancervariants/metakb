MERGE (cs:Condition {id: $condition_set.id})
ON CREATE SET
  cs.membership_operator = $condition_set.membership_operator,
  cs.extensions = $condition_set.extensions
SET cs:ConditionSet

WITH cs, $condition_set AS condition_set
UNWIND coalesce(condition_set.conditions, []) AS child

MERGE (c:Condition {id: child.id})

SET
  c.name             = child.name,
  c.normalized_id    = child.normalized_id,
  c.mappings         = child.mappings,
  c.membership_operator = coalesce(child.membership_operator, c.membership_operator),
  c.extensions       = coalesce(child.extensions, c.extensions)

MERGE (cs)-[:HAS_CONDITION]->(c)
