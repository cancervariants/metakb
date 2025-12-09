import { AppBar, Box, Toolbar, Typography } from '@mui/material'
import { Link } from 'react-router-dom'

const Header = () => {
  return (
    <AppBar position="static" color="header" sx={{ padding: 2 }}>
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            <Typography variant="h4" fontWeight="bold" color="white">
              MetaKB Jr.
            </Typography>
          </Link>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
