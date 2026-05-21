import { Typography, Box, Link, Stack, Divider } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function SourcesPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Current Sources
      </Typography>

      <Stack spacing={3} sx={{ mt: 3 }}>
        <Box>
          <Typography
            component={Link}
            href="https://civicdb.org/"
            target="_blank"
            rel="noopener"
            variant="h6"
            sx={{ textDecoration: 'none' }}
          >
            CIViC
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Clinical Interpretation of Variants in Cancer knowledgebase.
          </Typography>

          <Typography variant="body2" sx={{ mt: 1 }}>
            Griffith M, Spies NC, Krysiak K, et al. CIViC is a community knowledgebase for expert
            crowdsourcing the clinical interpretation of variants in cancer.
            <i> Nature Genetics.</i> 2017;49(2):170–174.
          </Typography>
        </Box>

        <Divider />

        <Box>
          <Typography
            component={Link}
            href="https://moalmanac.org/"
            target="_blank"
            rel="noopener"
            variant="h6"
            sx={{ textDecoration: 'none' }}
          >
            MOAlmanac
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Molecular Oncology Almanac interpretation resource.
          </Typography>

          <Typography variant="body2" sx={{ mt: 1 }}>
            Reardon B, Moore ND, Moore NS, et al. Integrating molecular profiles into clinical
            frameworks through the Molecular Oncology Almanac.
            <i> Nature Cancer.</i> 2021.
          </Typography>
        </Box>

        <Divider />

        <Box>
          <Typography
            component={Link}
            href="https://www.fda.gov/media/191379/download?attachment"
            target="_blank"
            rel="noopener"
            variant="h6"
            sx={{ textDecoration: 'none' }}
          >
            FDA Pediatric Oncology Approvals
          </Typography>

          <Typography variant="body2" color="text.secondary">
            FDA drug approval and pediatric oncology indication data.
          </Typography>

          <Typography variant="body2" sx={{ mt: 1 }}>
            U.S. Food and Drug Administration. FDA-approved oncology therapies and pediatric
            indication resources.
          </Typography>
        </Box>
      </Stack>
    </DocsLayout>
  )
}
