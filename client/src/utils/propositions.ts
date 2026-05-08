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

type ConditionInfo = {
  diseases: string[]
  hasPediatricOnset: boolean
}

const PEDIATRIC_ONSET_TERMS = new Set<string>([
  'HP:0410280',
  'HP:0003623',
  'HP:0011463',
  'HP:0003593',
  'HP:0003621',
  'HP:0025708',
  'HP:0011462',
])

const emptyConditionInfo = (): ConditionInfo => ({
  diseases: [],
  hasPediatricOnset: false,
})

const getNamedValue = (value: unknown): string | undefined => {
  if (value && typeof value === 'object' && 'name' in value && typeof value.name === 'string') {
    return value.name
  }

  return undefined
}

const getIdValue = (value: unknown): string | undefined => {
  if (value && typeof value === 'object' && 'id' in value && typeof value.id === 'string') {
    return value.id
  }

  return undefined
}

const isPhenotype = (condition: unknown): boolean =>
  !!condition &&
  typeof condition === 'object' &&
  'conceptType' in condition &&
  condition.conceptType === 'Phenotype'

function getConditionInfo(condition: string | Condition | undefined): ConditionInfo {
  const result = emptyConditionInfo()

  const visit = (value: string | Condition | undefined) => {
    if (!value) return

    if (typeof value === 'string') {
      result.diseases.push(value)
      return
    }

    if ('conditions' in value) {
      value.conditions.forEach(visit)
      return
    }

    if (isPhenotype(value)) {
      const phenotypeId = getIdValue(value)
      if (phenotypeId && PEDIATRIC_ONSET_TERMS.has(phenotypeId)) {
        result.hasPediatricOnset = true
      }

      return
    }

    const diseaseName = getNamedValue(value)
    if (diseaseName) {
      result.diseases.push(diseaseName)
    }
  }

  visit(condition)
  console.log(result)
  return result
}

/**
 * Extracts disease names and pediatric-onset phenotype status from a proposition.
 *
 * Traverses nested Condition / ConditionSet structures associated with the
 * proposition and:
 * - collects all non-phenotype condition names into `diseases`
 * - sets `hasPediatricOnset` to true if any phenotype term ID matches one of
 *   the configured pediatric-onset HPO IDs
 *
 * Phenotype terms themselves are not returned.
 *
 * @param prop - A supported proposition type containing condition information
 * @returns Object containing flattened disease names and pediatric-onset status
 */
export function getConditionsFromProposition(
  prop:
    | VariantTherapeuticResponseProposition
    | VariantDiagnosticProposition
    | VariantPrognosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | ExperimentalVariantFunctionalImpactProposition,
): ConditionInfo {
  if (!prop) return emptyConditionInfo()

  switch (prop.type) {
    case 'VariantTherapeuticResponseProposition':
      return getConditionInfo(prop.conditionQualifier)

    case 'VariantDiagnosticProposition':
    case 'VariantPrognosticProposition':
    case 'VariantPathogenicityProposition':
      return getConditionInfo(prop.objectCondition)

    case 'VariantOncogenicityProposition':
      return getConditionInfo(prop.objectTumorType)

    case 'ExperimentalVariantFunctionalImpactProposition':
    default:
      return emptyConditionInfo()
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
