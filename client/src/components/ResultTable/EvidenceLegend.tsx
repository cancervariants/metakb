import React from 'react'
import { Box, Typography } from '@mui/material'
import { LegendSwatch } from './LegendSwatch'
import { useTheme } from '@mui/material/styles'

export const EvidenceLegend: React.FC = () => {
  const theme = useTheme()
  const evidence = theme.palette.evidence

  return (
    <Box
      component="ul"
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 2,
        p: 0,
        m: 0,
        listStyle: 'none',
      }}
      aria-label="Evidence level color key"
    >
      <Typography>Key: </Typography>
      <LegendSwatch color={evidence.A} label="A" description="Authoritative" />
      <LegendSwatch color={evidence.B} label="B" description="Clinical Cohort" />
      <LegendSwatch color={evidence.C} label="C" description="Observation / Case Study" />
      <LegendSwatch color={evidence.D} label="D" description="Preclinical" />
      <LegendSwatch color={evidence.E} label="E" description="Inferential" />
    </Box>
  )
}
