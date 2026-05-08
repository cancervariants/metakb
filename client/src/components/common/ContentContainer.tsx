/**
 * Shared layout container that constrains content width,
 * centers content horizontally, and applies consistent
 * horizontal padding across the application.
 *
 * Used to keep top/bottom bar (header/footer) + main content
 * aligned to the same visual grid while allowing outer
 * page backgrounds to remain full-width.
 */
import { Box, BoxProps } from '@mui/material'

export default function ContentContainer(props: BoxProps) {
  return (
    <Box
      {...props}
      sx={{
        width: '100%',
        maxWidth: 1350,
        mx: 'auto',
        px: 3,
        ...props.sx,
      }}
    />
  )
}
