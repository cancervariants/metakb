import { Statement } from '../../ts_models'

// model for storing the data needed to display the aggregated evidence rows for the results table
export interface NormalizedResult {
  variant_name: string
  evidence_level: string
  disease: string
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
