import { Typography, Box } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function MethodsPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        MetaKB Data Transformation Methods
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>
        MetaKB Jr uses a modular data ingestion and transformation pipeline to normalize heterogeneous variant classification datasets into a unified schema. Our data model emphasizes reproducibility and transparent transformation workflows.
      </Typography>

    <Typography component="p" sx={{ mb: 2}}>
      Core processing steps include:
    </Typography>

    <Box component="ul" sx={{ pl: 4, mt: 0 }}>
  <li>
    <Typography>
      Data ingest from public sources
    </Typography>
  </li>

  <li>
    <Typography>
      Parsing and normalization of records
    </Typography>
  </li>

  <li>
    <Typography>
      Mapping entities to standardized identifiers and ontologies
    </Typography>
  </li>
  <li>
    <Typography>
      Aggregation and display of searchable evidence, therapies, diseases, and classifications
    </Typography>
  </li>

</Box>


    </DocsLayout>
  )
}
