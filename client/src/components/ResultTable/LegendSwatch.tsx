import React from 'react'
import { Box, Typography } from '@mui/material'

interface LegendSwatchProps {
  // the color for the swatch
  color: string
  //   the label to associate the color with
  label: string
  //   additional data/description to put next to the label
  description?: string
}

export const LegendSwatch: React.FC<LegendSwatchProps> = ({ color, label, description }) => (
  <Box
    component="li"
    sx={{
      display: 'flex',
      alignItems: 'center',
      gap: 1,
      listStyle: 'none',
    }}
    role="listitem"
  >
    <Box
      sx={{
        width: 12,
        height: 12,
        borderRadius: '50%',
        backgroundColor: color,
        border: '1px solid rgba(0,0,0,0.2)',
        flexShrink: 0,
      }}
      aria-hidden="true"
    />
    <Typography variant="body2" sx={{ fontWeight: 500 }}>
      {label}
    </Typography>
    {description && (
      <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }} aria-label={description}>
        {description}
      </Typography>
    )}
  </Box>
)
