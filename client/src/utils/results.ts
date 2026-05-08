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

import {
  EvidenceLine,
  MappableConcept,
  Statement,
  VariantDiagnosticProposition,
  VariantPrognosticProposition,
  VariantTherapeuticResponseProposition,
} from '../models/domain'
import {
  getConditionsFromProposition,
  getTherapyFromProposition,
  getVariantNameFromProposition,
} from './propositions'
import { getSources } from './sources'

export const TAB_LABELS: Record<'therapeutic' | 'diagnostic' | 'prognostic', string> = {
  therapeutic: 'Therapeutic',
  diagnostic: 'Diagnostic',
  prognostic: 'Prognostic',
}

// Represents a therapy interaction type - either combination or substitution, for groups, or None for a single therapy
export enum TherapyInteractionType {
  Combination = 'Combination',
  Substitution = 'Substitution',
  None = '',
}

/**
 * Represents a normalized therapy
 * Contains a list of therapy names and the interaction type
 */
export interface NormalizedTherapy {
  therapyNames: string[]
  therapyInteractionType: TherapyInteractionType
}

export interface StarRating {
  starRating: number
  ratingReason: string
}

type SupportedAssertionProposition =
  | VariantDiagnosticProposition
  | VariantPrognosticProposition
  | VariantTherapeuticResponseProposition

const isSupportedAssertionProposition = (
  proposition: Statement['proposition'] | null | undefined,
): proposition is SupportedAssertionProposition => {
  if (!proposition || typeof proposition !== 'object') return false

  return (
    proposition.type === 'VariantDiagnosticProposition' ||
    proposition.type === 'VariantPrognosticProposition' ||
    proposition.type === 'VariantTherapeuticResponseProposition'
  )
}

/**
 * Represents a single row for a MetaKB assertion, aggregating evidence
 * from one or more `Statement` objects into a single table row.
 */
export interface AssertionResult {
  /** Proposition defining the assertion */
  proposition: SupportedAssertionProposition
  /** Human-readable variant name (normalized for display) */
  variant_name: string
  /** Highest evidence level among grouped evidence */
  evidence_level: string
  /** Associated diseases, may include multiple names */
  disease: string[]
  /** Associated phenotype options */
  hasPediatricOnset: boolean
  /** Therapy or combination therapy (if applicable) */
  therapy: NormalizedTherapy
  /** Clinical significance string */
  significance: string
  /** Lines of evidence (incl statements) grouped into this row */
  grouped_evidence: EvidenceLine[]
  /** Sources (databases) that contributed evidence to this row */
  sources: string[]
  star_rating: StarRating
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

export const isStatement = (item: unknown): item is Statement =>
  typeof item === 'object' &&
  item !== null &&
  'type' in item &&
  (item as { type?: unknown }).type === 'Statement'

export const isEvidenceLine = (item: unknown): item is EvidenceLine =>
  typeof item === 'object' &&
  item !== null &&
  'directionOfEvidenceProvided' in item &&
  'hasEvidenceItems' in item

const getTerminalEvidenceLines = (assertion?: Statement | null): EvidenceLine[] => {
  const results: EvidenceLine[] = []

  const walk = (line: EvidenceLine): void => {
    const items = line.hasEvidenceItems ?? []

    const hasDirectStatementChild = items.some(isStatement)
    if (hasDirectStatementChild) {
      results.push(line)
      return
    }

    items.forEach((item) => {
      if (isEvidenceLine(item)) {
        walk(item)
      }
    })
  }

  ;(assertion?.hasEvidenceLines ?? []).forEach((line) => {
    if (isEvidenceLine(line)) {
      walk(line)
    }
  })

  return results
}

const getStarRatingValue = (value: unknown): number => {
  if (!value || typeof value !== 'object' || !('primaryCoding' in value)) return 1

  const primaryCoding = value.primaryCoding
  if (!primaryCoding || typeof primaryCoding !== 'object' || !('code' in primaryCoding)) {
    return 1
  }

  if (typeof primaryCoding.code !== 'string') return 1

  const match = primaryCoding.code.match(/^(\d+)_star$/)
  return match ? Number(match[1]) : 1
}

/**
 * Normalizes raw assertion statements into `NormalizedResult` rows
 * suitable for display in the results table.
 *
 * Each entry in the input `data` represents a single MetaKB assertion.
 * This function:
 *  - Extracts display metadata (variant name, disease(s), therapy, significance)
 *  - Collects all source databases referenced by terminal evidence statements
 *  - Preserves the terminal evidence lines in `grouped_evidence`
 *
 * Terminal evidence lines are the deepest evidence lines under the MetaKB
 * assertion that directly contain evidence item `Statement`s. The traversal
 * does not recurse into those statements, even if they themselves contain
 * evidence lines.
 *
 * @param data - A record mapping keys to assertion `Statement` objects
 *               returned from the API.
 * @returns Array of `NormalizedResult` objects, one per assertion.
 *          Returns an empty array if the input is empty or invalid.
 */
export const normalizeResults = (data: Record<string, Statement>): AssertionResult[] => {
  if (!data || Object.keys(data).length === 0) return []

  return Object.values(data).flatMap((assertion) => {
    if (!assertion || !isSupportedAssertionProposition(assertion.proposition)) return []

    const groupedEvidence = getTerminalEvidenceLines(assertion)
    const groupedStatements = groupedEvidence
      .flatMap((line) => line.hasEvidenceItems ?? [])
      .filter(isStatement)

    const extensions = assertion.extensions
    let starRating: StarRating = {
      starRating: 1,
      ratingReason: 'Does not meet other criteria',
    }

    if (extensions) {
      const ratingExt = extensions.find((ext) => ext.name === 'metakb_star_rating')?.value
      const reasonExt = extensions.find((ext) => ext.name === 'metakb_star_rating_reason')?.value

      const rating = getStarRatingValue(ratingExt)

      starRating = {
        starRating: rating,
        ratingReason: typeof reasonExt === 'string' ? reasonExt : starRating.ratingReason,
      }
    }
    const conditions = getConditionsFromProposition(assertion.proposition)
    return [
      {
        proposition: assertion.proposition,
        variant_name: getVariantNameFromProposition(assertion.proposition),
        evidence_level: getEvidenceGrade(assertion.strength),
        disease: conditions.diseases,
        hasPediatricOnset: conditions.hasPediatricOnset,
        therapy: getTherapyFromProposition(assertion.proposition),
        significance: assertion.proposition?.predicate
          ? formatSignificance(assertion.proposition.predicate)
          : 'N/A',
        sources: getSources(groupedStatements),
        grouped_evidence: groupedEvidence,
        star_rating: starRating,
      },
    ]
  })
}

/**
 * A single column of data for a VisX <HeatmapRect>.
 *
 * VisX interprets the *outer* dimension of the heatmap data as COLUMNS.
 * Each column contains a list of "bins", where each bin represents
 * a cell in the heatmap for:
 *
 *    (variant at rowIndex, disease at columnIndex)
 *
 * The index of each bin corresponds directly to the row index (variant index).
 *
 * For example, bins[3] is the cell located at:
 *    - row:    variants[3]
 *    - column: diseases[columnIndex]
 */
export interface VisxColumn {
  bins: { count: number }[]
}

/**
 * Full data structure expected by VisX <HeatmapRect>.
 *
 * columns:
 *    - The outer array
 *    - Each item represents a single disease (x-axis column)
 *    - columns[i] corresponds to diseases[i]
 *
 * variants:
 *    - Ordered list of variant names (y-axis labels / rows)
 *    - The index of a variant corresponds to the rowIndex inside each column's bins[]
 *
 * diseases:
 *    - Ordered list of disease names (x-axis labels / columns)
 *    - The index of a disease corresponds to the columnIndex in the heatmap
 *
 * Mapping summary:
 *
 *      columns[columnIndex].bins[rowIndex].count
 *
 *  gives the evidence count for:
 *      variants[rowIndex]   (y-axis row)
 *      diseases[columnIndex] (x-axis column)
 *
 * This strict indexing alignment is required so that:
 *    - <AxisLeft> ticks use variants[rowIndex]
 *    - <AxisBottom> ticks use diseases[columnIndex]
 *    - <HeatmapRect> draws cells in the correct positions
 */
export interface VisxHeatmapData {
  columns: VisxColumn[]
  variants: string[]
  diseases: string[]
}

/**
 * Constructs a variant x disease evidence matrix formatted for consumption by the VisX <HeatmapRect> component.
 *
 * This function:
 *   1. Extracts unique variants and diseases from the input results
 *   2. Computes the total evidence counts per variant and per disease
 *   3. Applies optional limiting (only keep the top N variants or diseases)
 *   4. Builds a rectangular matrix of shape: matrix[diseaseIndex][variantIndex]
 *      Each cell holds the aggregated evidence count for variants[variantIndex] and diseases[diseaseIndex]
 *   5. Converts the matrix into the VisX heatmap data format:
 *      {
 *        columns: [
 *             { bins: [ {count}, {count}, ... ] },  // column 0 (disease 0)
 *             { bins: [ {count}, {count}, ... ] },  // column 1
 *             ...
 *           ],
 *           variants: string[],   // row labels
 *           diseases: string[]    // column labels
 *       }
 *
 *      The `columns` array aligns 1:1 with `diseases`, and each column's
 *      `bins` array aligns 1:1 with `variants`. This ensures that:
 *
 *         - variants[rowIndex] always corresponds to bin[rowIndex]
 *         - diseases[columnIndex] always corresponds to columns[columnIndex]
 *
 * @param results A list of normalized result objects
 * @param limitRows Optional maximum number of variants (rows)
 * @param limitCols Optional maximum number of diseases (columns) to retain
 * @returns
 */
export function buildVariantDiseaseMatrix(
  results: AssertionResult[],
  limitRows?: number,
  limitCols?: number,
): VisxHeatmapData {
  // 1. Unique lists (unsorted)
  let variants = Array.from(new Set(results.map((r) => r.variant_name)))
  let diseases = Array.from(new Set(results.flatMap((r) => r.disease)))

  // 2. Variant totals
  const variantTotals = variants.map((v) =>
    results
      .filter((r) => r.variant_name === v)
      .reduce((sum, r) => sum + r.grouped_evidence.length, 0),
  )

  // sort variants by total desc and limit
  let variantSortOrder = variants
    .map((v, i) => ({ v, total: variantTotals[i] }))
    .sort((a, b) => b.total - a.total)

  if (limitRows && limitRows < variantSortOrder.length) {
    variantSortOrder = variantSortOrder.slice(0, limitRows)
  }

  variants = variantSortOrder.map((v) => v.v)

  // 3. Disease totals
  const diseaseTotals = diseases.map((d) =>
    results
      .filter((r) => r.disease.includes(d))
      .reduce((sum, r) => sum + r.grouped_evidence.length, 0),
  )

  // sort diseases by total desc and limit
  let diseaseSortOrder = diseases
    .map((d, i) => ({ d, total: diseaseTotals[i] }))
    .sort((a, b) => b.total - a.total)

  if (limitCols && limitCols < diseaseSortOrder.length) {
    diseaseSortOrder = diseaseSortOrder.slice(0, limitCols)
  }

  diseases = diseaseSortOrder.map((d) => d.d)

  // 4. Build matrix [columns][rows] = [disease][variant]
  const matrix = diseases.map(() => variants.map(() => 0))

  results.forEach((row) => {
    const evidence = row.grouped_evidence.length

    const vIdx = variants.indexOf(row.variant_name)
    if (vIdx === -1) return

    row.disease.forEach((d) => {
      const dIdx = diseases.indexOf(d)
      if (dIdx === -1) return

      // column = disease, row = variant
      matrix[dIdx][vIdx] += evidence
    })
  })

  // 5. Convert to VisX columns
  const columns: VisxColumn[] = matrix.map((colVals) => ({
    bins: colVals.map((count) => ({ count })),
  }))

  return { columns, variants, diseases }
}

/**
 * Transform an evidence strength concept to a simple A–D grade for display.
 *
 * @param strength - Evidence strength concept object or null/undefined.
 * @returns Evidence grade (`"A"`, `"B"`, `"C"`, `"D"`) or an empty string if
 * the grade cannot be determined.
 */
export function getEvidenceGrade(strength?: MappableConcept | null): string {
  if (!strength || !Array.isArray(strength.extensions)) return ''

  const displayExtension = strength.extensions.find(
    (ext) => typeof ext === 'object' && ext !== null && ext.name === 'metakb_display_value',
  )

  return typeof displayExtension?.value === 'string' ? displayExtension.value : ''
}
