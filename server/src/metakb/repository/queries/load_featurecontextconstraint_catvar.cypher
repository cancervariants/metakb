MERGE (cv:Variation:CategoricalVariant {id: $cv.id})
  ON CREATE SET
    cv +=
      {
        name: $cv.name,
        description: $cv.description,
        aliases: $cv.aliases,
        extensions: $cv.extensions,
        mappings: $cv.mappings
      }
MERGE (constr:Constraint:FeatureContextConstraint {id: $cv.has_constraint.id})
MERGE (cv)-[:HAS_CONSTRAINT]->(constr)
MERGE (g:Gene {id: $cv.has_constraint.has_feature_context.id})
  ON CREATE SET
    g +=
      {
        description: $cv.has_constraint.has_feature_context.description,
        name: $cv.has_constraint.has_feature_context.name,
        aliases: $cv.has_constraint.has_feature_context.aliases,
        mappings: $cv.has_constraint.has_feature_context.mappings,
        extensions: $cv.has_constraint.has_feature_context.extensions
      }
MERGE (constr)-[:HAS_FEATURE_CONTEXT]->(g)
