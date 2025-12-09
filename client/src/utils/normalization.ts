/**
 *
 * Contains utility functions for normalizing domain-level data structures
 * into standardized MetaKB representations.
 *
 * Functions in this module sit at the *domain normalization* layer —
 * transforming data **within** the MetaKB schema (e.g., converting
 * `MappableConcept.strength` objects into standard evidence levels).
 *
 * This is distinct from *UI-level normalization*, such as the transformation
 * of backend `Statement` data into table rows, which occurs in
 * `results.ts`.
 *
 * Related modules:
 *  - `models/codings.ts` — defines the enums and mappings used for evidence-level resolution.
 *  - `models/domains.ts` — provides the TypeScript definitions for model entities like `MappableConcept`.
 *  - `results.ts` — handles normalization at the UI/data presentation layer.
 */

import { EvidenceLevel, EvidenceCodeMapping, TermToEvidenceLevel } from '../models/codings'
import { MappableConcept } from '../models/domain'

/**
 * Normalizes the evidence level from a given `MappableConcept` representing
 * evidence strength.
 *
 * Attempts to interpret the concept’s `primaryCoding.code` or any mapped codes
 * and resolve them to a standardized evidence level (`A`–`E`), according to
 * the rules defined in `models/codings.ts`.
 *
 * Normalization strategy:
 *  1. If the primary code is already a valid evidence level (`A`–`E`),
 *     or matches `"Level A"` / `"Level B"`, return it directly.
 *  2. Otherwise, attempt to match the `name` field to known evidence terms
 *     (e.g., `"preclinical evidence"` → `"D"`).
 *  3. If not found, iterate through the concept’s `mappings` array and
 *     search for mappings with `relation: "exactMatch"`. If the mapped code
 *     (e.g., `"e000009"`) corresponds to a known external identifier, use
 *     the associated evidence level.
 *  4. As a final fallback, perform a substring match on known terms within
 *     the name field.
 *
 * @param strength - A `MappableConcept` object representing the evidence strength.
 * @returns A single-character evidence level (`"A"`, `"B"`, `"C"`, `"D"`, `"E"`),
 *          or an empty string if no mapping is found.
 */
export function normalizeEvidenceLevelFromStrength(strength?: MappableConcept | null): string {
  if (!strength) {
    return 'NA'
  }
  const codeFromPrimary = strength.primaryCoding?.code?.trim()

  // If code is already in "A", "B", "C", or "Level A" type format, return the letter code
  if (codeFromPrimary) {
    const stripped = codeFromPrimary.replace(/^Level\s*/i, '').toUpperCase()
    if (Object.values(EvidenceLevel).includes(stripped as EvidenceLevel)) {
      return stripped
    }
  }

  // If the strength name matches one of the terms we know the code for, use that
  const name = strength.name?.toLowerCase().trim()
  if (name && TermToEvidenceLevel[name]) {
    return TermToEvidenceLevel[name]
  }

  // Try getting the code from the VICC evidence code mapping
  if (strength.mappings) {
    for (const mapping of strength.mappings) {
      const relation = (mapping.relation ?? '').toLowerCase()
      const code = mapping.coding?.code?.trim().toLowerCase()
      if (relation === 'exactmatch' && code) {
        const codeKey = code as keyof typeof EvidenceCodeMapping
        const level = EvidenceCodeMapping[codeKey]
        if (level) return level
      }
    }
  }

  // If we still haven't found a code by this point, maybe we have something like "Preclinical evidence (in vitro)"
  // so we can try to match it with supported terms
  if (name) {
    for (const [term, level] of Object.entries(TermToEvidenceLevel)) {
      if (name.includes(term)) {
        return level
      }
    }
  }

  return ''
}
