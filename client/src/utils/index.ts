/**
 * Barrel file for re-exporting all utilities:
 * - Results normalization (`results.ts`)
 * - Filter helpers (`filters.ts`)
 * - Evidence source helpers (`sources.ts`)
 * - Proposition helpers (`propositions.ts`)
 * - Metadata retrieval (`metadata.ts`)
 *
 * Consumers should import from this index rather than from individual files
 * to ensure consistent dependency management and avoid circular imports.
 */

export * from './results'
export * from './filters'
export * from './sources'
export * from './propositions'
export * from './metadata'
