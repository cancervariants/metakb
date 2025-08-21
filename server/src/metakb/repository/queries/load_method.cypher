MERGE (m:Method {id: $method.id})
  ON CREATE SET m += {name: $method.name}
MERGE (m)-[:IS_REPORTED_IN]->(:Document {id: $method.reported_in.id})
