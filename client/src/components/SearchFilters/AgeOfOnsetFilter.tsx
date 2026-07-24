import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { AGE_OF_ONSET_TERMS, getParentIds, getTermAndChildrenIds } from '../../utils/ageOfOnset'

export interface AgeOfOnsetFilterProps {
  // literal age-of-onset options to select from
  options: string[]
  // subset of options indicating what's selected by the user
  selected: string[]
  // setter to set selections
  setSelected: (values: string[]) => void
}

const getChildTermIds = (parentId: string): string[] =>
  Object.values(AGE_OF_ONSET_TERMS)
    .filter((term) => term.parentConceptId === parentId)
    .map((term) => term.conceptId)

const AgeOfOnsetFilter = ({ selected, setSelected }: AgeOfOnsetFilterProps) => {
  const handleChange = (termId: string, checked: boolean) => {
    const affectedIds = getTermAndChildrenIds(termId)

    if (checked) {
      setSelected([...new Set([...selected, ...affectedIds])])
    } else {
      setSelected(selected.filter((selectedId) => !affectedIds.includes(selectedId)))
    }
  }

  const renderTerm = (termId: string, depth = 0) => {
    const term = AGE_OF_ONSET_TERMS[termId]
    const childIds = getChildTermIds(termId)
    const affectedIds = getTermAndChildrenIds(termId)

    const selectedChildCount = affectedIds.filter((id) => selected.includes(id)).length
    const checked = affectedIds.every((id) => selected.includes(id))
    const indeterminate = selectedChildCount > 0 && !checked

    return (
      <Box key={termId}>
        <FormControlLabel
          sx={{ ml: depth * 2 }}
          control={
            <Checkbox
              checked={checked}
              indeterminate={indeterminate}
              onChange={(event) => handleChange(termId, event.target.checked)}
            />
          }
          label={term.name}
        />

        {childIds.map((childId) => renderTerm(childId, depth + 1))}
      </Box>
    )
  }
  console.log(getParentIds())
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

      <AccordionDetails sx={{ px: 0 }}>
        {getParentIds().map((termId) => renderTerm(termId))}
      </AccordionDetails>
    </Accordion>
  )
}

export default AgeOfOnsetFilter
