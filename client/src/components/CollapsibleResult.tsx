import { useState, FC } from 'react'
import {
  Box,
  Collapse,
  IconButton,
  TableCell,
  TableRow,
} from '@mui/material'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'


const ResultTableRow: FC<{ row: any; columns: any[] }> = ({ row, columns }) => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <TableRow>
        {columns.map((column) => (
          <TableCell key={column.field}>
            {column.field === "expandRow" ? (
              <IconButton onClick={() => setOpen(!open)}>
                {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
              </IconButton>
            ) : column.render ? column.render(row) : row[column.field]}
          </TableCell>
        ))}
      </TableRow>
      <TableRow>
        <TableCell colSpan={columns.length} style={{ paddingBottom: 0, paddingTop: 0 }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            {row.grouped_evidence.map((e: any) => (
              <Box key={e.id} margin={1} sx={{ border: "1px solid #ccc", mb: 2, p: 2 }}>
                <div><strong>Evidence ID:</strong> {e.id}</div>
                <div><strong>Description:</strong> {e.description}</div>
              </Box>
            ))}
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  )
}

export default ResultTableRow

