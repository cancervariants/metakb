import { useState } from 'react'
import { Box, FormGroup, FormControlLabel, Checkbox, Button, TextField } from '@mui/material'

interface FilterSectionProps {
  title: string
  options: string[]
  selected: string[]
  setSelected: (values: string[]) => void
}

const FilterSection = ({ title, options, selected, setSelected }: FilterSectionProps) => {
  const [expanded, setExpanded] = useState(false)
  const [search, setSearch] = useState('')

  const maxVisible = 5

  // Filter options by search text (case-insensitive)
  const filteredOptions = options.filter((opt) => opt.toLowerCase().includes(search.toLowerCase()))

  const visibleOptions = expanded ? filteredOptions : filteredOptions.slice(0, maxVisible)

  const toggleOption = (opt: string, checked: boolean) => {
    if (checked) {
      setSelected([...selected, opt])
    } else {
      setSelected(selected.filter((x) => x !== opt))
    }
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <strong>{title}</strong>
        {selected.length > 0 && (
          <Button size="small" onClick={() => setSelected([])} color="success">
            clear
          </Button>
        )}
      </Box>

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
        <Button size="small" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Show less' : 'Show more'}
        </Button>
      )}
    </div>
  )
}

export default FilterSection
