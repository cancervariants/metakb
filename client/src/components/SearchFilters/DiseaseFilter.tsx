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
import { getAvailableDiseaseTissues } from '../../utils/oncotree'

export interface DiseaseFilterProps {
  diseases: MappableConcept[]
  selected: string[]
  onChange: (selected: string[]) => void
}

const DiseaseFilter = ({ diseases, selected, onChange }: DiseaseFilterProps) => {
  const tissues = getAvailableDiseaseTissues(diseases)

  const handleTissueChange = (tissueCode: string, checked: boolean) => {
    onChange(checked ? [...selected, tissueCode] : selected.filter((code) => code !== tissueCode))
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
          {tissues.map((tissue) => (
            <FormControlLabel
              key={tissue.code}
              control={
                <Checkbox
                  checked={selected.includes(tissue.code)}
                  onChange={(event) => handleTissueChange(tissue.code, event.target.checked)}
                />
              }
              label={tissue.name}
            />
          ))}
        </FormGroup>
      </AccordionDetails>
    </Accordion>
  )
}

export default DiseaseFilter
