MATCH (g:Gene {id: $gene_id})
MATCH (g)<-[:HAS_GENE_CONTEXT]-(:Statement)-[*]->(cg:Gene)
RETURN g AS gene, collect(DISTINCT cg) AS child_genes
