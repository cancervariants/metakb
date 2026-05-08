import { useEffect, useState } from 'react'
import { Box, IconButton, Toolbar, Typography } from '@mui/material'
import GitHubIcon from '@mui/icons-material/GitHub'
import theme from '../theme'
import ContentContainer from './common/ContentContainer'

const Footer = () => {
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
    <Box
      component="footer"
      sx={{
        py: 2,
        textAlign: 'center',
        width: '100%',
        bgcolor: theme.palette.footer.main,
      }}
    >
      <ContentContainer>
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Box display="flex" alignItems="center" gap={2}>
            {version && (
              <Typography variant="body2" color="white" sx={{ opacity: 0.8 }}>
                {version ? `MetaKB version ${version}` : 'version ?'}
                {environment && environment != 'prod' ? ` [${environment}]` : ''}
              </Typography>
            )}
          </Box>

          <IconButton
            component="a"
            href="https://github.com/cancervariants/metakb"
            target="_blank"
            rel="noopener noreferrer"
            color="secondary"
            disableRipple
            sx={{
              '&:hover': {
                color: 'white',
              },
            }}
          >
            {' '}
            <Box display="flex" alignItems="center" gap={1}>
              <GitHubIcon fontSize="large" />
              <Typography fontWeight="bold">GitHub</Typography>
            </Box>
          </IconButton>
        </Toolbar>
      </ContentContainer>
    </Box>
  )
}

export default Footer
