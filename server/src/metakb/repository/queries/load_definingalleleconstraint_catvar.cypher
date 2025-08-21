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
  (constr:Constraint:DefiningAlleleConstraint {id: $cv.constraint.id})
  ON CREATE SET cv += {relations: $cv.constraint.relations}
MERGE
  (allele:Variation:MolecularVariation:Allele {id: $cv.constraint.allele.id})
  ON CREATE SET
    allele +=
      {
        name: $cv.constraint.allele.name,
        digest: $cv.constraint.allele.digest,
        expression_hgvs_g: $cv.constraint.allele.expression_hgvs_g,
        expression_hgvs_c: $cv.constraint.allele.expression_hgvs_c,
        expression_hgvs_p: $cv.constraint.allele.expression_hgvs_p
      }
MERGE (constr)-[:HAS_DEFINING_ALLELE]->(allele)
MERGE (sl:Location:SequenceLocation {id: $cv.constraint.allele.location.id})
  ON CREATE SET
    sl +=
      {
        digest: $cv.constraint.allele.location.digest,
        start: $cv.constraint.allele.location.start,
        end: $cv.constraint.allele.location.end,
        refget_accession:
          $cv.constraint.allele.location.sequenceReference.refgetAccession,
        sequence: $cv.constraint.allele.location.sequence
      }
MERGE (allele)-[:HAS_LOCATION]->(sl)

// handle different kinds of state objects
FOREACH (_ IN
CASE
  WHEN $cv.constraint.allele.state.type = 'LiteralSequenceExpression' THEN [1]
  ELSE []
END |
  MERGE
    (lse:SequenceExpression:LiteralSequenceExpression
      {sequence: $cv.constraint.allele.state.sequence})
  MERGE (allele)-[:HAS_STATE]->(lse)
)
FOREACH (_ IN
CASE
  WHEN $cv.constraint.allele.state.type = 'ReferenceLengthExpression' THEN [1]
  ELSE []
END |
  MERGE
    (rle:SequenceExpression:ReferenceLengthExpression
      {
        length: $cv.constraint.allele.state.length,
        repeat_subunit_length:
          $cv.constraint.allele.state.repeat_subunit_length,
        sequence: $cv.constraint.allele.state.sequence
      })
  MERGE (allele)-[:HAS_STATE]->(rle)
)

WITH cv
UNWIND $cv.members AS m
MERGE (member_allele:Variation:MolecularVariation:Allele {id: m.id})
  ON CREATE SET
    member_allele +=
      {
        name: m.name,
        digest: m.digest,
        expression_hgvs_g: m.expression_hgvs_g,
        expression_hgvs_c: m.expression_hgvs_c,
        expression_hgvs_p: m.expression_hgvs_p
      }
MERGE (cv)-[:HAS_MEMBER]->(member_allele)
MERGE (member_sl:Location:SequenceLocation {id: m.location.id})
  ON CREATE SET
    member_sl +=
      {
        digest: m.location.digest,
        start: m.location.start,
        end: m.location.end,
        refget_accession: m.location.sequenceReference.refgetAccession,
        sequence: m.location.sequence
      }
MERGE (member_allele)-[:HAS_LOCATION]->(member_sl)

// handle different kinds of state objects
FOREACH (_ IN
CASE
  WHEN m.state.type = 'LiteralSequenceExpression' THEN [1]
  ELSE []
END |
  MERGE
    (member_lse:SequenceExpression:LiteralSequenceExpression
      {sequence: m.state.sequence})
  MERGE (member_allele)-[:HAS_STATE]->(member_lse)
)
FOREACH (_ IN
CASE
  WHEN m.state.type = 'ReferenceLengthExpression' THEN [1]
  ELSE []
END |
  MERGE
    (member_rle:SequenceExpression:ReferenceLengthExpression
      {
        length: m.state.length,
        repeat_subunit_length: m.state.repeat_subunit_length,
        sequence: m.state.sequence
      })
  MERGE (member_allele)-[:HAS_STATE]->(member_rle)
)
