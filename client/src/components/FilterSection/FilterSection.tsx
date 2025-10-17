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

interface FilterSectionProps {
  title: string
  options: string[]
  selected: string[]
  setSelected: (values: string[]) => void
}

const FilterSection = ({ title, options, selected, setSelected }: FilterSectionProps) => {
  // expand/collapse value for accordion for filter section
  const [expanded, setExpanded] = useState(true)
  // we only show the top 5 filters at a time, so this tracks if the user clicked a button to show all or not
  const [showMore, setShowMore] = useState(false)
  const [search, setSearch] = useState('')

  const maxVisible = 5

  const filteredOptions = options.filter((opt) => opt.toLowerCase().includes(search.toLowerCase()))

  const visibleOptions = showMore ? filteredOptions : filteredOptions.slice(0, maxVisible)

  const toggleOption = (opt: string, checked: boolean) => {
    if (checked) setSelected([...selected, opt])
    else setSelected(selected.filter((x) => x !== opt))
  }

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
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
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
          '& .MuiButtonBase-root': {
            padding: 0,
          },
          px: 0, // remove horizontal padding
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
              key={opt}
              control={
                <Checkbox
                  checked={selected.includes(opt)}
                  onChange={(e) => toggleOption(opt, e.target.checked)}
                />
              }
              label={opt}
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

export default FilterSection
