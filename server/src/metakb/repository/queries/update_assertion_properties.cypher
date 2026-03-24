MATCH (s:Statement {id: $statement_id})
SET s.direction = $direction
SET s.extensions = $extensions
RETURN s
