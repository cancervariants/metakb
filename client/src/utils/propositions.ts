/**
 * Utilities for working with proposition and entity objects within Statements.
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
import { NormalizedTherapy, TherapyInteractionType } from './results'

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
 * @returns NormalizedTherapy object containing therapy names and interaction type
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
): NormalizedTherapy {
  let interactionType = TherapyInteractionType.None
  let therapies: string[] = []

  if (!prop) return { therapyInteractionType: interactionType, therapyNames: therapies }

  if ('objectTherapeutic' in prop) {
    const therapeutic = prop.objectTherapeutic

    if (typeof therapeutic !== 'string') {
      therapies = getTherapyNames(therapeutic) ?? []

      if (isTherapyGroup(therapeutic)) {
        const operator = therapeutic.membershipOperator?.toUpperCase()
        if (operator === 'AND') {
          interactionType = TherapyInteractionType.Combination
        } else if (operator === 'OR') {
          interactionType = TherapyInteractionType.Substitution
        }
      }
    }
  }

  return { therapyInteractionType: interactionType, therapyNames: therapies }
}

/**
 * Type guard to determine if a Therapeutic is a TherapyGroup.
 */
function isTherapyGroup(obj: Therapeutic): obj is TherapyGroup {
  return Array.isArray((obj as TherapyGroup).therapies)
}

/**
 * Extracts human-readable therapy names from a Therapeutic object.
 *
 * @param objectTherapeutic - Therapeutic object to format
 * @returns String list of therapy names or [] if not available
 */
const getTherapyNames = (objectTherapeutic: Therapeutic): string[] | null => {
  if (!objectTherapeutic) return null

  if (isTherapyGroup(objectTherapeutic)) {
    // It's a TherapyGroup
    return objectTherapeutic.therapies.map((t) => t?.name).filter((n): n is string => Boolean(n))
  }

  // Otherwise it's a single MappableConcept
  if (objectTherapeutic.conceptType === 'Therapy') {
    return objectTherapeutic.name ? [objectTherapeutic.name] : []
  }

  return []
}

const getNamedValue = (value: unknown): string => {
  if (value && typeof value === 'object' && 'name' in value && typeof value.name === 'string') {
    return value.name
  }
  return 'N/A'
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

  if ('conditions' in condition) {
    return condition.conditions.map(getNamedValue)
  }

  return [getNamedValue(condition)]
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
 * Extracts associated variant name from a proposition.
 *
 * @param prop - A variant proposition of various supported types
 * @returns String variant name, or "" if not available
 */
export function getVariantNameFromProposition(
  prop:
    | VariantTherapeuticResponseProposition
    | VariantDiagnosticProposition
    | VariantPrognosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | ExperimentalVariantFunctionalImpactProposition,
): string {
  if (!prop) return ''

  const subjectVariant = prop.subjectVariant

  if (typeof subjectVariant === 'string') {
    return subjectVariant
  } else if (subjectVariant && 'name' in subjectVariant) {
    return subjectVariant.name ?? ''
  }
  return ''
}

export type HasExtensions = {
  extensions?: { name: string; value: unknown }[] | null
}

export const getExtension = <T>(obj: HasExtensions, name: string): T | null => {
  return (obj.extensions?.find((ext) => ext.name === name)?.value as T) ?? null
}
