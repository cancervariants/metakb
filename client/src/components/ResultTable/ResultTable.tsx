import { useState, MouseEvent, FC } from 'react'
import {
  Box,
  IconButton,
  Rating,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TablePagination,
  TableRow,
  Tooltip,
  useTheme,
} from '@mui/material'
import FirstPageIcon from '@mui/icons-material/FirstPage'
import KeyboardArrowLeft from '@mui/icons-material/KeyboardArrowLeft'
import KeyboardArrowRight from '@mui/icons-material/KeyboardArrowRight'
import LastPageIcon from '@mui/icons-material/LastPage'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import ResultTableRow from './ResultTableRow'
import { ResultColumn } from './types'
import { NormalizedResult, TherapyInteractionType } from '../../utils'
import { getEvidenceGrade } from '../../utils/results'
import { EvidenceLevel } from '../../models/codings'
import { PieChart, Pie, Cell } from 'recharts'
import theme from '../../theme'
import { EvidenceLegend } from './EvidenceLegend'

interface TablePaginationActionsProps {
  count: number
  page: number
  rowsPerPage: number
  onPageChange: (event: MouseEvent<HTMLButtonElement>, newPage: number) => void
}

function TablePaginationActions(props: TablePaginationActionsProps) {
  const theme = useTheme()
  const { count, page, rowsPerPage, onPageChange } = props
  const lastPage = Math.ceil(count / rowsPerPage) - 1

  const handleFirstPageButtonClick = (event: MouseEvent<HTMLButtonElement>) => {
    onPageChange(event, 0)
  }

  const handleBackButtonClick = (event: MouseEvent<HTMLButtonElement>) => {
    onPageChange(event, page - 1)
  }

  const handleNextButtonClick = (event: MouseEvent<HTMLButtonElement>) => {
    onPageChange(event, page + 1)
  }

  const handleLastPageButtonClick = (event: MouseEvent<HTMLButtonElement>) => {
    onPageChange(event, Math.max(0, lastPage))
  }

  // we don't support rtl yet - am unsure whether or not to leave this in or just hardcode the table for ltr for now
  const isRtl = theme.direction === 'rtl'
  const onLastPage = page >= lastPage

  return (
    <Box sx={{ flexShrink: 0, ml: 2.5 }}>
      <IconButton
        onClick={handleFirstPageButtonClick}
        disabled={page === 0}
        aria-label="first page"
      >
        {isRtl ? <LastPageIcon /> : <FirstPageIcon />}
      </IconButton>
      <IconButton onClick={handleBackButtonClick} disabled={page === 0} aria-label="previous page">
        {isRtl ? <KeyboardArrowRight /> : <KeyboardArrowLeft />}
      </IconButton>
      <IconButton onClick={handleNextButtonClick} disabled={onLastPage} aria-label="next page">
        {isRtl ? <KeyboardArrowLeft /> : <KeyboardArrowRight />}
      </IconButton>
      <IconButton onClick={handleLastPageButtonClick} disabled={onLastPage} aria-label="last page">
        {isRtl ? <FirstPageIcon /> : <LastPageIcon />}
      </IconButton>
    </Box>
  )
}

interface ResultTableProps {
  // list of results
  results: NormalizedResult[]
  // result type - used for determining which columns to show
  resultType: 'therapeutic' | 'prognostic' | 'diagnostic'
}

const ResultTable: FC<ResultTableProps> = ({ results, resultType }) => {
  const [open, setOpen] = useState(false)

  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  function handleChangePage(_event: React.MouseEvent<HTMLButtonElement> | null, newpage: number) {
    setPage(newpage)
  }

  function handleChangeRowsPerPage(
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  let columns: ResultColumn[] = [
    {
      field: 'star_rating',
      headerName: 'Star Rating',
      width: 100,
      render: (value: NormalizedResult) => {
        const rating = value.star_rating.starRating
        const reason = value.star_rating.ratingReason
        return (
          <Tooltip
            arrow
            title={reason || 'No rating explanation available'}
            slotProps={{
              tooltip: {
                sx: {
                  fontSize: theme.typography.pxToRem(14),
                },
              },
            }}
          >
            <Stack component="span" sx={{ display: 'inline-flex' }}>
              <Rating name="half-rating" value={rating} precision={1} readOnly max={4} />
            </Stack>
          </Tooltip>
        )
      }
    },
    {
      field: 'variant_name',
      headerName: 'Variant',
      width: 150,
      render: (value: NormalizedResult) => value?.variant_name,
    },
    {
      field: 'evidence_summary',
      headerName: 'Evidence Summary',
      width: 100,
      render: (value: NormalizedResult) => {
        const supportingEvidence = value.grouped_evidence
        // get array of normalized codes from supporting evidence
        const codeGroups = supportingEvidence.map((evidence) => getEvidenceGrade(evidence.strength))

        // format into object with counts
        const counts = codeGroups.reduce<Record<EvidenceLevel, number>>(
          (acc, code) => {
            if (code && Object.values(EvidenceLevel).includes(code as EvidenceLevel)) {
              acc[code as EvidenceLevel] = (acc[code as EvidenceLevel] || 0) + 1
            }
            return acc
          },
          { A: 0, B: 0, C: 0, D: 0, E: 0 },
        )
        // format object with counts into expected object format for recharts Pie
        const data = Object.entries(counts)
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          .filter(([_, value]) => value > 0)
          .map(([level, value]) => ({
            name: level,
            value,
          }))
        const levelColor = theme.palette.evidence

        return (
          <Box id="evidence-level-container" display="flex" flexDirection="column">
            <Tooltip
              arrow
              followCursor
              enterDelay={100}
              title={
                <Box id="evidence-level-breakdown-tooltip">
                  {data.map((d) => (
                    <div key={d.name}>
                      {d.name}: {d.value}
                    </div>
                  ))}
                </Box>
              }
            >
              <Box
                sx={{
                  position: 'relative',
                  width: 40,
                  height: 40,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <PieChart width={40} height={40}>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={12}
                    outerRadius={20}
                    paddingAngle={2}
                    label={false}
                    animationDuration={200}
                  >
                    {data.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={levelColor[entry.name as EvidenceLevel]} />
                    ))}
                  </Pie>
                </PieChart>

                <Box
                  sx={{
                    position: 'absolute',
                    fontSize: 12,
                    fontWeight: 600,
                    pointerEvents: 'none', // this is so the cursor will remain the same on hover
                    color: theme.palette.text.primary,
                  }}
                >
                  {value?.evidence_level}
                </Box>
              </Box>
            </Tooltip>
            <Box sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
              {value.grouped_evidence.length}{' '}
              {`record${value.grouped_evidence.length > 1 ? 's' : ''}`}
            </Box>
          </Box>
        )
      },
    },
    {
      field: 'disease',
      headerName: 'Disease',
      width: 150,
      render: (value: NormalizedResult) => value?.disease,
    },
    {
      field: 'significance',
      headerName: 'Significance',
      width: 100,
      render: (value: NormalizedResult) => value?.significance,
    },
    {
      field: 'expandRow',
      headerName: '',
      width: 10,
      render: () => {
        return (
          <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        )
      },
    },
  ]

  // only add therapy column for Therapeutic Response tab
  if (resultType === 'therapeutic') {
    columns = [
      ...columns.slice(0, 3),
      {
        field: 'therapy',
        headerName: 'Therapy',
        width: 150,
        render: (value: NormalizedResult) => {
          const therapyData = value?.therapy
          if (!therapyData) return ''

          const { therapyNames, therapyInteractionType } = therapyData
          if (!therapyNames || therapyNames.length === 0) return ''

          const therapyList = therapyNames.join(', ')
          const prefix =
            therapyInteractionType !== TherapyInteractionType.None
              ? `${therapyInteractionType}: `
              : ''

          return `${prefix}${therapyList}`
        },
      },
      ...columns.slice(3),
    ]
  }

  const popperProps = {
    modifiers: [{ name: 'offset', options: { offset: [0, 8] } }],
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          {columns.map((column) => (
            <TableCell key={column.field} style={{ width: column.width }}>
              {column.field === 'evidence_summary' ? (
                <Box display="flex" alignItems="center" gap={0.75}>
                  {column.headerName}
                  <Tooltip
                    arrow
                    placement="top"
                    enterTouchDelay={0}
                    title={<EvidenceLegend />}
                    slotProps={{ popper: popperProps }}
                  >
                    <IconButton
                      size="small"
                      aria-label="Show evidence level legend"
                      sx={{ p: 0.25 }}
                    >
                      <HelpOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              ) : (
                column.headerName
              )}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((row, index) => (
          <ResultTableRow key={index} row={row} columns={columns} />
        ))}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            ActionsComponent={TablePaginationActions}
            count={results.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableRow>
      </TableFooter>
    </Table>
  )
}

export default ResultTable
