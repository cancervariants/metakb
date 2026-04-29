/**
 * Generate an external resource URL for a given CURIE-style object ID.
 *
 * Supports known gene identifier prefixes (e.g., ncbigene, ensembl, hgnc)
 * and returns the corresponding provider URL. Returns null if the prefix is
 * unsupported or the identifier cannot be parsed.
 */
export const generateUrlForId = (objectId: string): string | null => {
  const lui = objectId.split(':').pop()
  if (objectId.startsWith('ncbigene:')) {
    return lui ? `https://www.ncbi.nlm.nih.gov/gene/${lui}` : null
  }
  if (objectId.startsWith('ensembl:')) {
    return lui ? `https://www.ensembl.org/Homo_sapiens/Gene/Summary?db=core;g=${lui}` : null
  }
  if (objectId.startsWith('hgnc:')) {
    return lui ? `https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:${lui}` : null
  }
  if (objectId.startsWith('civic.gid:')) {
    return lui ? `https://www.civicdb.org/features/${lui}` : null
  }
  if (objectId.startsWith('moa.gene:')) {
    return lui ? `https://moalmanac.org/search?s=Gene%3A%22${lui}%22%5Battribute%5D` : null
  }
  if (objectId.startsWith('clingen.allele:')) {
    return lui
      ? `https://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_canonicalid?canonicalid=${lui}`
      : null
  }
  if (objectId.startsWith('clinvar.variation:')) {
    return lui ? `https://www.ncbi.nlm.nih.gov/clinvar/variation/${lui}` : null
  }
  if (objectId.startsWith('civic.mpid:')) {
    return lui ? `https://www.civicdb.org/molecular-profiles/${lui}` : null
  }
  if (objectId.startsWith('dbsnp:')) {
    return lui ? `https://www.ncbi.nlm.nih.gov/snp/${lui}` : null
  }
  return null
}
