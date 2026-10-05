import type { ReactNode } from 'react'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export interface FilterAccordionProps {
  title: string
  hasSelection: boolean
  onClear: () => void
  children: ReactNode
}

const FilterAccordion = ({ title, hasSelection, onClear, children }: FilterAccordionProps) => {
  return (
    <Accordion
      defaultExpanded={false}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        backgroundColor: 'transparent',
      }}
      disableGutters
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          minHeight: 'unset !important',
          px: 0,
          '& .MuiAccordionSummary-content': { margin: 0 },
          '&.Mui-expanded': { margin: 0 },
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
          <Typography fontWeight="bold">{title}</Typography>
          {hasSelection && (
            <Button
              size="small"
              color="success"
              onClick={(event) => {
                event.stopPropagation()
                onClear()
              }}
            >
              Clear
            </Button>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>{children}</AccordionDetails>
    </Accordion>
  )
}

export default FilterAccordion
