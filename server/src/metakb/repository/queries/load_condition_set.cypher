MERGE (cs:Condition:ConditionSet {id: $condition_set.id})
ON CREATE SET
  cs.membership_operator = $condition_set.membership_operator,
  cs.extensions = $condition_set.extensions,
  cs.node_type = $condition_set.node_type

WITH cs, $condition_set AS condition_set
UNWIND coalesce(condition_set.conditions, []) AS child

MERGE (c:Condition {id: child.id})

FOREACH (_ IN CASE WHEN child.node_type = 'Disease' THEN [1] ELSE [] END |
  SET c:Disease
)
FOREACH (_ IN CASE WHEN child.node_type = 'Phenotype' THEN [1] ELSE [] END |
  SET c:Phenotype
)
FOREACH (_ IN CASE WHEN child.node_type = 'ConditionSet' THEN [1] ELSE [] END |
  SET c:ConditionSet
)

SET
  c.node_type        = child.node_type,
  c.name             = child.name,
  c.normalized_id    = child.normalized_id,
  c.mappings         = child.mappings,
  c.membership_operator = coalesce(child.membership_operator, c.membership_operator),
  c.extensions       = coalesce(child.extensions, c.extensions)

MERGE (cs)-[:HAS_CONDITION]->(c)
