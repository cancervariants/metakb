/**
 * Utilities for working with proposition objects within Statements.
 * - Extracts disease/condition names from propositions
 * - Extracts therapy information and formats therapy groups
 * - Provides type guards for TherapyGroup and geneContextQualifier
 *
 * These helpers isolate proposition-specific branching logic so that
 * normalization and UI code can remain clean and consistent.
 */

import {
  ExperimentalVariantFunctionalImpactProposition,
  VariantDiagnosticProposition,
  VariantOncogenicityProposition,
  VariantPathogenicityProposition,
  VariantPrognosticProposition,
  VariantTherapeuticResponseProposition,
  Therapeutic,
  TherapyGroup,
  Condition,
} from '../models/domain'

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
