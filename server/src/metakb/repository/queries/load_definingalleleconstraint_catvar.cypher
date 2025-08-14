MERGE (cv:Variation:CategoricalVariant:ProteinSequenceConsequence { id: $cv.id })
ON CREATE SET cv += {
    name: $cv.name,
    description: $cv.description,
    aliases: $cv.aliases,
    extensions: $cv_extensions,
    mappings: $cv_mappings
}
MERGE (cv) -[:HAS_CONSTRAINT]-> (constr:Constraint:DefiningAlleleConstraint { id: $constraint_id })
ON CREATE SET cv += {
    relations: $constr.relations
}
MERGE (allele:Variation:MolecularVariation:Allele { id: $allele.id })
ON CREATE SET allele += {
    name: $allele.name,
    digest: $allele.digest,
    expression_hgvs_g: $allele.expression_hgvs_g,
    expression_hgvs_c: $allele.expression_hgvs_c,
    expression_hgvs_p: $allele.expression_hgvs_p
}
MERGE (constr) -[:HAS_DEFINING_ALLELE]-> (allele)
MERGE (sl:Location:SequenceLocation { id: $allele.location.id })
ON CREATE SET sl += {
    digest: $allele.location.digest,
    start: $allele.location.start,
    end: $allele.location.end,
    refget_accession: $allele.location.sequenceReference.refgetAccession,
    sequence: $allele.location.sequence
}
MERGE (allele) -[:HAS_LOCATION]-> (sl)

// handle different kinds of state objects
FOREACH (_ IN CASE WHEN $allele.state.type = 'LiteralSequenceExpression' THEN [1] ELSE [] END |
    MERGE (lse:SequenceExpression:LiteralSequenceExpression { sequence: $allele.state.sequence })
    MERGE (allele)-[:HAS_STATE]->(lse)
)
FOREACH (_ IN CASE WHEN $allele.state.type = 'ReferenceLengthExpression' THEN [1] ELSE [] END |
    MERGE (rle:SequenceExpression:ReferenceLengthExpression {
        length: $allele.state.length,
        repeat_subunit_length: $allele.state.repeatSubunitLength,
        sequence: $allele.state.sequence
    })
    MERGE (allele)-[:HAS_STATE]->(rle)
)

WITH cv
    UNWIND $members as m
    MERGE (member_allele:Variation:MolecularVariation:Allele { id: m.id })
    ON CREATE SET member_allele += {
        name: m.name,
        digest: m.digest,
        expression_hgvs_g: m.expression_hgvs_g,
        expression_hgvs_c: m.expression_hgvs_c,
        expression_hgvs_p: m.expression_hgvs_p
    }
    MERGE (cv) -[:HAS_MEMBER]-> (member_allele)
    MERGE (member_sl:Location:SequenceLocation { id: m.location.id })
    ON CREATE SET member_sl += {
        digest: m.location.digest,
        start: m.location.start,
        end:  m.location.end,
        refget_accession: m.location.sequenceReference.refgetAccession,
        sequence: m.location.sequence
    }
    MERGE (member_allele) -[:HAS_LOCATION] -> (member_sl)

    // handle different kinds of state objects
    FOREACH (_ IN CASE WHEN m.state.type = 'LiteralSequenceExpression' THEN [1] ELSE [] END |
        MERGE (member_lse:SequenceExpression:LiteralSequenceExpression { sequence: m.state.sequence })
        MERGE (member_allele)-[:HAS_STATE]->(member_lse)
    )
    FOREACH (_ IN CASE WHEN m.state.type = 'ReferenceLengthExpression' THEN [1] ELSE [] END |
        MERGE (member_rle:SequenceExpression:ReferenceLengthExpression {
            length: m.state.length,
            repeat_subunit_length: m.state.repeatSubunitLength,
            sequence: m.state.sequence
        })
        MERGE (member_allele)-[:HAS_STATE]->(member_rle)
    )
