MATCH (n:EvidenceLine {id: $evidence_line_id})
DETACH DELETE n
