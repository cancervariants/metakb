MATCH (s:Statement)
MATCH (s)-[:HAS_STRENGTH]->(str:Strength)
MATCH (s)-[:IS_SPECIFIED_BY]->(mth:Method)-[:IS_REPORTED_IN]->(mthdoc:Document)
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
  ($condition_id IS NULL OR c.normalizer_id = $condition_id) AND
  ($gene_id IS NULL OR g.normalizer_id = $gene_id) AND
  ($therapy_id IS NULL OR
    EXISTS {
      MATCH (s)-[:HAS_THERAPEUTIC]->(:Therapy {normalizer_id: $therapy_id})
    } OR
    EXISTS {
      MATCH
        (s)-[:HAS_THERAPEUTIC]->
        (:TherapyGroup)-[:HAS_SUBSTITUTES|HAS_COMPONENTS]->
        (:Therapy {normalizer_id: $therapy_id})
    })

WITH s, str, mth, mthdoc, cv, c, g, $therapy_id AS therapy_id

// --- Therapy resolution (direct or via group) ---
OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(th:Therapy)
WHERE therapy_id IS NOT NULL AND th.normalizer_id = therapy_id

OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(tg0:TherapyGroup)
WHERE therapy_id IS NOT NULL
OPTIONAL MATCH (tg0)-[:HAS_SUBSTITUTES|HAS_COMPONENTS]->(m:Therapy)
WHERE therapy_id IS NOT NULL

WITH
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th,
  therapy_id,
  tg0,
  collect(DISTINCT m) AS members,
  collect(DISTINCT m.normalizer_id) AS member_ids
WITH
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th,
  CASE
    WHEN
      therapy_id IS NOT NULL AND tg0 IS NOT NULL AND therapy_id IN member_ids
      THEN tg0
  END AS tg_candidate,
  CASE
    WHEN
      therapy_id IS NOT NULL AND tg0 IS NOT NULL AND therapy_id IN member_ids
      THEN members
    ELSE []
  END AS therapies_candidate
WITH
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th,
  head([x IN collect(tg_candidate) WHERE x IS NOT NULL]) AS tg,
  head([x IN collect(therapies_candidate) WHERE size(x) > 0]) AS therapies

// --- CategoricalVariant details (defining allele + members as objects) ---
MATCH
  (cv)-[:HAS_CONSTRAINT]->
  (:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
  (defining_allele:Allele)
MATCH (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
MATCH (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)

OPTIONAL MATCH (cv)-[:HAS_MEMBER]->(member_allele:Allele)
OPTIONAL MATCH
  (member_allele)-[:HAS_LOCATION]->(member_allele_sl:SequenceLocation)
OPTIONAL MATCH
  (member_allele)-[:HAS_STATE]->(member_allele_se:SequenceExpression)

WITH
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th,
  tg,
  therapies,
  defining_allele,
  defining_allele_sl,
  defining_allele_se,
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

WITH
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th,
  tg,
  therapies,
  defining_allele,
  defining_allele_sl,
  defining_allele_se,
  [m IN members_raw WHERE m IS NOT NULL] AS members

RETURN DISTINCT
  s,
  str,
  mth,
  mthdoc,
  cv,
  c,
  g,
  th, // direct therapy, if matched
  tg,
  therapies, // group and ALL its member therapies (array), if matched
  defining_allele,
  defining_allele_sl,
  defining_allele_se,
  members // array of {allele, location, state} for cv members
ORDER BY s.id;
