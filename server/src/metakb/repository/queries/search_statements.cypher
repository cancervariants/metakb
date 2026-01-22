// ------ Process input args -----
// Expect all params to be lists (possibly empty), never null:
// $statement_ids, $variation_ids, $condition_ids, $gene_ids, $therapy_ids
MATCH (s:Statement)
WHERE $statement_ids = [] OR s.id IN $statement_ids

MATCH (s)-[:HAS_SUBJECT_VARIANT]->(cv:CategoricalVariant)
MATCH (s)-[:HAS_GENE_CONTEXT]->(g:Gene)
WHERE
  ($variation_ids = [] OR
    EXISTS {
      MATCH
        (cv)-[:HAS_CONSTRAINT]->
        (:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
        (a:Allele)
      WHERE a.id IN $variation_ids
    } OR
    EXISTS {
      MATCH (cv)-[:HAS_MEMBER]->(a:Allele)
      WHERE a.id IN $variation_ids
    }) AND
  ($condition_ids = [] OR
    EXISTS {
      MATCH (s)-[:HAS_TUMOR_TYPE]->(cond:Condition)
      WHERE cond.normalized_id IN $condition_ids
    } OR EXISTS {
      MATCH
        (s)-[:HAS_TUMOR_TYPE]->
        (:ConditionSet)-[:HAS_CONDITION*0..]->
        (cond:Condition)
      WHERE cond.normalized_id IN $condition_ids
    }) AND
  ($gene_ids = [] OR g.normalized_id IN $gene_ids) AND
  ($therapy_ids = [] OR
    EXISTS {
      MATCH (s)-[:HAS_THERAPEUTIC]->(t:Therapeutic)
      WHERE t.normalized_id IN $therapy_ids
    } OR
    EXISTS {
      MATCH
        (s)-[:HAS_THERAPEUTIC]->
        (:TherapyGroup)-[:HAS_THERAPY]->
        (d:Drug)
      WHERE d.normalized_id IN $therapy_ids
    })

//  ----- get basic statement info  -----
MATCH (s)-[:HAS_STRENGTH]->(str:Strength)
MATCH (s)-[:IS_SPECIFIED_BY]->(method:Method)
MATCH (method)-[:IS_REPORTED_IN]->(method_doc:Document)
OPTIONAL MATCH (s)-[:HAS_CLASSIFICATION]->(classification:Classification)

// condition set
OPTIONAL MATCH (s)-[:HAS_TUMOR_TYPE]->(condition_set:ConditionSet)
OPTIONAL MATCH cond_path = (condition_set)-[:HAS_CONDITION*0..]->(cond_member)
WHERE cond_member:Condition OR cond_member:ConditionSet

// condition
OPTIONAL MATCH (s)-[:HAS_TUMOR_TYPE]->(c:Condition)
WHERE condition_set IS NULL
WITH
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  g,
  condition_set,
  c AS condition,
  collect(DISTINCT cond_member) AS condition_nodes,
  collect(DISTINCT relationships(cond_path)) AS condition_rels

// Get therapeutic components
OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(tg:TherapyGroup)
OPTIONAL MATCH (tg)-[:HAS_THERAPY]->(tm:Drug)
WITH
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  condition_set,
  condition,
  condition_nodes,
  condition_rels,
  g,
  tg,
  collect(DISTINCT tm) AS tmembers

OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(td:Drug)
WITH
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  condition_set,
  condition,
  condition_nodes,
  condition_rels,
  g,
  CASE
    WHEN tg IS NOT NULL THEN {therapy_group: tg, members: tmembers}
  END AS therapy_group,
  CASE
    WHEN tg IS NULL THEN td
  END AS drug

// ----- Get catvar components -----
MATCH (cv)-[:HAS_CONSTRAINT]->(constraint)
// Either get constraint for Feature Context...
OPTIONAL MATCH
  (constraint:FeatureContextConstraint)-[:HAS_FEATURE_CONTEXT]->
  (feature_context:Gene)
// ...or for Defining Allele
OPTIONAL MATCH
  (constraint:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
  (defining_allele:Allele)
OPTIONAL MATCH
  (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
OPTIONAL MATCH
  (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)
OPTIONAL MATCH
  (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
OPTIONAL MATCH
  (defining_allele_sl)-[:HAS_SEQUENCE_REFERENCE]->
  (defining_allele_sr:SequenceReference)
OPTIONAL MATCH
  (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)
// Then get members
CALL {
  WITH cv
  OPTIONAL MATCH (cv)-[:HAS_MEMBER]->(m:Allele)
  OPTIONAL MATCH (m)-[:HAS_LOCATION]->(sl:SequenceLocation)
  OPTIONAL MATCH (sl)-[:HAS_SEQUENCE_REFERENCE]->(sr:SequenceReference)
  OPTIONAL MATCH (m)-[:HAS_STATE]->(se:SequenceExpression)
  WITH m, sl, sr, se
  WHERE m IS NOT NULL AND sl IS NOT NULL AND sr IS NOT NULL AND se IS NOT NULL
  RETURN
    collect(
      DISTINCT
      {allele: m, location: sl {.*, has_sequence_reference: sr}, state: se}
    ) AS members
}

// get documents
CALL {
  WITH s
  MATCH (s)-[:IS_REPORTED_IN]->(doc:Document)
  RETURN collect(DISTINCT doc) AS documents
}

// get evidence line IDs
CALL {
  WITH s
  OPTIONAL MATCH (s)-[:HAS_EVIDENCE_LINE]->(line:EvidenceLine)
  OPTIONAL MATCH (line)-[:HAS_EVIDENCE_ITEM]->(ei:Statement)
  WITH line, collect(DISTINCT ei.id) AS item_ids
  WITH
    collect(
      CASE
        WHEN line IS NULL THEN null
        ELSE line {.*, evidence_item_ids: item_ids}
      END
    ) AS tmp
  RETURN [x IN tmp WHERE x IS NOT NULL] AS evidence_lines
}

// ----- return everything -----
RETURN DISTINCT
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  constraint,
  defining_allele,
  defining_allele_sl {.*, has_sequence_reference: defining_allele_sr} AS defining_allele_sl,
  defining_allele_se,
  feature_context,
  members,
  condition_set,
  condition,
  condition_nodes,
  condition_rels,
  g,
  therapy_group,
  drug,
  documents,
  evidence_lines
ORDER BY s.id SKIP $start
LIMIT $limit;
