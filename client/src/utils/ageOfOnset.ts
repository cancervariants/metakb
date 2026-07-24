/**
 * Utilities for working for age of onset phenotype terms
 */

export type PhenotypeConceptId = string

export type AgeOfOnset = {
  name: string
  description: string
  conceptId: PhenotypeConceptId
  parentConceptId: string | null
}

export const AGE_OF_ONSET_TERMS: Record<PhenotypeConceptId, AgeOfOnset> = {
  'HP:0003623': {
    name: 'Neonatal onset',
    description: 'Onset of signs or symptoms of disease within the first 28 days of life.',
    conceptId: 'HP:0003623',
    parentConceptId: null,
  },
  'HP:0410280': {
    name: 'Pediatric onset',
    description:
      'Onset of disease manifestations before adulthood, defined here as before the age of 16 years, but excluding neonatal or congenital onset.',
    conceptId: 'HP:0410280',
    parentConceptId: null,
  },
  'HP:0011463': {
    name: 'Childhood onset',
    description: 'Onset of disease at the age of between 1 and 5 years',
    conceptId: 'HP:0011463',
    parentConceptId: 'HP:0410280', // pediatric onset
  },
  'HP:0003593': {
    name: 'Infantile onset',
    description: 'Onset of signs or symptoms of disease between 28 days to one year of life.',
    conceptId: 'HP:0003593',
    parentConceptId: 'HP:0410280', // pediatric onset
  },
  'HP:0003621': {
    name: 'Juvenile onset',
    description: 'Onset of signs or symptoms of disease between the age of 5 and 15 years.',
    conceptId: 'HP:0003621',
    parentConceptId: 'HP:0410280', // pediatric onset
  },
  'HP:0011462': {
    name: 'Young adult onset',
    description: 'Onset of disease at the age of between 16 and 40 years.',
    conceptId: 'HP:0011462',
    parentConceptId: null,
  },
  'HP:0025708': {
    name: 'Early young adult onset',
    description:
      'This term includes the full 16th year of age up to the completed 18th year of age (i.e., less than the 19th birthday).',
    conceptId: 'HP:0025708',
    parentConceptId: 'HP:0011462', // Young adult onset
  },
}

/**
 * Return the given age-of-onset term and all descendant term IDs.
 *
 * Used to expand selections so that choosing a broader age-of-onset category
 * also includes all more specific descendant categories.
 */
export const getTermAndChildrenIds = (termId: string): string[] => {
  const childIds = Object.values(AGE_OF_ONSET_TERMS)
    .filter((term) => term.parentConceptId === termId)
    .flatMap((child) => getTermAndChildrenIds(child.conceptId))
  return [termId, ...childIds]
}
