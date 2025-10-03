import { NormalizedResult } from '../pages/Results/utils'

type ColumnField = Exclude<keyof NormalizedResult, 'grouped_evidence'> | 'expandRow' | 'resultCount'

export interface ResultColumn {
  field: ColumnField
  headerName: string
  width: number
  render?: (value: NormalizedResult) => React.ReactNode
}
