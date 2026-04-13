// load strength node
// since this query is responsible for actually generating the node properties,
// it needs to be called before statements/ev lines/anything else that connects to it
MERGE (strength:Strength {id: $strength.id})
  ON CREATE SET
    strength +=
      {
        name: $strength.name,
        mappings: $strength.mappings,
        primary_coding: $strength.primary_coding,
        extensions: $strength.extensions
      }
