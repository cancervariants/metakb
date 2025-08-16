MERGE (d:Document {id: $doc.id})
  ON CREATE SET
    d +=
      {
        title: $doc.title,
        urls: $doc.urls,
        pmid: $doc.pmid,
        name: $doc.name,
        doi: $doc.doi,
        source_type: $doc.source_type
      }
