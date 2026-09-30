import { useState } from 'react'
import { Box, IconButton, Typography } from '@mui/material'
import StarIcon from '@mui/icons-material/Star'
import StarBorderIcon from '@mui/icons-material/StarBorder'
import FilterAccordion from './FilterAccordion'

export interface StarRatingFilterProps {
  // literal star rating options to select from ('1', '2', etc)
  options: string[]
  // subset of options indicating what should be shown to the user
  // note that this is interpreted as a minimum: if a user
  // selects '2', the setter function will fire with ['2', '3', '4']
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}

const RATINGS = ['1', '2', '3', '4']

const StarRatingFilter = ({ selected, setSelected }: StarRatingFilterProps) => {
  const [hoveredRating, setHoveredRating] = useState<string | null>(null)

  const selectedThreshold = selected.length > 0 ? Math.min(...selected.map(Number)) : null

  const displayedThreshold = hoveredRating !== null ? Number(hoveredRating) : selectedThreshold

  const selectMinimumRating = (minimumRating: string) => {
    if (selectedThreshold === Number(minimumRating)) {
      setSelected([])
      return
    }

    setSelected(RATINGS.filter((rating) => Number(rating) >= Number(minimumRating)))
  }

  return (
    <FilterAccordion
      title="Star Rating"
      hasSelection={selected.length > 0}
      onClear={() => setSelected([])}
    >
      <Box
        display="flex"
        alignItems="center"
        onMouseLeave={() => setHoveredRating(null)}
        paddingTop="8px"
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) {
            setHoveredRating(null)
          }
        }}
      >
        {RATINGS.map((rating) => {
          const numericRating = Number(rating)

          const isActive = displayedThreshold !== null && numericRating <= displayedThreshold

          const isHoverPreview = hoveredRating !== null && isActive

          return (
            <IconButton
              key={rating}
              size="small"
              aria-label={`Filter by ${rating}`}
              onMouseEnter={() => setHoveredRating(rating)}
              onFocus={() => setHoveredRating(rating)}
              onClick={() => selectMinimumRating(rating)}
              sx={{
                color: isHoverPreview
                  ? 'text.secondary'
                  : isActive
                    ? 'warning.main'
                    : 'action.disabled',
              }}
            >
              {isActive ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
          )
        })}
        <Typography sx={{ transform: 'translate(5px, 1px)' }}>& up</Typography>
      </Box>
    </FilterAccordion>
  )
}

export default StarRatingFilter
