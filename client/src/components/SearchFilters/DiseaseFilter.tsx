import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Typography,
} from '@mui/material'
import type { MappableConcept } from '../../models/domain'
import { getDiseaseTissueGroups } from '../../utils/oncotree'

export interface DiseaseFilterProps {
  diseases: MappableConcept[]
  selected: string[]
  onChange: (selected: string[]) => void
}

const DiseaseFilter = ({ diseases, selected, onChange }: DiseaseFilterProps) => {
  const tissueGroups = getDiseaseTissueGroups(diseases)

  const handleDiseaseChange = (diseaseId: string, checked: boolean) => {
    onChange(checked ? [...selected, diseaseId] : selected.filter((id) => id !== diseaseId))
  }

  const handleTissueChange = (diseaseIds: string[], checked: boolean) => {
    onChange(
      checked
        ? [...new Set([...selected, ...diseaseIds])]
        : selected.filter((id) => !diseaseIds.includes(id)),
    )
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
          '& .MuiAccordionSummary-content': { margin: 0 },
          '& .MuiButtonBase-root': { padding: 0 },
          px: 0,
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
          <Typography fontWeight="bold">Disease</Typography>
          {selected.length > 0 && (
            <Button
              size="small"
              color="success"
              onClick={(event) => {
                event.stopPropagation()
                onChange([])
              }}
            >
              clear
            </Button>
          )}
        </Box>
      </AccordionSummary>

      <AccordionDetails sx={{ px: 0 }}>
        <FormGroup>
          {tissueGroups.map((group) => {
            const diseaseIds = group.diseases.map((disease) => disease.id)
            const selectedCount = diseaseIds.filter((id) => selected.includes(id)).length
            const checked = diseaseIds.length > 0 && selectedCount === diseaseIds.length
            const indeterminate = selectedCount > 0 && !checked

            return (
              <Box key={group.code}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={checked}
                      indeterminate={indeterminate}
                      onChange={(event) => handleTissueChange(diseaseIds, event.target.checked)}
                    />
                  }
                  label={group.name}
                />

                <Box sx={{ ml: 2 }}>
                  {group.diseases.map((disease) => (
                    <FormControlLabel
                      key={`${group.code}-${disease.id}`}
                      control={
                        <Checkbox
                          checked={selected.includes(disease.id)}
                          onChange={(event) =>
                            handleDiseaseChange(disease.id, event.target.checked)
                          }
                        />
                      }
                      label={disease.name ?? disease.id}
                    />
                  ))}
                </Box>
              </Box>
            )
          })}
        </FormGroup>
      </AccordionDetails>
    </Accordion>
  )
}

export default DiseaseFilter
