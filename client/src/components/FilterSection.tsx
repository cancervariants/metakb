import { Checkbox, FormControlLabel, FormGroup } from '@mui/material'
import * as React from 'react'
import { useState, MouseEvent, FC } from 'react'

interface FilterSectionProps {
  title: string
  options: any[]
  selected: any[]
  setSelected: (event: MouseEvent<HTMLButtonElement>, newPage: number) => void
}

const FilterSection = ({ title, options, selected, setSelected }) => {
  return (
    <div style={{ marginBottom: 16 }}>
      <strong>{title}</strong>
      <FormGroup>
        {options.map((opt) => (
          <FormControlLabel
            key={opt}
            control={
              <Checkbox
                checked={selected.includes(opt)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelected([...selected, opt])
                  } else {
                    setSelected(selected.filter((x) => x !== opt))
                  }
                }}
              />
            }
            label={opt}
          />
        ))}
      </FormGroup>
    </div>
  )
}

export default FilterSection
