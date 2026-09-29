import { useState } from 'react'
import {
  Box,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Button,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export interface ChecklistFilterProps<T> {
  // title of filter section
  title: string
  // complete options to select from
  options: T[]
  // stable key stored in selection state
  getOptionId: (option: T) => string
  // user-facing text for an option
  getOptionLabel: (option: T) => string
  // subset of options indicating what's selected by the user
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}

const ChecklistFilter = <T,>({
  title,
  options,
  getOptionId,
  getOptionLabel,
  selected,
  setSelected,
}: ChecklistFilterProps<T>) => {
  // we only show the top 5 filters at a time, so this tracks if the user clicked a button to show all or not
  const [showMore, setShowMore] = useState(false)
  const [search, setSearch] = useState('')

  const maxVisible = 5

  const filteredOptions = options.filter((opt) =>
    getOptionLabel(opt).toLowerCase().includes(search.toLowerCase()),
  )

  const visibleOptions = showMore ? filteredOptions : filteredOptions.slice(0, maxVisible)

  const toggleOption = (option: T, checked: boolean) => {
    const id = getOptionId(option)
    if (checked) setSelected([...selected, id])
    else setSelected(selected.filter((selectedId) => selectedId !== id))
  }

  return (
    <Accordion
      defaultExpanded={false}
      sx={{
        boxShadow: 'none',
        '&:before': { display: 'none' },
        '& .Mui-expanded': { margin: 0 },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          minHeight: 'unset !important',
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
          '& .MuiButtonBase-root': {
            padding: 0,
          },
          px: 0,
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
          <Typography fontWeight="bold">{title}</Typography>
          {selected.length > 0 && (
            <Button
              size="small"
              color="success"
              onClick={(e) => {
                e.stopPropagation()
                setSelected([])
              }}
            >
              clear
            </Button>
          )}
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        {/* Search box if more than 5 options */}
        {options.length > maxVisible && (
          <TextField
            size="small"
            placeholder={`Search ${title.toLowerCase()}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            fullWidth
            sx={{ mb: 1 }}
          />
        )}

        <FormGroup>
          {visibleOptions.map((opt) => (
            <FormControlLabel
              key={getOptionId(opt)}
              control={
                <Checkbox
                  checked={selected.includes(getOptionId(opt))}
                  onChange={(e) => toggleOption(opt, e.target.checked)}
                />
              }
              label={getOptionLabel(opt)}
            />
          ))}
        </FormGroup>

        {filteredOptions.length > maxVisible && (
          <Button size="small" onClick={() => setShowMore(!showMore)}>
            {showMore ? 'Show less' : 'Show more'}
          </Button>
        )}
      </AccordionDetails>
    </Accordion>
  )
}

export default ChecklistFilter
