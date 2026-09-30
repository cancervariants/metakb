import oncotree from '../data/oncotree.json'
import type { Coding, Coding1, MappableConcept } from '../models/domain'

type OncoTreeNode = {
  code: string
  name: string
  children: Record<string, OncoTreeNode>
}

export type OncoTreeTissue = {
  code: string
  name: string
}

export type DiseaseTissueGroup = OncoTreeTissue & {
  diseases: (MappableConcept & { id: string })[]
}

const ONCOTREE_ID_PATTERN = /(?:^|[:_])oncotree[_:](.+)$/i

const normalizeCode = (value: string | null | undefined): string | null => {
  const normalized = value?.trim().toUpperCase()
  return normalized || null
}

const isOncoTreeCoding = (coding: Coding | Coding1): boolean =>
  /oncotree/i.test(coding.id ?? '') || /oncotree/i.test(coding.system)

const codeFromCoding = (coding: Coding | Coding1): string | null => {
  if (!isOncoTreeCoding(coding)) return null
  return normalizeCode(coding.code)
}

const codeFromDiseaseId = (id: string | null | undefined): string | null => {
  const match = id?.match(ONCOTREE_ID_PATTERN)
  return match ? normalizeCode(match[1]) : null
}

const buildTissueIndex = (root: OncoTreeNode): Map<string, OncoTreeTissue> => {
  const index = new Map<string, OncoTreeTissue>()

  const visit = (node: OncoTreeNode, tissue: OncoTreeTissue | null) => {
    const nextTissue =
      node.code === root.code
        ? null
        : (tissue ?? {
            code: node.code,
            name: node.name,
          })

    if (nextTissue) index.set(node.code.toUpperCase(), nextTissue)

    Object.values(node.children).forEach((child) => visit(child, nextTissue))
  }

  visit(root, null)
  return index
}

const root = oncotree.TISSUE as OncoTreeNode
const tissueByOncoTreeCode = buildTissueIndex(root)

/**
 * Return every top-level OncoTree tissue represented by a disease concept.
 * Direct OncoTree disease IDs, primary codings, and any OncoTree mapping are eligible.
 */
export const getDiseaseTissues = (disease: MappableConcept): OncoTreeTissue[] => {
  const codes = [
    codeFromDiseaseId(disease.id),
    disease.primaryCoding ? codeFromCoding(disease.primaryCoding) : null,
    ...(disease.mappings ?? []).map((mapping) => codeFromCoding(mapping.coding)),
  ]

  const tissues = new Map<string, OncoTreeTissue>()
  codes.forEach((code) => {
    if (!code) return
    const tissue = tissueByOncoTreeCode.get(code)
    if (tissue) tissues.set(tissue.code, tissue)
  })

  return Array.from(tissues.values())
}

export const getAvailableDiseaseTissues = (diseases: MappableConcept[]): OncoTreeTissue[] => {
  const tissues = new Map<string, OncoTreeTissue>()
  diseases.forEach((disease) => {
    getDiseaseTissues(disease).forEach((tissue) => tissues.set(tissue.code, tissue))
  })

  return Array.from(tissues.values()).sort((a, b) => a.name.localeCompare(b.name))
}

/**
 * Group ID-bearing disease concepts by every top-level OncoTree tissue to
 * which they resolve. A disease with mappings in multiple tissues appears in
 * each matching group.
 */
export const getDiseaseTissueGroups = (diseases: MappableConcept[]): DiseaseTissueGroup[] => {
  const groups = new Map<string, DiseaseTissueGroup>()

  diseases.forEach((disease) => {
    if (!disease.id) return

    getDiseaseTissues(disease).forEach((tissue) => {
      const group = groups.get(tissue.code) ?? { ...tissue, diseases: [] }
      if (!group.diseases.some((groupedDisease) => groupedDisease.id === disease.id)) {
        group.diseases.push(disease as MappableConcept & { id: string })
      }
      groups.set(tissue.code, group)
    })
  })

  return Array.from(groups.values())
    .map((group) => ({
      ...group,
      diseases: [...group.diseases].sort((a, b) => (a.name ?? a.id).localeCompare(b.name ?? b.id)),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

export const diseaseMatchesTissues = (disease: MappableConcept, selectedTissueCodes: string[]) =>
  getDiseaseTissues(disease).some((tissue) => selectedTissueCodes.includes(tissue.code))
