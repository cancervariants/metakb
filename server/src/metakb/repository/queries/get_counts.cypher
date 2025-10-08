// 'label' property should be the same as the key in `metakb.repository.base.RepositoryStats` model
// to enable clean unpacking of result into response object
MATCH (g:Gene)
RETURN {label: 'num_genes', count: count(g)} AS info
  UNION ALL
MATCH (th:Therapeutic)
RETURN {label: 'num_therapeutics', count: count(th)} AS info
  UNION ALL
MATCH (c:Condition)
RETURN {label: 'num_conditions', count: count(c)} AS info
  UNION ALL
MATCH (cv:CategoricalVariant)
RETURN {label: 'num_variations', count: count(cv)} AS info
  UNION ALL
MATCH (s:Statement)
RETURN {label: 'num_statements', count: count(s)} AS info
  UNION ALL
MATCH (d:Document)
RETURN {label: 'num_documents', count: count(d)} AS info
