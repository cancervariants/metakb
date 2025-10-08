import React, { useEffect, useState } from 'react'
import { AppBar, Typography } from '@mui/material'
import { Link } from 'react-router-dom'
import { fetchVersion } from '../utils/'

const Header = () => {
  const [version, setVersion] = useState('')

  useEffect(() => {
    fetchVersion().then((versionResponse) => {
      setVersion(versionResponse)
    })
  }, [])

  return (
    <AppBar position="static" color="header" sx={{ padding: 2 }}>
      <Link to="/">
        <Typography variant="h4" fontWeight="bold" color="white">
          MetaKB
        </Typography>
      </Link>
      <Typography>{version}</Typography>
    </AppBar>
  )
}

export default Header
