MERGE (m:Method {id: $method.id})
  ON CREATE SET m += {name: $method.name}
MERGE (doc:Document {id: $method.has_document.id})
MERGE (m)-[:IS_REPORTED_IN]->(doc)
