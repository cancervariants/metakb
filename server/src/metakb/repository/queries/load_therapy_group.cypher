MERGE (thg:Therapeutic:TherapyGroup {id: $therapy_group.id})
  ON CREATE SET
    thg +=
      {
        membership_operator: $therapy_group.membership_operator,
        extensions: $therapy_group.extensions
      }

WITH thg, $therapy_group AS tg
UNWIND tg.members AS m
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

// use subqueries to dynamically set relationship type based on membership operator
CALL {
  WITH thg, member_drug, tg
  WHERE tg.membership_operator = 'OR'
  MERGE (thg)-[:HAS_SUBSTITUTE]->(member_drug)
  RETURN 0
}
CALL {
  WITH thg, member_drug, tg
  WHERE tg.membership_operator <> 'OR'
  MERGE (thg)-[:HAS_COMPONENT]->(member_drug)
  RETURN 0
}
