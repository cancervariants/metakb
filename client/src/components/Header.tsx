import { AppBar, Box, Toolbar } from '@mui/material'
import { Link } from 'react-router-dom'
import metakbJrLogo from '../assets/metakbjr-logo.png'

const Header = () => {
  return (
    <AppBar position="static" color="header">
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            <Box
              component="img"
              src={metakbJrLogo}
              alt="MetaKB Jr."
              sx={{ height: 75, width: 'auto', display: 'block', padding: 1}}
            />
          </Link>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
