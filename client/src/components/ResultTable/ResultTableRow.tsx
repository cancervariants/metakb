import { useState, FC } from 'react'
import { Box, Collapse, IconButton, Link, TableCell, TableRow } from '@mui/material'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import { Statement } from '../../models/domain'
import { ResultColumn } from './types'
import { getEvidenceLabelUrl, getEvidenceSource, NormalizedResult } from '../../utils'
import { normalizeEvidenceLevelFromStrength } from '../../utils/normalization'

const ResultTableRow: FC<{ row: NormalizedResult; columns: ResultColumn[] }> = ({
  row,
  columns,
}) => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <TableRow>
        {columns.map((column) => (
          <TableCell key={column.field}>
            {column.field === 'expandRow' ? (
              <IconButton onClick={() => setOpen(!open)}>
                {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
              </IconButton>
            ) : column.render ? (
              column.render(row)
            ) : (
              (() => {
                const val = row[column.field as keyof NormalizedResult]
                return Array.isArray(val) ? val.join(', ') : (val as React.ReactNode)
              })()
            )}
          </TableCell>
        ))}
      </TableRow>
      <TableRow>
        <TableCell colSpan={columns.length} style={{ paddingBottom: 0, paddingTop: 0 }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            {row.grouped_evidence.map((e: Statement) => {
              const { evidenceLabel, evidenceUrl } = getEvidenceLabelUrl(e.id || '')
              const evidenceSource = e.id ? getEvidenceSource(e.id) : null
              const originalCode = e.strength?.primaryCoding?.code

              return (
                <Box key={e.id} margin={1} sx={{ border: '1px solid #ccc', mb: 2, p: 2 }}>
                  <div>
                    <Link
                      href={evidenceUrl}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontWeight: 'bold' }}
                    >
                      <span>{evidenceLabel}</span>
                    </Link>
                  </div>
                  <div>
                    <strong>Evidence Level:</strong>{' '}
                    {normalizeEvidenceLevelFromStrength(e.strength)}
                    {evidenceSource && originalCode ? (
                      <>
                        {' '}
                        <span style={{ color: 'grey' }}>
                          ({evidenceSource}: {originalCode})
                        </span>
                      </>
                    ) : null}
                  </div>
                  <div>
                    <strong>Description:</strong> {e.description}
                  </div>
                </Box>
              )
            })}
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  )
}

export default ResultTableRow
