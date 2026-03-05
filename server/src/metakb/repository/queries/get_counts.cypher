// 'label' property should be the same as the key in `metakb.repository.base.RepositoryStats` model
// to enable clean unpacking of result into response object
// 'label' property should be the same as the key in `metakb.repository.base.RepositoryStats` model
// to enable clean unpacking of result into response object
MATCH (g:Gene)
WHERE g.id STARTS WITH "metakb"
RETURN {label: 'num_genes', count: count(g)} AS info
  UNION ALL
MATCH (d:Drug)
WHERE d.id STARTS WITH "metakb"
RETURN {label: 'num_drugs', count: count(d)} AS info
  UNION ALL
MATCH (di:Disease)
WHERE di.id STARTS WITH "metakb"
RETURN {label: 'num_diseases', count: count(di)} AS info
  UNION ALL
MATCH (cv:CategoricalVariant)
WHERE cv.id STARTS WITH "metakb"
RETURN {label: 'num_variations', count: count(cv)} AS info
  UNION ALL
MATCH (s:Statement)
WHERE s.id STARTS WITH "civic" OR s.id STARTS WITH "moa"
RETURN {label: 'num_source_statements', count: count(s)} AS info
  UNION ALL
MATCH (d:Document)
RETURN {label: 'num_documents', count: count(d)} AS info
  UNION ALL
MATCH (metakb_s:Statement)
WHERE metakb_s.id STARTS WITH "metakb"
RETURN {label: 'num_metakb_assertions', count: count(metakb_s)} AS info
