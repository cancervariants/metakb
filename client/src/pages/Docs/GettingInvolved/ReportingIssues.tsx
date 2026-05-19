import { Typography, Box, Link } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'
import GitHubIcon from '@mui/icons-material/GitHub'

export default function ReportingIssuesPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Reporting Issues
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>We welcome bug reports, data quality issues, and feature requests from the community. When reporting an issue, please include: </Typography>
      <Box component="ul" sx={{ pl: 4, mt: 0 }}>
  <li>
    <Typography>
      A clear description of the problem
    </Typography>
  </li>

  <li>
    <Typography>
      Steps to reproduce the issue
    </Typography>
  </li>

  <li>
    <Typography>
      Relevant screenshots or error messages
    </Typography>
  </li>
</Box>

<Box
  component={Link}
  href="https://github.com/cancervariants/metakb/issues/new/choose"
  target="_blank"
  rel="noopener"
  sx={{
    display: 'inline-flex',
    alignItems: 'center',
    gap: 1,
    px: 2,
    py: 1,
    borderRadius: 2,
    textDecoration: 'none',
    bgcolor: 'grey.100',
    border: '1px solid',
    borderColor: 'grey.300',
    transition: '0.2s',
    '&:hover': {
      bgcolor: 'grey.200',
    },
  }}
>
  <GitHubIcon fontSize="small" />

  <Typography>
   Submit a New Issue
  </Typography>
</Box>


    </DocsLayout>
  )
}
