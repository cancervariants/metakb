import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import FilterAccordion from './FilterAccordion'

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
    <FilterAccordion
      title="Evidence Level"
      hasSelection={selected.length > 0}
      onClear={() => setSelected([])}
    >
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
    </FilterAccordion>
  )
}

export default EvidenceLevelFilter
