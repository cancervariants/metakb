/**
 * Utilities for transforming raw `Statement` data into `NormalizedResult` rows
 * used by the results table UI. Includes:
 * - Normalization logic (`normalizeResults`) that aggregates grouped evidence
 * - Evidence level ordering for sorting
 * - Mapping predicate strings into human-readable significance labels
 *
 * These functions sit at the boundary between API data (Statements) and
 * frontend UI data (NormalizedResult).
 * Possible TODO: we might be able to reduce or eliminate the need for constructing normalized result
 * if we change how the backend provides the response
 *
 *
 */

import { Statement } from '../models/domain'
import { getDiseaseFromProposition, getTherapyFromProposition } from './propositions'
import { getSources } from './sources'

export const TAB_LABELS: Record<'therapeutic' | 'diagnostic' | 'prognostic', string> = {
  therapeutic: 'Therapeutic',
  diagnostic: 'Diagnostic',
  prognostic: 'Prognostic',
}

/**
 * Represents a single normalized row of evidence results, aggregating evidence
 * from one or more `Statement` objects into a single table row.
 */
export interface NormalizedResult {
  /** Human-readable variant name (normalized for display) */
  variant_name: string
  /** Highest evidence level among grouped evidence */
  evidence_level: string
  /** Associated diseases, may include multiple names */
  disease: string[]
  /** Therapy or combination therapy (if applicable) */
  therapy: string
  /** Clinical significance string */
  significance: string
  /** All evidence statements grouped into this row */
  grouped_evidence: Statement[]
  /** Sources (databases) that contributed evidence to this row */
  sources: string[]
}

/**
 * Maps a backend predicate string into a human-readable clinical significance label.
 *
 * The API returns predicates such as `"predictsSensitivityTo"` or
 * `"associatedWithWorseOutcomeFor"`. This function translates those
 * into shorter, user-friendly labels for display in the results table.
 *
 * Known mappings:
 *  - "predictsSensitivityTo" → "Sensitivity"
 *  - "predictsResistanceTo" → "Resistance"
 *  - "isDiagnosticInclusionCriterionFor" → "Inclusion Criterion"
 *  - "isDiagnosticExclusionCriterionFor" → "Exclusion Criterion"
 *  - "associatedWithWorseOutcomeFor" → "Worse Outcome"
 *  - "associatedWithBetterOutcomeFor" → "Better Outcome"
 *
 * @param predicate - Predicate string value from a proposition.
 * @returns Human-readable significance label, or an empty string if not recognized.
 */
const formatSignificance = (predicate: string): string => {
  if (predicate === 'predictsSensitivityTo') {
    return 'Sensitivity'
  }
  if (predicate === 'predictsResistanceTo') {
    return 'Resistance'
  }
  if (predicate === 'isDiagnosticInclusionCriterionFor') {
    return 'Inclusion Criterion'
  }
  if (predicate === 'isDiagnosticExclusionCriterionFor') {
    return 'Exclusion Criterion'
  }
  if (predicate === 'associatedWithWorseOutcomeFor') {
    return 'Worse Outcome'
  }
  if (predicate === 'associatedWithBetterOutcomeFor') {
    return 'Better Outcome'
  }
  return ''
}

/**
 * Mapping of evidence level codes to numeric ranks used for sorting.
 * Lower numbers indicate stronger evidence.
 */
export const evidenceOrder: Record<string, number> = {
  A: 1,
  'Level A': 1,
  B: 3,
  C: 4,
  D: 5,
  E: 6,
  'N/A': 999,
}

/**
 * Normalizes raw evidence statements into `NormalizedResult` rows
 * suitable for display in the results table.
 *
 * Each entry in the input `data` represents a group of `Statement[]`
 * (evidence records) associated with a single variant/disease/therapy context.
 * This function:
 *  - Flattens grouped evidence into rows
 *  - Extracts display metadata (variant name, disease(s), therapy, significance)
 *  - Computes the "highest" evidence level using `evidenceOrder`
 *  - Collects all source databases referenced by the evidence
 *  - Preserves the full set of underlying `Statement`s in `grouped_evidence`
 *
 * @param data - A record mapping keys to arrays of `Statement` objects
 *               returned from the API.
 * @returns Array of `NormalizedResult` objects, one per evidence grouping.
 *          Returns an empty array if the input is empty or invalid.
 */
export const normalizeResults = (data: Record<string, Statement[]>): NormalizedResult[] => {
  if (!data || Object.keys(data).length === 0) return []
  return Object.values(data).flatMap((arr) => {
    if (!Array.isArray(arr) || arr.length === 0) return []

    const first = arr[0] // use first item for metadata

    // get highest evidence level for display
    const highestEvidenceLevel = arr.reduce((highest, item) => {
      const code = item?.strength?.primaryCoding?.code ?? 'N/A'
      const rank = evidenceOrder[code] ?? 999
      const bestRank = evidenceOrder[highest] ?? 999
      return rank < bestRank ? code : highest
    }, 'N/A')
    return [
      {
        variant_name:
          typeof first?.proposition?.subjectVariant === 'string'
            ? first.proposition.subjectVariant
            : (first?.proposition?.subjectVariant?.name ?? 'Unknown'),

        evidence_level: highestEvidenceLevel,
        disease: getDiseaseFromProposition(first?.proposition),
        therapy: getTherapyFromProposition(first?.proposition),
        significance: first?.proposition?.predicate
          ? formatSignificance(first?.proposition?.predicate)
          : 'N/A',
        sources: getSources(arr),
        grouped_evidence: arr,
      },
    ]
  })
}
