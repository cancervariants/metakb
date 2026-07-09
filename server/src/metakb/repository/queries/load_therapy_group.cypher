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
        extensions: m.extensions,
        primary_coding: m.primary_coding
      }
MERGE (thg)-[:HAS_THERAPY]->(member_drug)
