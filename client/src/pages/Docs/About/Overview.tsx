import { Typography, Box } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function OverviewPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Overview
      </Typography>

<Typography component="p" sx={{ mb: 2 }}>
  MetaKB Jr. is an open, community-driven knowledgebase designed to make
  clinically relevant somatic variant interpretation data easier to explore,
  integrate, and reuse. MetaKB aggregates and harmonizes data from multiple
  precision oncology knowledgebases into a singular, consistent data model
  with a focus on pediatric data.
</Typography>

<Typography component="p" sx={{ mb: 2 }}>
  MetaKB Jr. is intended for researchers, bioinformaticians, educators,
  variant classification experts, and the broader precision oncology
  community.
</Typography>

<Typography component="p" sx={{ mb: 1 }}>
  The goal of MetaKB Jr. is to lower the barrier to working with variant
  classification data by providing:
</Typography>

<Box component="ul" sx={{ pl: 4, mt: 0 }}>
  <li>
    <Typography>
      Harmonized terminology and structured relationships
    </Typography>
  </li>

  <li>
    <Typography>
      Aggregated classification knowledge
    </Typography>
  </li>

  <li>
    <Typography>
      Transparent provenance and attribution
    </Typography>
  </li>
</Box>
    </DocsLayout>
  )
}
