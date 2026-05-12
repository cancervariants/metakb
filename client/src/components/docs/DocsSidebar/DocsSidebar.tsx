import { Box, List, ListItemButton, ListItemText, Typography } from '@mui/material'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { docsSections } from '../../../routes/docsConfig'

export default function DocsSidebar() {
  const { pathname } = useLocation()

  const currentSection = docsSections.find((section) =>
    section.pages.some((page) => page.path === pathname),
  )

  if (!currentSection) return null

  return (
    <Box component="nav" sx={{ width: 220, flexShrink: 0 }}>
      <Typography variant="subtitle2" fontWeight="bold" mb={1}>
        {currentSection.label}
      </Typography>

      <List dense disablePadding>
        {currentSection.pages.map((page) => {
          const isActive = page.path === pathname

          return (
            <ListItemButton
              key={page.path}
              component={RouterLink}
              to={page.path}
              selected={isActive}
              sx={{
                borderRadius: 1,
                fontWeight: isActive ? 'bold' : 'normal',
              }}
            >
              <ListItemText primary={page.label} />
            </ListItemButton>
          )
        })}
      </List>
    </Box>
  )
}
