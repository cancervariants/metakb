import { AppBar, Typography } from '@mui/material'
import { Link } from 'react-router-dom'

const Header = () => {
  return (
    <AppBar position="static" color="header" sx={{ padding: 2 }}>
      <Link to="/">
        <Typography variant="h4" fontWeight="bold" color="white">
        MetaKB
      </Typography></Link>
    </AppBar>
  )
}

export default Header
