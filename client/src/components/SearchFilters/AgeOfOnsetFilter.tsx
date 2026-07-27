import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
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
import { AGE_OF_ONSET_TERMS, getParentIds, getTermAndChildrenIds } from '../../utils/ageOfOnset'

export type AgeOfOnsetSelection = {
  conceptIds: string[]
  includeNotSpecified: boolean
}

export interface AgeOfOnsetFilterProps {
  // Literal age-of-onset concept ID options present in the results.
  // TODO: use this to hide unused options.
  options: string[]

  // Current age-of-onset filter selection.
  value: AgeOfOnsetSelection

  // Update the age-of-onset filter selection.
  onChange: (value: AgeOfOnsetSelection) => void
}

const getChildTermIds = (parentId: string): string[] =>
  Object.values(AGE_OF_ONSET_TERMS)
    .filter((term) => term.parentConceptId === parentId)
    .map((term) => term.conceptId)

const AgeOfOnsetFilter = ({ options, value, onChange }: AgeOfOnsetFilterProps) => {
  const { conceptIds, includeNotSpecified } = value

  const optionIds = new Set(options)

  /**
   * Return whether the given term or any descendant is present in the
   * available age-of-onset options.
   */
  const branchHasOptions = (termId: string): boolean =>
    getTermAndChildrenIds(termId).some((id) => optionIds.has(id))

  const visibleRootIds = getParentIds().filter(branchHasOptions)

  const visibleConceptIds = Object.keys(AGE_OF_ONSET_TERMS).filter((id) => optionIds.has(id))

  const handleConceptIdsChange = (nextConceptIds: string[]) => {
    onChange({
      ...value,
      conceptIds: nextConceptIds,
    })
  }

  const handleNotSpecifiedChange = (nextIncludeNotSpecified: boolean) => {
    onChange({
      ...value,
      includeNotSpecified: nextIncludeNotSpecified,
    })
  }

  const handleTermChange = (termId: string, checked: boolean) => {
    const affectedIds = getTermAndChildrenIds(termId).filter((id) => optionIds.has(id))

    if (checked) {
      handleConceptIdsChange([...new Set([...conceptIds, ...affectedIds])])
      return
    }

    handleConceptIdsChange(conceptIds.filter((selectedId) => !affectedIds.includes(selectedId)))
  }

  const handleSpecifiedChange = (checked: boolean) => {
    handleConceptIdsChange(checked ? visibleConceptIds : [])
  }

  const specifiedChecked =
    visibleConceptIds.length > 0 && visibleConceptIds.every((id) => conceptIds.includes(id))

  const specifiedIndeterminate =
    visibleConceptIds.some((id) => conceptIds.includes(id)) && !specifiedChecked

  const hasSelection = conceptIds.length > 0 || includeNotSpecified

  const renderTerm = (termId: string, depth = 0) => {
    if (!branchHasOptions(termId)) {
      return null
    }

    const term = AGE_OF_ONSET_TERMS[termId]

    const childIds = getChildTermIds(termId).filter(branchHasOptions)

    const affectedIds = getTermAndChildrenIds(termId).filter((id) => optionIds.has(id))

    const selectedCount = affectedIds.filter((id) => conceptIds.includes(id)).length

    const checked = affectedIds.length > 0 && affectedIds.every((id) => conceptIds.includes(id))

    const indeterminate = selectedCount > 0 && !checked

    return (
      <Box key={termId}>
        <FormControlLabel
          sx={{ ml: depth * 2 }}
          control={
            <Checkbox
              checked={checked}
              indeterminate={indeterminate}
              onChange={(event) => handleTermChange(termId, event.target.checked)}
            />
          }
          label={term.name}
        />

        {childIds.map((childId) => renderTerm(childId, depth + 1))}
      </Box>
    )
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
          <Typography fontWeight="bold">Age of Onset</Typography>

          {hasSelection && (
            <Button
              size="small"
              color="success"
              onClick={(event) => {
                event.stopPropagation()
                onChange({
                  conceptIds: [],
                  includeNotSpecified: false,
                })
              }}
            >
              Clear
            </Button>
          )}
        </Box>
      </AccordionSummary>

      <AccordionDetails sx={{ px: 0 }}>
        {visibleRootIds.length > 0 && (
          <>
            <FormControlLabel
              control={
                <Checkbox
                  checked={specifiedChecked}
                  indeterminate={specifiedIndeterminate}
                  onChange={(event) => handleSpecifiedChange(event.target.checked)}
                />
              }
              label="Age of onset specified"
            />

            <Box sx={{ ml: 2 }}>{visibleRootIds.map((termId) => renderTerm(termId))}</Box>
          </>
        )}

        <FormControlLabel
          control={
            <Checkbox
              checked={includeNotSpecified}
              onChange={(event) => handleNotSpecifiedChange(event.target.checked)}
            />
          }
          label="Age of onset not specified"
        />
      </AccordionDetails>
    </Accordion>
  )
}

export default AgeOfOnsetFilter
