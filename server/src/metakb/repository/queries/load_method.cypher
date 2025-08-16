MERGE (m:Method {id: $method.id})
  ON CREATE SET m += {name: $method.name}
