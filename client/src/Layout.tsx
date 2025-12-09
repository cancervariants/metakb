// Layout component for providing the header and footer and a full-height container for every page
import { Box } from '@mui/material'
import Header from './components/Header'
import Footer from './components/Footer'
import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />

      <Box component="main" sx={{ flexGrow: 1 }}>
        <Outlet />
      </Box>

      <Footer />
    </Box>
  )
}
