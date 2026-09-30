import { Box, Checkbox, FormControlLabel, FormGroup } from '@mui/material'
import type { MappableConcept } from '../../models/domain'
import { getDiseaseTissueGroups } from '../../utils/oncotree'
import FilterAccordion from './FilterAccordion'

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
    <FilterAccordion
      title="Disease"
      hasSelection={selected.length > 0}
      onClear={() => onChange([])}
    >
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
                        onChange={(event) => handleDiseaseChange(disease.id, event.target.checked)}
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
    </FilterAccordion>
  )
}

export default DiseaseFilter
