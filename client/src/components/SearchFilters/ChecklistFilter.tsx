import { useState } from 'react'
import { FormGroup, FormControlLabel, Checkbox, Button, TextField } from '@mui/material'
import FilterAccordion from './FilterAccordion'

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
    <FilterAccordion
      title={title}
      hasSelection={selected.length > 0}
      onClear={() => setSelected([])}
    >
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
    </FilterAccordion>
  )
}

export default ChecklistFilter
