import { describe, expect, it } from 'vitest'
import type { MappableConcept } from '../models/domain'
import { diseaseMatchesTissues, getAvailableDiseaseTissues, getDiseaseTissues } from './oncotree'

const disease = (overrides: Partial<MappableConcept>): MappableConcept => ({
  conceptType: 'Disease',
  ...overrides,
})

describe('OncoTree disease resolution', () => {
  it('resolves a direct MetaKB OncoTree disease ID to its root tissue', () => {
    expect(getDiseaseTissues(disease({ id: 'metakb.disease:oncotree_HGNEC' }))).toEqual([
      { code: 'BOWEL', name: 'Bowel' },
    ])
  })

  it('resolves a case-insensitive OncoTree mapping regardless of relation', () => {
    expect(
      getDiseaseTissues(
        disease({
          mappings: [
            {
              relation: 'broadMatch',
              coding: {
                id: 'ONCOTREE:PRNET',
                code: 'prnet',
                system: 'https://oncotree.mskcc.org/',
              },
            },
          ],
        }),
      ),
    ).toEqual([{ code: 'BRAIN', name: 'CNS/Brain' }])
  })

  it('deduplicates tissues from primary and mapped OncoTree terms', () => {
    expect(
      getDiseaseTissues(
        disease({
          primaryCoding: {
            code: 'COADREAD',
            system: 'https://oncotree.mskcc.org/',
          },
          mappings: [
            {
              relation: 'exactMatch',
              coding: {
                code: 'HGNEC',
                system: 'https://oncotree.mskcc.org/',
              },
            },
          ],
        }),
      ),
    ).toEqual([{ code: 'BOWEL', name: 'Bowel' }])
  })

  it('omits unknown and non-OncoTree terms', () => {
    expect(
      getDiseaseTissues(
        disease({
          id: 'metakb.disease:ncit_C5105',
          mappings: [
            {
              relation: 'exactMatch',
              coding: { code: 'UNKNOWN', system: 'https://oncotree.mskcc.org/' },
            },
          ],
        }),
      ),
    ).toEqual([])
  })

  it('lists distinct tissues and matches any selected tissue', () => {
    const bowelDisease = disease({ id: 'metakb.disease:oncotree_HGNEC' })
    const brainDisease = disease({
      primaryCoding: { code: 'PRNET', system: 'https://oncotree.mskcc.org/' },
    })

    expect(getAvailableDiseaseTissues([brainDisease, bowelDisease])).toEqual([
      { code: 'BOWEL', name: 'Bowel' },
      { code: 'BRAIN', name: 'CNS/Brain' },
    ])
    expect(diseaseMatchesTissues(bowelDisease, ['BRAIN', 'BOWEL'])).toBe(true)
    expect(diseaseMatchesTissues(bowelDisease, ['BRAIN'])).toBe(false)
  })
})
