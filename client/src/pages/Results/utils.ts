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

// model for storing the data needed to display the aggregated evidence rows for the results table
export interface NormalizedResult {
  variant_name: string
  evidence_level: string
  disease: string[]
  therapy: string
  significance: string
  grouped_evidence: Statement[]
}

// evidence level ranking
export const evidenceOrder: Record<string, number> = {
  A: 1,
  'Level A': 1,
  B: 3,
  C: 4,
  D: 5,
  E: 6,
  'N/A': 999,
}

// helper: compute counts by variant name
export function buildCountMap(results: any[], key: keyof any): Record<string, number> {
  return results.reduce((acc: Record<string, number>, item: any) => {
    const val = item[key]
    if (val) {
      acc[val] = (acc[val] || 0) + 1
    }
    return acc
  }, {})
}

// Values for sources
export enum SourceName {
  Civic = 'CIViC',
  Moalmanac = 'MOAlmanac',
}

// Values for source namespace prefix
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
 * Given an evidence identifier, return the source name
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
 * Given an array of evidence statements, return unique source names
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

function isTherapyGroup(obj: Therapeutic): obj is TherapyGroup {
  return Array.isArray((obj as TherapyGroup).therapies)
}

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
