/**
 * Utilities for building filters and counts from result data.
 * - `buildCountMap` produces frequency maps of property values
 *
 * These are pure helpers for aggregating result data to drive filter options
 * and counts for the sidebar UI.
 */

import { NormalizedResult } from './results'

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
 * Filters an array of `NormalizedResult` rows against the currently
 * selected filter criteria.
 *
 * Each filter category (variants, diseases, therapies, evidenceLevels,
 * significance, sources) is optional — if no values are selected in a
 * category, all items pass that category. Otherwise, an item must match
 * at least one of the selected values for each active category.
 *
 * @param items - Array of `NormalizedResult` rows to filter.
 * @param selected - Object containing the active filter selections.
 *   - `variants`: Variant names to match.
 *   - `diseases`: Disease names to match (checks against all diseases in a row - in case of a ConditionSet).
 *   - `therapies`: Therapies to match.
 *   - `evidenceLevels`: Evidence levels to match.
 *   - `significance`: Clinical significance values to match.
 *   - `sources`: Evidence sources to match (checks if row contains any selected source).
 *
 * @returns Array of `NormalizedResult` rows that satisfy all active filters.
 */
export const applyFilters = (
  items: NormalizedResult[],
  selected: {
    variants: string[]
    diseases: string[]
    therapies: string[]
    evidenceLevels: string[]
    significance: string[]
    sources: string[]
  },
): NormalizedResult[] => {
  return items.filter((r) => {
    const variantMatch =
      selected.variants.length === 0 || selected.variants.includes(r.variant_name)
    const diseaseMatch =
      selected.diseases.length === 0 || r.disease.some((d: string) => selected.diseases.includes(d))

    const therapyMatch = selected.therapies.length === 0 || selected.therapies.includes(r.therapy)
    const levelMatch =
      selected.evidenceLevels.length === 0 || selected.evidenceLevels.includes(r.evidence_level)
    const significanceMatch =
      selected.significance.length === 0 || selected.significance.includes(r.significance)

    const sourceMatch =
      selected.sources.length === 0 || selected.sources.some((s) => r.sources.includes(s))

    return (
      variantMatch && diseaseMatch && therapyMatch && levelMatch && significanceMatch && sourceMatch
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
  results: NormalizedResult[],
  key: keyof NormalizedResult,
): string[] => {
  const counts = buildCountMap(results, key)

  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1]) // sort by count desc
    .map(([value]) => value)
}
