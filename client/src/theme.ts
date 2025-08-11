import { createTheme, ThemeOptions } from '@mui/material/styles';

// theme.d.ts (or at the top of theme.ts if you're not splitting files)
import { PaletteColorOptions, PaletteColor } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    header: PaletteColor;
  }
  interface PaletteOptions {
    header?: PaletteColorOptions;
  }
}

declare module '@mui/material/AppBar' {
  interface AppBarPropsColorOverrides {
    header: true;
  }
}

export const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#268669',
    },
    secondary: {
      main: '#A1D044',
    },
    header: {
      main: '#18252B',
      contrastText: '#FFFFFF',
    },
  },
};

const theme = createTheme(themeOptions);

export default theme;
