import { Typography, Box } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function ContributingPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Contributing to MetaKB
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>
       MetaKB Jr is an open source project and contributions are encouraged.
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>
       Ways to contribute include:
      </Typography>

<Box component="ul" sx={{ pl: 4, mt: 0 }}>
  <li>
    <Typography>
      Reporting bugs
    </Typography>
  </li>

  <li>
    <Typography>
      Suggesting new features
    </Typography>
  </li>

  <li>
    <Typography>
      Suggesting new data sources
    </Typography>
  </li>
  <li>
    <Typography>
      Contributing code
    </Typography>
  </li>
  <li>
    <Typography>
      Participating in discussions on GitHub
    </Typography>
  </li>

</Box>
    </DocsLayout>
  )
}
