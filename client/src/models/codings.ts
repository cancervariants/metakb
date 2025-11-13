/**
 *
 * Defines standardized enumerations and mappings for evidence-related codings
 * used throughout MetaKB. These constants are part of the domain layer and
 * provide a single source of truth for interpreting evidence strength and
 * coding identifiers from external data sources such as CIViC or Moalmanac
 * or other integrated evidence providers.
 *
 * This module serves three main purposes:
 *  1. Establish evidence level codes (A–E) used across MetaKB. (AMP/ASCO/CAP evidence codes)
 *  2. Map external or system-specific codes (e.g., "e000009") to these levels.
 *  3. Map human-readable evidence strength terms (e.g., "preclinical evidence")
 *     to the same standardized levels.
 */

/**
 * Enumeration of standardized evidence levels used in MetaKB.
 *
 * These levels represent decreasing confidence or data quality from A to E:
 *  - **A:** Authoritative / FDA-recognized evidence
 *  - **B:** Clinical evidence (cohort-level)
 *  - **C:** Clinical intervention / observation / case study evidence
 *  - **D:** Preclinical evidence
 *  - **E:** Inferential evidence
 */
export enum EvidenceLevel {
  A = 'A',
  B = 'B',
  C = 'C',
  D = 'D',
  E = 'E',
}

/**
 * Mapping of VICC evidence coding identifiers
 * to standardized evidence codes.
 *
 * For example:
 *  - `"e000009"` → `EvidenceLevel.D`
 *  - `"e000010"` → `EvidenceLevel.E`
 *
 */
export enum EvidenceCodeMapping {
  e000001 = EvidenceLevel.A,
  e000002 = EvidenceLevel.A,
  e000003 = EvidenceLevel.A,
  e000004 = EvidenceLevel.B,
  e000005 = EvidenceLevel.B,
  e000006 = EvidenceLevel.C,
  e000007 = EvidenceLevel.C,
  e000008 = EvidenceLevel.C,
  e000009 = EvidenceLevel.D,
  e000010 = EvidenceLevel.E,
}

/**
 * Maps human-readable textual descriptions of evidence strength
 * (as found in metadata from some external providers) to standardized
 * MetaKB evidence levels.
 *
 * This mapping supports strings such as:
 *  - `"authoritative evidence"` → `EvidenceLevel.A`
 *  - `"preclinical evidence"` → `EvidenceLevel.D`
 *  - `"inferential evidence"` → `EvidenceLevel.E`
 *
 * These mappings are used when parsing or normalizing data that uses
 * descriptive terms rather than formal codes. (Like Moalmanac does)
 */
export const TermToEvidenceLevel: Record<string, EvidenceLevel> = {
  'authoritative evidence': EvidenceLevel.A,
  'fda recognized evidence': EvidenceLevel.A,
  'professional guideline evidence': EvidenceLevel.A,
  'clinical evidence': EvidenceLevel.B,
  'clinical cohort evidence': EvidenceLevel.B,
  'clinical intervention evidence': EvidenceLevel.C,
  'clinical observation evidence': EvidenceLevel.C,
  'clinical case study evidence': EvidenceLevel.C,
  'preclinical evidence': EvidenceLevel.D,
  'inferential evidence': EvidenceLevel.E,
}
