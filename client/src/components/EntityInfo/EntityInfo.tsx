import { Box, Typography } from '@mui/material'
import { CategoricalVariant, MappableConcept } from '../../models/domain'
import GeneInfo from './GeneInfo'
import VariationInfo from './VariationInfo'

type InfoRowProps = {
  label: string
  children: React.ReactNode
  show?: boolean
}

export const InfoRow = ({ label, children, show = true }: InfoRowProps) => {
  if (!show) return null

  return (
    <Box display="flex">
      <Box sx={{ width: 160, flexShrink: 0 }}>
        <Typography fontWeight="bold">{label}</Typography>
      </Box>
      <Box flex={1}>{children}</Box>
    </Box>
  )
}

type EntityInfoProps =
  | { type: 'gene'; data: MappableConcept }
  | { type: 'variant'; data: CategoricalVariant }

export const EntityInfo = (props: EntityInfoProps) => {
  switch (props.type) {
    case 'gene':
      return <GeneInfo data={props.data} />
    case 'variant':
      return <VariationInfo data={props.data} />
  }
}
