import { Typography, Box } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function DataModelPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        MetaKB Data Model
      </Typography>


      <Typography component="p" sx={{ mb: 2 }}>
        The MetaKB Jr data model uses a knowledge graph approach designed to represent complex relationships between variant classification data. This schema supports the following data types:
      </Typography>

      <Box component="ul" sx={{ pl: 4, mt: 0 }}>
  <li>
    <Typography>
      Genes
    </Typography>
  </li>

  <li>
    <Typography>
      Variants
    </Typography>
  </li>

  <li>
    <Typography>
      Diseases
    </Typography>
  </li>
  <li>
    <Typography>
      Evidence statements
    </Typography>
  </li>
  <li>
    <Typography>
      Publications
    </Typography>
  </li>
 </Box>

<Typography component="p" sx={{ mb: 2 }}>
        Data objects in MetaKB are represented under the GA4GH Genomic Knowledge Standards, including use of the Variant Annotation Specification (VA-Spec) and Categorical Variant Representation Specification (CatVRS).
      </Typography>

      <Typography></Typography>
    </DocsLayout>
  )
}
