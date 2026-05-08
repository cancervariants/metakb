import { Box } from '@mui/material'
import ContentContainer from '../../common/ContentContainer'
import DocsSidebar from '../DocsSidebar/DocsSidebar'

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <Box component="main" sx={{ py: 5 }}>
      <ContentContainer>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 4,
            p: 4,
            bgcolor: 'white',
            borderRadius: 1,
          }}
        >
          <DocsSidebar />

          <Box component="article" sx={{ flex: 1, minWidth: 0 }}>
            {children}
          </Box>
        </Box>
      </ContentContainer>
    </Box>
  )
}
