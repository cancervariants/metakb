MATCH (s:Statement)
WHERE s.id STARTS WITH "metakb.assertion:"
RETURN s.id
