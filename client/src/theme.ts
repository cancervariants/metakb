import { createTheme, ThemeOptions } from '@mui/material/styles'
import { PaletteColorOptions, PaletteColor } from '@mui/material/styles'

declare module '@mui/material/styles' {
  interface Palette {
    header: PaletteColor
    footer: PaletteColor
    evidence: Record<'A' | 'B' | 'C' | 'D' | 'E', string>
  }
  interface PaletteOptions {
    header?: PaletteColorOptions
    footer?: PaletteColorOptions
    evidence?: Partial<Record<'A' | 'B' | 'C' | 'D' | 'E', string>>
  }
}

declare module '@mui/material/AppBar' {
  interface AppBarPropsColorOverrides {
    header: true
  }
}

export const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: { main: '#268669' },
    secondary: { main: '#A1D044' },
    header: {
      main: '#18252B',
      contrastText: '#FFFFFF',
    },
    footer: {
      main: '#7E7E7E',
      contrastText: '#FFFFFF',
    },
    evidence: {
      A: '#1f77b4', // blue
      B: '#2ca02c', // green
      C: '#f1c40f', // yellow
      D: '#ff7f0e', // orange
      E: '#d62728', // red
    },
  },
}

const theme = createTheme(themeOptions)
export default theme
