import { useState, MouseEvent, FC } from 'react'
import {
  Box,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TablePagination,
  TableRow,
  useTheme,
} from '@mui/material'
import FirstPageIcon from '@mui/icons-material/FirstPage'
import KeyboardArrowLeft from '@mui/icons-material/KeyboardArrowLeft'
import KeyboardArrowRight from '@mui/icons-material/KeyboardArrowRight'
import LastPageIcon from '@mui/icons-material/LastPage'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import ResultTableRow from './CollapsibleResult'
import { NormalizedResult } from '../pages/Results/utils'
import { ResultColumn } from './utils'

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
  results: NormalizedResult[]
  resultType: string
}

const ResultTable: FC<ResultTableProps> = ({ results, resultType }) => {
  const [open, setOpen] = useState(false)

  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  function handleChangePage(event: React.MouseEvent<HTMLButtonElement> | null, newpage: number) {
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
      field: 'variant_name',
      headerName: 'Variant',
      width: 150,
      render: (value: NormalizedResult) => value?.variant_name,
    },
    {
      field: 'evidence_level',
      headerName: 'Evidence Level',
      width: 150,
      render: (value: NormalizedResult) => value?.evidence_level,
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
      width: 150,
      render: (value: NormalizedResult) => value?.significance,
    },
    {
      field: 'resultCount',
      headerName: 'Records',
      width: 150,
      render: (value: NormalizedResult) => {
        return value?.grouped_evidence.length
      },
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
        render: (value: NormalizedResult) => value?.therapy,
      },
      ...columns.slice(3),
    ]
  }

  return (
    <Table>
      <TableHead>
        <TableRow>
          {columns.map((column) => (
            <TableCell key={column.field} style={{ width: column.width }}>
              {column.headerName}
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
