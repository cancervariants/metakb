// Expect all params to be lists (possibly empty), never null:
// $statement_ids, $variation_ids, $condition_ids, $gene_ids, $therapy_ids
MATCH (s:Statement)
WHERE $statement_ids = [] OR s.id IN $statement_ids

MATCH (s)-[:HAS_SUBJECT_VARIANT]->(cv:CategoricalVariant)
MATCH
  (s)-[:HAS_TUMOR_TYPE]->(c:Condition)-[:NORMALIZES_TO]->(nc:NormalizedDisease)
MATCH (s)-[:HAS_GENE_CONTEXT]->(g:Gene)-[:NORMALIZES_TO]->(ng:NormalizedGene)
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
  ($condition_ids = [] OR nc.id IN $condition_ids) AND
  ($gene_ids = [] OR ng.id IN $gene_ids) AND
  ($therapy_ids = [] OR
    EXISTS {
      MATCH
        (s)-[:HAS_THERAPEUTIC]->
        (:Therapeutic)-[:NORMALIZES_TO]->
        (nd:NormalizedDrug)
      WHERE nd.id IN $therapy_ids
    } OR
    EXISTS {
      MATCH
        (s)-[:HAS_THERAPEUTIC]->
        (:TherapyGroup)-[:HAS_SUBSTITUTE|HAS_COMPONENT]->
        (:Drug)-[:NORMALIZES_TO]->
        (nd:NormalizedDrug)
      WHERE nd.id IN $therapy_ids
    })

WITH
  s,
  cv,
  c {.*, normalized_disease: nc} AS disease_obj,
  g {.*, normalized_gene: ng} AS gene_obj

// get basic statement info
MATCH (s)-[:HAS_STRENGTH]->(str:Strength)
MATCH (s)-[:IS_SPECIFIED_BY]->(method:Method)
MATCH (method)-[:IS_REPORTED_IN]->(method_doc:Document)
OPTIONAL MATCH (s)-[:HAS_CLASSIFICATION]->(classification:Classification)

// Get therapeutic components
OPTIONAL MATCH (s)-[:HAS_THERAPEUTIC]->(tg:TherapyGroup)
OPTIONAL MATCH
  (tg)-[:HAS_SUBSTITUTE|HAS_COMPONENT]->
  (tm:Drug)-[:NORMALIZES_TO]->
  (tm_nd:NormalizedDrug)
WITH
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  disease_obj,
  gene_obj,
  tg,
  collect(DISTINCT tm {.*, normalized_drug: tm_nd}) AS tmembers

OPTIONAL MATCH
  (s)-[:HAS_THERAPEUTIC]->(td:Drug)-[:NORMALIZES_TO]->(td_nd:NormalizedDrug)
WITH
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  disease_obj,
  gene_obj,
  CASE
    WHEN tg IS NOT NULL THEN {therapy_group: tg, members: tmembers}
  END AS therapy_group,
  CASE
    WHEN tg IS NULL THEN td {.*, normalized_drug: td_nd}
  END AS drug

// Get catvar components
MATCH
  (cv)-[:HAS_CONSTRAINT]->
  (constraint:DefiningAlleleConstraint)-[:HAS_DEFINING_ALLELE]->
  (defining_allele:Allele)
MATCH (defining_allele)-[:HAS_LOCATION]->(defining_allele_sl:SequenceLocation)
MATCH (defining_allele)-[:HAS_STATE]->(defining_allele_se:SequenceExpression)
CALL (cv) {
  WITH cv
  OPTIONAL MATCH (cv)-[:HAS_MEMBER]->(m:Allele)
  OPTIONAL MATCH (m)-[:HAS_LOCATION]->(sl:SequenceLocation)
  OPTIONAL MATCH (m)-[:HAS_STATE]->(se:SequenceExpression)
  WITH m, sl, se
  WHERE m IS NOT NULL AND sl IS NOT NULL AND se IS NOT NULL
  RETURN collect(DISTINCT {allele: m, location: sl, state: se}) AS members
}

// get documents
CALL (s) {
  MATCH (s)-[:IS_REPORTED_IN]->(doc:Document)
  RETURN collect(DISTINCT doc) AS documents
}

// get evidence line IDs
CALL (s) {
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

RETURN DISTINCT
  s,
  str,
  method,
  method_doc,
  classification,
  cv,
  constraint,
  defining_allele,
  defining_allele_sl,
  defining_allele_se,
  members,
  disease_obj,
  gene_obj,
  therapy_group,
  drug,
  documents,
  evidence_lines
ORDER BY s.id SKIP $start
LIMIT $limit;
