import * as React from 'react'
import { useState, MouseEvent, FC } from 'react'
import {
  Box,
  Collapse,
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
  results: any[]
}

const ResultTable: FC<ResultTableProps> = ({ results }) => {
  const [open, setOpen] = useState(false)

  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)

  function handleChangePage(event: any, newpage: any) {
    setPage(newpage)
  }

  function handleChangeRowsPerPage(event: any) {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const columns = [
    { field: 'id', headerName: 'ID', width: 90 },
    {
      field: 'variant',
      headerName: 'Variant',
      width: 150,
      render: (value: any) => value?.proposition?.subjectVariant?.name,
    },
    {
      field: 'evidence_level',
      headerName: 'Evidence Level',
      width: 150,
      render: (value: any) => value?.strength?.primaryCoding?.code,
    },
    {
      field: 'disease',
      headerName: 'Disease',
      width: 150,
      render: (value: any) =>
        value?.proposition?.conditionQualifier?.name || value?.proposition?.objectCondition?.name,
    },
    {
      field: 'significance',
      headerName: 'Significance',
      width: 150,
      render: (value: any) => value?.proposition?.predicate,
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

  console.log(results)
  result = [
    {
      variant_name: 'BRAF V600E',
      evidence_level: 'Level A',
      disease: 'Melanoma',
      significance: 'Predictive',
      description: 'This is a description of the evidence item.',
      grouped_evidence: [
        // the array here
      ]
    }
  ]
  

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
        {results.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((row) => (
          <>
            <TableRow key={row.id}>
              {columns.map((column) => {
                const value = column.render ? column.render(row) : row[column.field]
                return (
                  <TableCell key={column.field} style={{ width: column.width }}>
                    {value}
                  </TableCell>
                )
              })}
            </TableRow>
            <TableRow>
              <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                <Collapse in={open} timeout="auto" unmountOnExit>
                  {row?.description}
                </Collapse>
              </TableCell>
            </TableRow>
          </>
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
