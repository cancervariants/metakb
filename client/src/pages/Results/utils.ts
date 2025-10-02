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
