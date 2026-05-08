import { useEffect, useState } from 'react'
import { Box, Link, Typography } from '@mui/material'
import theme from '../theme'
import ContentContainer from './common/ContentContainer'
import { Link as RouterLink } from 'react-router-dom'

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

  const footerTextSx = { opacity: 0.8, flexShrink: 0 }
  return (
    <Box
      component="footer"
      sx={{
        py: 2,
        width: '100%',
        bgcolor: theme.palette.footer.main,
      }}
    >
      <ContentContainer>
        <Box
          px={3}
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 4,
          }}
        >
          {/* Column 1: Application meta */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="body1" color="white" sx={{ ...footerTextSx, flexShrink: 0 }}>
              {`MetaKB ${version ?? '?'}`}
              {environment && environment !== 'prod' ? ` [${environment}]` : ''}
            </Typography>
            <Typography variant="body2" color="white" sx={footerTextSx}>
              <Link
                href="https://github.com/cancervariants/metakb/releases"
                target="_blank"
                rel="noopener noreferrer"
                underline="hover"
                color="inherit"
              >
                Release History
              </Link>
            </Typography>
            <Typography variant="body2" color="white" sx={footerTextSx}>
              <Link
                href="https://github.com/cancervariants/metakb"
                target="_blank"
                rel="noopener noreferrer"
                underline="hover"
                color="inherit"
              >
                Source Code
              </Link>
            </Typography>
          </Box>
          {/* Column 2: Info/help */}
          <Box display="flex" flexDirection="column" sx={{ flex: 1, minWidth: 0 }}>
            <Box pb={3}>
              <Typography variant="body1" color="white" sx={footerTextSx}>
                About
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/about/overview"
                  underline="hover"
                  color="inherit"
                >
                  Overview
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/about/team"
                  underline="hover"
                  color="inherit"
                >
                  Team
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/about/sources"
                  underline="hover"
                  color="inherit"
                >
                  Sources
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/about/publications"
                  underline="hover"
                  color="inherit"
                >
                  Publications
                </Link>
              </Typography>
            </Box>
            <Box>
              <Typography variant="body1" color="white" sx={footerTextSx}>
                Getting Involved
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/getting_involved/reporting_issues"
                  underline="hover"
                  color="inherit"
                >
                  Reporting Issues
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/getting_involved/contributing"
                  underline="hover"
                  color="inherit"
                >
                  Contributing
                </Link>
              </Typography>
            </Box>
          </Box>
          {/* Column 3: more info/tutorials */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box pb={3}>
              <Typography variant="body1" color="white" sx={footerTextSx}>
                Knowledge
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/knowledge/methods"
                  underline="hover"
                  color="inherit"
                >
                  Methods
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/knowledge/data_model"
                  underline="hover"
                  color="inherit"
                >
                  Data Model
                </Link>
              </Typography>
              <Typography variant="body2" color="white" sx={footerTextSx}>
                <Link
                  component={RouterLink}
                  to="/docs/knowledge/faq"
                  underline="hover"
                  color="inherit"
                >
                  FAQ
                </Link>
              </Typography>
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Box>
                <Typography variant="body1" color="white" sx={footerTextSx}>
                  Data & Policy
                </Typography>
                <Typography variant="body2" color="white" sx={footerTextSx}>
                  <Link
                    component={RouterLink}
                    to="/docs/data_policy/license"
                    underline="hover"
                    color="inherit"
                  >
                    License
                  </Link>
                </Typography>
                <Typography variant="body2" color="white" sx={footerTextSx}>
                  <Link
                    component={RouterLink}
                    to="/docs/data_policy/downloads"
                    underline="hover"
                    color="inherit"
                  >
                    Downloads
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Column 4: contact/links */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              gap: 0.75,
              flex: 1,
              minWidth: 0,
            }}
          >
            <Box pb={3}>
              <Typography variant="body1" color="white" sx={{ ...footerTextSx, flexShrink: 0 }}>
                <Link
                  href="https://github.com/cancervariants/metakb/issues/new/choose"
                  target="_blank"
                  rel="noopener noreferrer"
                  underline="hover"
                  color="inherit"
                >
                  Contact us
                </Link>
              </Typography>
            </Box>
          </Box>
        </Box>
      </ContentContainer>
    </Box>
  )
}

export default Footer
