import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export interface AgeOfOnsetFilterProps {
  // literal options to select from (eg disease names, star ratings, etc)
  options: string[]
  // subset of options indicating what's selected by the user
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}

const AgeOfOnsetFilter = ({ selected, setSelected }: AgeOfOnsetFilterProps) => {
  return (
    <Accordion
      defaultExpanded
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        backgroundColor: 'transparent',
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          minHeight: 'unset !important',
          px: 0,
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
          <Typography fontWeight="bold">Age of Onset</Typography>

          {selected.length > 0 && (
            <Button
              size="small"
              color="success"
              onClick={(event) => {
                event.stopPropagation()
                setSelected([])
              }}
            >
              Clear
            </Button>
          )}
        </Box>
      </AccordionSummary>

      <AccordionDetails sx={{ px: 0 }}>lksdfjklsdf</AccordionDetails>
    </Accordion>
  )
}

export default AgeOfOnsetFilter
