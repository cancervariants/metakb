/**
 * Utilities for building filters and counts from result data.
 * - `buildCountMap` produces frequency maps of property values
 *
 * These are pure helpers for aggregating result data to drive filter options
 * and counts for the sidebar UI.
 */

import { AgeOfOnsetSelection } from '../components/SearchFilters/AgeOfOnsetFilter'
import { AssertionResult } from './results'

/**
 * Builds a frequency map of values from a list of results.
 *
 * @typeParam T - The type of each row in the results
 * @typeParam K - The key in `T` to count by
 *
 * @param results - Array of result objects
 * @param key - The property key in `T` to count occurrences of
 * @returns A record mapping each distinct value (stringified) to its count
 */
export function buildCountMap<T, K extends keyof T>(results: T[], key: K): Record<string, number> {
  return results.reduce((acc: Record<string, number>, item) => {
    const val = item[key]

    if (val != null) {
      if (Array.isArray(val)) {
        val.forEach((v) => {
          if (v != null) {
            acc[String(v)] = (acc[String(v)] || 0) + 1
          }
        })
      } else {
        acc[String(val)] = (acc[String(val)] || 0) + 1
      }
    }

    return acc
  }, {})
}

/**
 * Filters an array of `AssertionResult` rows against the currently
 * selected filter criteria.
 *
 * Each filter category is optional. If no values are selected in a category,
 * all items pass that category. Otherwise, an item must match at least one
 * selected value in each active category.
 *
 * Age-of-onset filtering supports both selected HPO concept IDs and results
 * where no tracked age-of-onset term is specified.
 *
 * @param items - Array of `AssertionResult` rows to filter.
 * @param selected - Object containing the active filter selections.
 * @returns Rows that satisfy all active filters.
 */
export const applyFilters = (
  items: AssertionResult[],
  selected: {
    variants: string[]
    diseases: string[]
    agesOfOnset: AgeOfOnsetSelection
    therapies: string[]
    evidenceLevels: string[]
    starRatings: string[]
    significance: string[]
    sources: string[]
  },
): AssertionResult[] => {
  return items.filter((r) => {
    const variantMatch =
      selected.variants.length === 0 || selected.variants.includes(r.variant_name)

    const diseaseMatch =
      selected.diseases.length === 0 || r.disease.some((d: string) => selected.diseases.includes(d))

    const ageOfOnsetFilterActive =
      selected.agesOfOnset.conceptIds.length > 0 || selected.agesOfOnset.includeNotSpecified

    const ageOfOnsetMatch =
      !ageOfOnsetFilterActive ||
      (r.ageOfOnset
        ? selected.agesOfOnset.conceptIds.includes(r.ageOfOnset.conceptId)
        : selected.agesOfOnset.includeNotSpecified)

    const therapyMatch =
      selected.therapies.length === 0 ||
      r.therapy.therapyNames.some((t: string) => selected.therapies.includes(t))

    const levelMatch =
      selected.evidenceLevels.length === 0 || selected.evidenceLevels.includes(r.evidence_level)

    const starRatingMatch =
      selected.starRatings.length === 0 ||
      selected.starRatings.includes(String(r.star_rating.starRating))

    const significanceMatch =
      selected.significance.length === 0 || selected.significance.includes(r.significance)

    const sourceMatch =
      selected.sources.length === 0 || selected.sources.some((s) => r.sources.includes(s))

    return (
      variantMatch &&
      diseaseMatch &&
      ageOfOnsetMatch &&
      therapyMatch &&
      levelMatch &&
      starRatingMatch &&
      significanceMatch &&
      sourceMatch
    )
  })
}

/**
 * Builds a list of filter option values for a given property key in
 * `NormalizedResult` rows, sorted by frequency of occurrence.
 *
 * Uses `buildCountMap` to count how often each unique value appears,
 * then sorts descending by count. Useful for generating dropdown or
 * checkbox filter options ordered by relevance.
 *
 * @param results - Array of `NormalizedResult` rows.
 * @param key - The property key in `NormalizedResult` to aggregate on
 *              (e.g. "variant_name", "disease", "therapy").
 *
 * @returns Array of unique string values for the given key,
 *          sorted from most frequent to least frequent.
 */
export const buildFilterOptions = (
  results: AssertionResult[],
  key: keyof AssertionResult,
): string[] => {
  const counts = buildCountMap(results, key)

  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1]) // sort by count desc
    .map(([value]) => value)
}
