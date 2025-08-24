MERGE (thg:Therapeutic:TherapyGroup {id: $therapy_group.id})
  ON CREATE SET
    thg +=
      {
        membership_operator: $therapy_group.membership_operator,
        extensions: $therapy_group.extensions
      }

WITH thg, $therapy_group AS tg
UNWIND tg.has_therapies AS m // TODO double check that this is right
MERGE (member_drug:Therapeutic:Drug {id: m.id})
  ON CREATE SET
    member_drug +=
      {
        normalized_id: m.normalized_id,
        name: m.name,
        mappings: m.mappings,
        aliases: m.aliases,
        extensions: m.extensions
      }
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
