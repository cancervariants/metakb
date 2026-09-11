import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export interface EvidenceLevelFilterProps {
  // literal evidence level options to select from ('A', 'B', etc)
  options: string[]
  // subset of options indicating what should be shown to the user
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}

const LEVELS = ['A', 'B', 'C', 'D']

const EvidenceLevelFilter = ({ options, selected, setSelected }: EvidenceLevelFilterProps) => {
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
          <Typography fontWeight="bold">Evidence Level</Typography>

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

      <AccordionDetails sx={{ px: 0 }}>
        <Box display="flex" alignItems="center" justifyContent="center" paddingTop="8px">
          <ToggleButtonGroup
            value={selected}
            onChange={(_event, newOptions) => setSelected(newOptions)}
          >
            {LEVELS.map((level) => (
              <ToggleButton key={level} value={level} disabled={!options.includes(level)}>
                <Typography sx={{ fontWeight: 'bold' }}>{level}</Typography>
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>
      </AccordionDetails>
    </Accordion>
  )
}

export default EvidenceLevelFilter
