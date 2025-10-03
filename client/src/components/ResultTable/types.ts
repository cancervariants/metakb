/**
 * Type definitions for the `ResultTable` component.
 *
 * These types define the shape of column configurations used to render
 * normalized evidence results in the table. Each column specifies:
 *  - which field of a `NormalizedResult` it maps to,
 *  - its display name in the header,
 *  - its width in pixels,
 *  - and an optional custom render function.
 *
 * Columns can also include special non-data fields (`expandRow`, `resultCount`)
 * to handle UI interactions or derived values.
 */

import { NormalizedResult } from '../../utils'

/**
 * Union of all supported column field keys for the results table.
 * - Includes all properties of `NormalizedResult` except `grouped_evidence`
 *   (since that is expanded separately).
 * - Also includes special fields:
 *   - `expandRow`: UI-only column for expand/collapse toggles
 *   - `resultCount`: Derived column for showing evidence record counts
 */
type ColumnField = Exclude<keyof NormalizedResult, 'grouped_evidence'> | 'expandRow' | 'resultCount'

/**
 * Represents a single column definition in the results table.
 */
export interface ResultColumn {
  // Key indicating which field or special column this represents
  field: ColumnField
  // Display name for the column as it should appear in the table
  headerName: string
  // Column width in pixels
  width?: number
  /**
   * Optional render function to customize cell rendering.
   * Receives the full `NormalizedResult` for the row.
   */
  render?: (value: NormalizedResult) => React.ReactNode
}
