MERGE (cv:Variation:CategoricalVariant:ProteinSequenceConsequence {id: $cv.id})
  ON CREATE SET
    cv +=
      {
        name: $cv.name,
        description: $cv.description,
        aliases: $cv.aliases,
        extensions: $cv.extensions,
        mappings: $cv.mappings
      }
MERGE
  (cv)-[:HAS_CONSTRAINT]->
  (constr:Constraint:DefiningAlleleConstraint {id: $cv.has_constraint.id})
  ON CREATE SET cv += {relations: $cv.has_constraint.relations}
MERGE
  (allele:Variation:MolecularVariation:Allele
    {id: $cv.has_constraint.has_defining_allele.id})
  ON CREATE SET
    allele +=
      {
        name: $cv.has_constraint.has_defining_allele.name,
        digest: $cv.has_constraint.has_defining_allele.digest,
        expressions: $cv.has_constraint.has_defining_allele.expressions
      }
MERGE (constr)-[:HAS_DEFINING_ALLELE]->(allele)
MERGE
  (sl:Location:SequenceLocation
    {id: $cv.has_constraint.has_defining_allele.has_location.id})
  ON CREATE SET
    sl +=
      {
        digest: $cv.has_constraint.has_defining_allele.has_location.digest,
        start: $cv.has_constraint.has_defining_allele.has_location.start,
        end: $cv.has_constraint.has_defining_allele.has_location.end,
        refget_accession:
          $cv.has_constraint.has_defining_allele.has_location.refget_accession,
        sequence: $cv.has_constraint.has_defining_allele.has_location.sequence
      }
MERGE (allele)-[:HAS_LOCATION]->(sl)

// handle different kinds of state objects
FOREACH (_ IN
CASE
  WHEN
    $cv.has_constraint.has_defining_allele.state.type =
    'LiteralSequenceExpression'
    THEN [1]
  ELSE []
END |
  MERGE
    (lse:SequenceExpression:LiteralSequenceExpression
      {sequence: $cv.has_constraint.has_defining_allele.state.sequence})
  MERGE (allele)-[:HAS_STATE]->(lse)
)
FOREACH (_ IN
CASE
  WHEN
    $cv.has_constraint.has_defining_allele.state.type =
    'ReferenceLengthExpression'
    THEN [1]
  ELSE []
END |
  MERGE
    (rle:SequenceExpression:ReferenceLengthExpression
      {
        length: $cv.has_constraint.has_defining_allele.has_state.length,
        repeat_subunit_length:
          $cv.has_constraint.has_defining_allele.has_state.repeat_subunit_length,
        sequence: $cv.has_constraint.has_defining_allele.has_state.sequence
      })
  MERGE (allele)-[:HAS_STATE]->(rle)
)

WITH cv
UNWIND $cv.has_members AS m
MERGE (member_allele:Variation:MolecularVariation:Allele {id: m.id})
  ON CREATE SET
    member_allele += {name: m.name, digest: m.digest, expression: m.expressions}
MERGE (cv)-[:HAS_MEMBER]->(member_allele)
MERGE (member_sl:Location:SequenceLocation {id: m.has_location.id})
  ON CREATE SET
    member_sl +=
      {
        digest: m.has_location.digest,
        start: m.has_location.start,
        end: m.has_location.end,
        refget_accession: m.has_location.refget_accession,
        sequence: m.haslocation.sequence
      }
MERGE (member_allele)-[:HAS_LOCATION]->(member_sl)

// handle different kinds of state objects
FOREACH (_ IN
CASE
  WHEN m.has_state.type = 'LiteralSequenceExpression' THEN [1]
  ELSE []
END |
  MERGE
    (member_lse:SequenceExpression:LiteralSequenceExpression
      {sequence: m.has_state.sequence})
  MERGE (member_allele)-[:HAS_STATE]->(member_lse)
)
FOREACH (_ IN
CASE
  WHEN m.has_state.type = 'ReferenceLengthExpression' THEN [1]
  ELSE []
END |
  MERGE
    (member_rle:SequenceExpression:ReferenceLengthExpression
      {
        length: m.has_state.length,
        repeat_subunit_length: m.has_state.repeat_subunit_length,
        sequence: m.has_state.sequence
      })
  MERGE (member_allele)-[:HAS_STATE]->(member_rle)
)
