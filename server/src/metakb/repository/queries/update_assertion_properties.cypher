MATCH (s:Statement {id: $statement_id})
SET s.direction = $direction
RETURN s
