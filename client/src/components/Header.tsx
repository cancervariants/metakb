import { useEffect, useState } from 'react'
import { AppBar, Box, IconButton, Toolbar, Typography } from '@mui/material'
import { Link } from 'react-router-dom'
import GitHubIcon from '@mui/icons-material/GitHub'

const Header = () => {
  const [version, setVersion] = useState('')
  const [environment, setEnvironment] = useState('')

  useEffect(() => {
    const run = async () => {
      const url = '/api/service-info'
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
      })
      if (!res.ok) throw new Error(`Service info API request failed: ${res.status}`)
      const data = await res.json()
      setVersion(data.version)
      setEnvironment(data.environment)
    }
    run()
  }, [])

  return (
    <AppBar position="static" color="header" sx={{ padding: 2 }}>
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
            <Typography variant="h4" fontWeight="bold" color="white">
              MetaKB
            </Typography>
          </Link>
          {version && (
            <Typography variant="body2" color="white" sx={{ opacity: 0.8 }}>
              {version ? `version ${version}` : 'version ?'}
              {environment && environment != 'prod' ? ` [${environment}]` : ''}
            </Typography>
          )}
        </Box>

        <IconButton
          component="a"
          href="https://github.com/cancervariants/metakb"
          target="_blank"
          rel="noopener noreferrer"
          color="inherit"
        >
          {' '}
          <Box display="flex" alignItems="center" gap={1}>
            <GitHubIcon fontSize="large" />
            <Typography>Visit us on GitHub!</Typography>
          </Box>
        </IconButton>
      </Toolbar>
    </AppBar>
  )
}

export default Header
