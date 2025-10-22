import { useEffect, useState } from 'react'
import { AppBar, Typography } from '@mui/material'
import { Link } from 'react-router-dom'

const Header = () => {
  const [version, setVersion] = useState('')
  const [environment, setEnvironment] = useState('')

  useEffect(() => {
    const run = async () => {
      const url = '/api/v2/service-info'
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
      <Link to="/">
        <Typography variant="h4" fontWeight="bold" color="white">
          MetaKB
        </Typography>
      </Link>
      <Typography>
        {version ? `version ${version}` : 'version ?'}
        {environment && environment != 'prod' ? ` [${environment}]` : ''}
      </Typography>
    </AppBar>
  )
}

export default Header
