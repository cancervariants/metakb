MERGE (thg:Therapeutic:TherapyGroup {id: $therapy_group.id})
  ON CREATE SET
    thg +=
      {
        membership_operator: $therapy_group.membership_operator,
        extensions: $therapy_group.extensions
      }

WITH thg, $therapy_group AS tg
UNWIND tg.has_therapies AS m
MERGE (member_drug:Therapeutic:Drug {id: m.id})
  ON CREATE SET
    member_drug +=
      {
        name: m.name,
        mappings: m.mappings,
        aliases: m.aliases,
        extensions: m.extensions
      }
MERGE (normalized_member_drug:NormalizedDrug {id: m.normalized_drug.id})
  ON CREATE SET
    normalized_member_drug +=
      {
        name: m.normalized_drug.name,
        mappings: m.normalized_drug.mappings,
        extensions: m.normalized_drug.extensions
      }
MERGE (member_drug)-[:NORMALIZES_TO]->(normalized_member_drug)
FOREACH (_ IN
CASE
  WHEN tg.membership_operator = 'OR' THEN [1]
  ELSE []
END |
  MERGE (thg)-[:HAS_SUBSTITUTE]->(member_drug)
)
FOREACH (_ IN
CASE
  WHEN tg.membership_operator <> 'OR' THEN [1]
  ELSE []
END |
  MERGE (thg)-[:HAS_COMPONENT]->(member_drug)
)
