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
        normalized_id: m.normalized_id,
        name: m.name,
        mappings: m.mappings,
        aliases: m.aliases,
        extensions: m.extensions
      }
MERGE (thg)-[:HAS_THERAPY]->(member_drug)
