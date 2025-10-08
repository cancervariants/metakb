/**
 * Utilities for handling evidence sources (e.g. CIViC, MOAlmanac).
 * - SourceName and SourceNamespacePrefix enums define supported sources
 * - `getEvidenceLabelUrl` generates human-friendly labels and source URLs
 * - `getEvidenceSource` infers the source from an evidence identifier
 * - `getSources` collects unique sources from a set of Statements
 *
 * These functions encapsulate all logic related to external evidence databases.
 */

import { Statement } from '../models/domain'

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
