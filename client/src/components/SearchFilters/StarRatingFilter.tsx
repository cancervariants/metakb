import { useState } from 'react'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  IconButton,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import StarIcon from '@mui/icons-material/Star'
import StarBorderIcon from '@mui/icons-material/StarBorder'

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
    setSelected(RATINGS.filter((rating) => Number(rating) >= Number(minimumRating)))
  }

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
          <Typography fontWeight="bold">Star Rating</Typography>

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
        <Box
          display="flex"
          alignItems="center"
          onMouseLeave={() => setHoveredRating(null)}
          paddingTop="8px"
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
                onBlur={() => setHoveredRating(null)}
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
      </AccordionDetails>
    </Accordion>
  )
}

export default StarRatingFilter
