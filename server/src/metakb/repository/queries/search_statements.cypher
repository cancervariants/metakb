MATCH (s:Statement)
MATCH (s)-[:HAS_STRENGTH]->(str:Strength)
OPTIONAL MATCH (s)-[:HAS_CLASSIFICATION]->(classification:Classification)
MATCH (s)-[:HAS_SUBJECT_VARIANT]->(cv:CategoricalVariant)
MATCH (s)-[:HAS_TUMOR_TYPE]->(c:Condition)
MATCH (s)-[:HAS_GENE_CONTEXT]->(g:Gene)
WHERE
  ($variation_id IS NULL OR
    EXISTS {
      MATCH
        (cv)-[:HAS_CONSTRAINT]->
        (:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
        (:Allele {id: $variation_id})
    } OR
    EXISTS {
      MATCH (cv)-[:HAS_MEMBER]->(:Allele {id: $variation_id})
    }) AND
  ($condition_id IS NULL OR c.normalized_id = $condition_id) AND
  ($gene_id IS NULL OR g.normalized_id = $gene_id) AND
  ($therapy_id IS NULL OR
    EXISTS {
      MATCH (s)-[:HAS_THERAPEUTIC]->(:Therapy {normalized_id: $therapy_id})
    } OR
    EXISTS {
      MATCH
        (s)-[:HAS_THERAPEUTIC]->
        (:TherapyGroup)-[:HAS_SUBSTITUTES|HAS_COMPONENTS]->
        (:Therapy {normalized_id: $therapy_id})
    })

// --- Therapy (direct or via group) ---
OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(th:Therapy)
WHERE $therapy_id IS NOT NULL AND th.normalized_id = $therapy_id
OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(tg:TherapyGroup)
OPTIONAL MATCH (tg)-[:HAS_SUBSTITUTES|HAS_COMPONENTS]->(tm:Therapy)
WITH *, collect(DISTINCT tm) AS all_tm
WITH
  *,
  CASE
    WHEN
      $therapy_id IS NOT NULL AND
      tg IS NOT NULL AND
      any(t IN all_tm WHERE t.normalized_id = $therapy_id)
      THEN tg
  END AS tg_hit,
  CASE
    WHEN
      $therapy_id IS NOT NULL AND
      tg IS NOT NULL AND
      any(t IN all_tm WHERE t.normalized_id = $therapy_id)
      THEN all_tm
    ELSE []
  END AS therapies

// get catvar components
MATCH
  (cv)-[:HAS_CONSTRAINT]->
  (constraint:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
  (defining_allele:Allele)
MATCH (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
MATCH (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)
OPTIONAL MATCH (cv)-[:HAS_MEMBER]->(member_allele:Allele)
OPTIONAL MATCH
  (member_allele)-[:HAS_LOCATION]->(member_allele_sl:SequenceLocation)
OPTIONAL MATCH
  (member_allele)-[:HAS_STATE]->(member_allele_se:SequenceExpression)
WITH
  *,
  collect(
    DISTINCT
    CASE
      WHEN
        member_allele IS NOT NULL AND
        member_allele_sl IS NOT NULL AND
        member_allele_se IS NOT NULL
        THEN
          {
            allele: member_allele,
            location: member_allele_sl,
            state: member_allele_se
          }
    END) AS members_raw

// get statement documents
CALL (s) {
  MATCH
    (s)-[:IS_SPECIFIED_BY]->(method:Method)-[:IS_REPORTED_IN]->(doc:Document)
  RETURN collect(DISTINCT doc) AS documents
}

RETURN DISTINCT
  s,
  str,
  cv,
  constraint,
  defining_allele,
  defining_allele_sl,
  defining_allele_se,
  c,
  g,
  th,
  tg_hit AS tg,
  therapies,
  [m IN members_raw WHERE m IS NOT NULL] AS members,
  method,
  documents
ORDER BY s.id;
