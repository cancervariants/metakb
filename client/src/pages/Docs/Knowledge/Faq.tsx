import { Typography, Box, Divider } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

// TODO: Make this an external component
function FAQItem({
  question,
  answer,
}: {
  question: string
  answer: string
}) {
  return (
    <Box sx={{ py: 2 }}>
      <Typography
        variant="h6"
        fontWeight="bold"
        sx={{ mb: 1 }}
      >
        {question}
      </Typography>

      <Typography
        component="p"
        color="text.secondary"
      >
        {answer}
      </Typography>

    </Box>
  )
}

export default function FAQPage() {
  return (
    <DocsLayout>
      <Typography
        variant="h4"
        mb={1}
        fontWeight="bold"
      >
        Frequently Asked Questions
      </Typography>

      <FAQItem
        question="What is MetaKB Jr?"
        answer="MetaKB Jr is a harmonized cancer variant interpretation knowledgebase that integrates information from multiple oncology resources into a unified structure."
      />

      <FAQItem
        question="Who is MetaKB Jr for?"
        answer="Researchers, developers, clinicians, students, and anyone interested in precision oncology or variant classification."
      />

      <FAQItem
        question="Is the data open?"
        answer="MetaKB Jr prioritizes open and transparent data access whenever licensing permits. "
      />

      <FAQItem
        question="How often is the data updated?"
        answer="Data updates depend on source availability and release schedules. Regular refreshes are planned to maintain current content."
      />

      <FAQItem
        question="Can I use MetaKB Jr programmatically?"
        answer="Yes. MetaKB Jr is designed to support APIs, bulk downloads, and computational workflows."
      />

      <FAQItem
        question="How can I contribute?"
        answer="See the Contributing page for details on reporting issues, improving documentation, or contributing code and data integrations."
      />
    </DocsLayout>
  )
}