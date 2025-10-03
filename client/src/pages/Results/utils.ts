import {
  Condition,
  ExperimentalVariantFunctionalImpactProposition,
  Statement,
  Therapeutic,
  TherapyGroup,
  VariantDiagnosticProposition,
  VariantOncogenicityProposition,
  VariantPathogenicityProposition,
  VariantPrognosticProposition,
  VariantTherapeuticResponseProposition,
} from '../../ts_models'

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
 * Enum of supported evidence source names.
 */
export enum SourceName {
  Civic = 'CIViC',
  Moalmanac = 'MOAlmanac',
}

/**
 * Enum of namespace prefixes that identify evidence sources in identifiers.
 */
export enum SourceNamespacePrefix {
  Civic = 'civic',
  Moalmanac = 'moa',
}

/**
 * Given an evidence identifier, return an object containing the evidence label
 * and evidence url
 *
 * @param {string} evidenceIdentifier - The evidence_identifier field in the evidence
 *  table.
 * @returns {Object} - Object containing `evidenceLabel` and `evidenceUrl`
 */
export function getEvidenceLabelUrl(evidenceIdentifier: string): {
  evidenceLabel: string
  evidenceUrl: string
} {
  const recordId = evidenceIdentifier.split(':').slice(-1)[0]
  let evidenceLabel = ''
  let evidenceUrl = ''
  if (evidenceIdentifier.startsWith(SourceNamespacePrefix.Moalmanac)) {
    evidenceLabel = `${SourceName.Moalmanac} AID:${recordId}`
    evidenceUrl = `https://moalmanac.org/assertion/${recordId}`
  } else if (evidenceIdentifier.startsWith(`${SourceNamespacePrefix.Civic}.eid`)) {
    evidenceLabel = `${SourceName.Civic}  EID:${recordId}`
    evidenceUrl = `https://civicdb.org/evidence/${recordId}/summary`
  } else if (evidenceIdentifier.startsWith(`${SourceNamespacePrefix.Civic}.aid`)) {
    evidenceLabel = `${SourceName.Civic} AID:${recordId}`
    evidenceUrl = `https://civicdb.org/assertions/${recordId}/summary`
  }
  return {
    evidenceLabel: evidenceLabel,
    evidenceUrl: evidenceUrl,
  }
}

/**
 * Infers the source name (CIViC, MOAlmanac, etc.) from an evidence identifier.
 *
 * @param evidenceIdentifier - The identifier string from a Statement
 * @returns Source name if recognized, otherwise null
 */
export function getEvidenceSource(evidenceIdentifier: string): SourceName | null {
  if (evidenceIdentifier.startsWith(SourceNamespacePrefix.Moalmanac)) {
    return SourceName.Moalmanac
  } else if (
    evidenceIdentifier.startsWith(`${SourceNamespacePrefix.Civic}.eid`) ||
    evidenceIdentifier.startsWith(`${SourceNamespacePrefix.Civic}.aid`)
  ) {
    return SourceName.Civic
  }
  return null
}

/**
 * Collects unique source names from an array of evidence statements.
 *
 * @param statements - Array of `Statement` objects
 * @returns Array of distinct source names found in the evidence identifiers
 */
export function getSources(statements: Statement[]): string[] {
  const sources = new Set<string>()

  for (const s of statements) {
    const id = s.id
    if (!id) continue

    const source = getEvidenceSource(id)
    if (source) {
      sources.add(source)
    }
  }

  return Array.from(sources)
}

/**
 * Extracts human-readable condition names from a Condition object.
 *
 * @param condition - A string, MappableConcept, ConditionSet, or undefined
 * @returns Array of condition names (may be multiple for ConditionSet)
 */
function getConditionNames(condition: string | Condition | undefined): string[] {
  if (!condition) return ['N/A']

  if (typeof condition === 'string') {
    return [condition]
  }

  // If it's a MappableConcept
  if ('name' in condition) {
    return [condition.name ?? 'N/A']
  }

  // If it's a ConditionSet
  if ('conditions' in condition) {
    return condition.conditions.map((c) => c.name ?? 'N/A')
  }

  return ['N/A']
}

/**
 * Extracts associated disease names from a proposition, based on its type.
 *
 * @param prop - A variant proposition of various supported types
 * @returns Array of disease/condition names, or ["N/A"] if not available
 */
export function getDiseaseFromProposition(
  prop:
    | VariantTherapeuticResponseProposition
    | VariantDiagnosticProposition
    | VariantPrognosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | ExperimentalVariantFunctionalImpactProposition,
): string[] {
  if (!prop) return ['N/A']

  switch (prop.type) {
    case 'VariantTherapeuticResponseProposition':
      return getConditionNames(prop.conditionQualifier)

    case 'VariantDiagnosticProposition':
    case 'VariantPrognosticProposition':
      return getConditionNames(prop.objectCondition)

    case 'VariantOncogenicityProposition':
      return getConditionNames(prop.objectTumorType)
    case 'VariantPathogenicityProposition':
      return getConditionNames(prop.objectCondition)

    case 'ExperimentalVariantFunctionalImpactProposition':
      return ['N/A']

    default:
      return ['N/A']
  }
}

/**
 * Type guard to determine if a Therapeutic is a TherapyGroup.
 */
function isTherapyGroup(obj: Therapeutic): obj is TherapyGroup {
  return Array.isArray((obj as TherapyGroup).therapies)
}

/**
 * Formats a Therapeutic into a human-readable therapy string.
 * - For TherapyGroup, joins multiple therapies with "and"/"or"
 * - For MappableConcept of type "Therapy", returns its name
 *
 * @param objectTherapeutic - Therapeutic object to format
 * @returns Formatted therapy name or null if not available
 */
const formatTherapies = (objectTherapeutic: Therapeutic): string | null => {
  if (!objectTherapeutic) return null

  if (isTherapyGroup(objectTherapeutic)) {
    // It's a TherapyGroup
    const names = objectTherapeutic.therapies.map((t) => t?.name).filter(Boolean)
    if (names.length === 0) return null
    if (names.length === 1) return names[0] ?? null

    const operator = objectTherapeutic.membershipOperator?.toLowerCase() === 'or' ? 'or' : 'and'
    return `${names.slice(0, -1).join(', ')} ${operator} ${names[names.length - 1]}`
  }

  // Otherwise it's a MappableConcept
  if (objectTherapeutic.conceptType === 'Therapy') {
    return objectTherapeutic.name ?? null
  }

  return null
}

/**
 * Extracts therapy information from a proposition.
 * Only VariantTherapeuticResponseProposition objects have therapies.
 *
 * @param prop - Proposition object (may be undefined)
 * @returns Therapy name string, or "N/A" if not applicable
 */
export function getTherapyFromProposition(
  prop:
    | VariantTherapeuticResponseProposition
    | VariantDiagnosticProposition
    | VariantPrognosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | ExperimentalVariantFunctionalImpactProposition
    | undefined,
): string {
  if (!prop) return 'N/A'

  if ('objectTherapeutic' in prop) {
    const therapeutic = prop.objectTherapeutic
    return typeof therapeutic !== 'string' ? (formatTherapies(therapeutic) ?? 'N/A') : 'N/A'
  }

  return 'N/A'
}

/**
 * Type guard to check if a proposition includes a geneContextQualifier.
 *
 * @param prop - Proposition object (may be undefined)
 * @returns True if the proposition has a geneContextQualifier property
 */
export function hasGeneContextQualifier(
  prop:
    | ExperimentalVariantFunctionalImpactProposition
    | VariantDiagnosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | VariantPrognosticProposition
    | VariantTherapeuticResponseProposition
    | undefined,
): prop is Exclude<typeof prop, ExperimentalVariantFunctionalImpactProposition | undefined> & {
  geneContextQualifier?: { extensions?: { name: string; value: unknown }[] }
} {
  return !!prop && 'geneContextQualifier' in prop
}
