import { useState, FC } from 'react'
import { Box, Collapse, IconButton, Link, TableCell, TableRow, useTheme } from '@mui/material'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import { EvidenceLine } from '../../models/domain'
import { ResultColumn } from './types'
import { getEvidenceLabelUrl, getEvidenceSource, AssertionResult } from '../../utils'
import { getEvidenceGrade, isStatement } from '../../utils/results'

/* Dictate order that evidence appears underneath assertion **/
const gradeOrder: Record<string, number> = {
  A: 0,
  B: 1,
  C: 2,
  D: 3,
}
const getGradeRank = (line: EvidenceLine): number => {
  const grade = getEvidenceGrade(line.strengthOfEvidenceProvided)
  return grade && grade in gradeOrder ? gradeOrder[grade] : 999
}

const getFirstEvidenceItemId = (line: EvidenceLine): string => {
  const item = line.hasEvidenceItems?.[0]
  return isStatement(item) ? (item.id ?? '') : ''
}
const ResultTableRow: FC<{ row: AssertionResult; columns: ResultColumn[] }> = ({
  row,
  columns,
}) => {
  const [open, setOpen] = useState(false)
  const theme = useTheme()

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
                const val = row[column.field as keyof AssertionResult]
                return Array.isArray(val) ? val.join(', ') : (val as React.ReactNode)
              })()
            )}
          </TableCell>
        ))}
      </TableRow>
      <TableRow>
        <TableCell colSpan={columns.length} style={{ paddingBottom: 0, paddingTop: 0 }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            {row.grouped_evidence
              .sort((a: EvidenceLine, b: EvidenceLine) => {
                const rankA = getGradeRank(a)
                const rankB = getGradeRank(b)

                if (rankA !== rankB) {
                  return rankA - rankB
                }

                return getFirstEvidenceItemId(a).localeCompare(getFirstEvidenceItemId(b))
              })
              .map((line: EvidenceLine) => {
                const item = line.hasEvidenceItems?.[0]
                if (!isStatement(item)) return null

                const statement = item
                const { evidenceLabel, evidenceUrl } = getEvidenceLabelUrl(statement.id || '')
                const evidenceSource = statement.id ? getEvidenceSource(statement.id) : null
                const originalCode = statement.strength?.primaryCoding?.code
                const displayLevel = getEvidenceGrade(statement.strength)
                const levelColor =
                  displayLevel in theme.palette.evidence
                    ? theme.palette.evidence[displayLevel as keyof typeof theme.palette.evidence]
                    : '#ccc'

                return (
                  <Box
                    key={item.id}
                    margin={1}
                    sx={{
                      border: '1px solid #ccc',
                      borderLeft: `6px solid ${levelColor}`,
                      mb: 2,
                      p: 2,
                    }}
                  >
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
                      <strong>Evidence Level:</strong> {displayLevel}
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
                      <strong>Description:</strong> {item.description}
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
